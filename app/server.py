import os
import collections
import time
import pickle
import platform
import subprocess
import shelve
import logging
import sys
from datetime import datetime

import numpy as np

import requests

from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO

from sklearn.datasets import fetch_20newsgroups
from sklearn import metrics

# to grab text from things like pdf, ppt, docx, etc
# actually there may be a function to pass a file into tika and
# it tells us whether or not it can parse it...
from tika import parser

# to talk with frontend
import webview

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

BERT_SERVER = 'http://199.168.72.148:6666'
PICKLED_FILE = '20newsgroups_train_encoded'
SAMPLE_SIZE = 10

FRONTEND_BUILD_FOLDER = os.path.normpath('frontend/build')

DB_FILE = 'db'

app = Flask(__name__, static_folder=FRONTEND_BUILD_FOLDER)
socketio = SocketIO(app)


@socketio.on('getAllFiles')
def get_all_files():
    with shelve.open(DB_FILE) as db:
        id_to_file = db['id_to_file']
        return {'payload': id_to_file, 'error': 0, 'error_str': 'Success'}

    return {'error': -1, 'error_str': 'Could not open DB'}


@socketio.on('openFile')
def open_file(filepath):
    filepath = os.path.normpath(filepath)
    filedir = os.path.dirname(filepath)
    if platform.system() == "Windows":
        subprocess.Popen(["explorer", "/select,", filepath])
    elif platform.system() == "Darwin":
        subprocess.Popen(["open", filedir])
    else:
        subprocess.Popen(["xdg-open", filedir])
    return {'payload': True, 'error': 0, 'error_str': 'Successfully opened file."}


def tikaParse(filepath):
    raw = parser.from_file(filepath)
    return raw


def readFile(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    return content

def getEncoding(filepath):
    raw = tikaParse(filepath)
    if raw['status'] != 200 or not raw['content']:
        return jsonify({"error": "Unsupported content."})

    content = raw['content']
    r = requests.post(BERT_SERVER, json={
                      "doc": content, "sample_size": SAMPLE_SIZE})
    enc = r.json()['features']

    return enc


@app.route('/rcv', methods=['POST'])
def receive_download_data():
    content = request.json

    if content['state'] != 'complete':
        return jsonify({"error": True})

    filepath = os.path.normpath(content['filename'])
    if not os.path.exists(filepath):
        return jsonify({"error": True})

    mimetype = content['mime']
    logging.debug(mimetype)

    unique_id = -1
    with shelve.open(DB_FILE) as db:
        unique_id = db['unique_id']
        db['unique_id'] += 1

    # Populate tags after
    file_dict = {
            'id': unique_id,
            'name': os.path.basename(filepath),
            'path': filepath,
            'tags': [],
            'timestamp': str(datetime.utcnow())
            }

    with shelve.open(DB_FILE) as db:
        o_dict = db['id_to_file']
        o_dict[unique_id] = file_dict
        db['id_to_file'] = o_dict
        logging.info(filepath +' file saved')
        
    # Load file
    socketio.emit('newFile', file_dict)
    enc = getEncoding(filepath)

    topk = 5
    docs_names = []
    docs_vec = []
    with shelve.open(DB_FILE) as db:
        tags = db['tags']
        #TODO tags is empty
        if len(tags) == 0:
            logging.warning('There are no tags defined.')
            return jsonify({"error": True}) 
        #TODO change to constant
        # random key to get shape
        #embed_len = next(iter(tags))['enc'].shape[1]
        for key, val in tags.items():
            docs_names.append(key)
            docs_vec.append(val["enc"])

        docs_vec = np.array(docs_vec)

    if len(docs_vec) == 0:
        logging.error("Docs Vector not properly initialized.")
        return jsonify({"error": True}) 

    score = np.sum(enc * docs_vec, axis=1) / np.linalg.norm(docs_vec, axis=1)
    topk_idx = np.argsort(score)[::-1][:topk]

    names = []
    for idx in topk_idx:
        name = docs_names[idx]
        logging.info(f'Score: {score[idx]}\t\tPred: {name}')
        names.append(name)

    #TODO fix this shit
    # Update names in the db
    file_dict['tags'] = names 
    with shelve.open(DB_FILE) as db:
        db['id_to_file'][unique_id] = file_dict

    socketio.emit('newFile', file_dict)

    return jsonify({"error": False})


@socketio.on('addTag')
def add_tag(unique_id, tag_name):
    logging.debug(f'unique_id: {unique_id} \t tag_name: {tag_name}')
    filepath = None
    file_dict = None
    with shelve.open(DB_FILE) as db:
        # Check name doesn't exist
        if tag_name in db['tags'].keys():
            return {"error": -1, "error_str": "Tag already exists!"}
        file_dict = db['id_to_file'][unique_id]
        filepath = file_dict['path']

    # err if file_dict None
    if filepath is None:
        return {"error": -1, "error_str": "Could not retrieve file."}
    
    enc = getEncoding(filepath)

    #TODO change to encoding
    new_tag = { "enc": enc, "num_docs": 1 }
    with shelve.open(DB_FILE) as db:
        tags = db['tags']
        tags[tag_name] = new_tag
        db['tags'] = tags
        logging.info('New tag: ' + tag_name)
        id_to_file = db['id_to_file']
        file_dict = id_to_file[unique_id]
        file_dict['tags'].append(tag_name)
        db['id_to_file'] = id_to_file

    socketio.emit('newFile', file_dict) 
    return {"error": 0, "error_str": "Success adding tag."}

@socketio.on('updateTag')
def update_tag(unique_id, tag_name):
    filepath = None
    with shelve.open(DB_FILE) as db:
        file_dict = db['id_to_file'][unique_id]
        filepath = file_dict['path']

    if filepath == None:
        return {"error": -1, "error_str": "Could not retrieve file."}
    
    enc = getEncoding(filepath)

    with shelve.open(DB_FILE) as db:
        oldEnc, num_docs = db['tags'][tag_name]
        # Mean with previous encoding
        newEnc = (num_docs/(num_docs+1)) * oldEnc + (1/(num_docs+1)) * enc
        db['tags'][tag_name]= {"name": newEnc, "num_docs": num_docs+1}

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path == "":
        return send_from_directory(FRONTEND_BUILD_FOLDER, 'index.html')
    elif os.path.exists(os.path.join(FRONTEND_BUILD_FOLDER, path)):
        return send_from_directory(FRONTEND_BUILD_FOLDER, path)
    else:
        return send_from_directory(FRONTEND_BUILD_FOLDER, 'index.html')

def main(debug=False):
    # seed
    with shelve.open(DB_FILE) as db:
        if 'unique_id' not in db:
            db['unique_id'] = 0
            db['id_to_file'] = collections.OrderedDict()
            db['tags'] = {}
    # tags_encodes = {}
    # with open(PICKLED_FILE, 'rb') as handle:
    #     tags_encodes = pickle.load(handle)

    # name_to_label = collections.OrderedDict()
    # for i, name in enumerate(newsgroups_train.target_names):
    #     name_to_label[name] = i

    # tags_encodes = collections.OrderedDict(tags_encodes)

    # with shelve.open(DB_FILE) as db:
    #     db['index_to_name'] = {}

    #     all_docs = []
    #     for i, (k, v) in enumerate(tags_encodes.items()):
    #         all_docs.append(v)
    #         index_to_name[i] = k

    #     db['docs_vec'] = np.array(all_docs)

    # app.run(port=4994, debug=False, threaded=True)
    socketio.run(app, port=4994, debug=debug)

if __name__ == '__main__':
    main(debug=True)
