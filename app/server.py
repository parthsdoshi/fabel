import os
import collections
import time
import pickle
import platform
import subprocess
import shelve
import logging
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

        files = []
        for k, v in id_to_file.items():
            files.append(v)

        return {'payload': files, 'error': 0, 'error_str': 'Success'}

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
    return True


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
    logging.debug(content)
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

    enc = getEncoding(filepath)

    topk = 5
    index_to_name = None
    docs_vec = None
    with shelve.open(DB_FILE) as db:
        index_to_name = db['index_to_name']
        docs_vec = db['docs_vec']

    if index_to_name is None:
        logging.error("Index to Name vector not properly initialized.")
    if docs_vec is None:
        logging.error("Docs Vector not properly initialized.")

    score = np.sum(enc * docs_vec, axis=1) / np.linalg.norm(docs_vec, axis=1)
    topk_idx = np.argsort(score)[::-1][:topk]

    names = []
    sorted_score = np.sort(score)[::-1]
    for i, idx in enumerate(topk_idx[:5]):
        name = index_to_name[idx]
        logging.info(f'Score: {sorted_score[i]}\t\tPred: {name}')
        names.append(name)

    unique_id = -1
    with shelve.open(DB_FILE) as db:
        unique_id = db['unique_id']
        db['unique_id'] += 1

    file_dict = {
            'id': unique_id,
            'name': os.path.basename(filepath),
            'path': filepath,
            'tags': names,
            'timestamp': str(datetime.utcnow())
            }

    with shelve.open(DB_FILE) as db:
        db['id_to_file'][unique_id] = file_dict

    socketio.emit('newFile', file_dict)

    return jsonify({"error": False})


@socketio.on('addTag')
def add_tag(unique_id, tag_name):
    filepath = None
    with shelve.open(DB_FILE) as db:
        # Check name doesn't exist
        if tag_name in db['tags'].keys():
            return {"error": -1, "error_str": "Tag already exists!"}
        file_dict = db['id_to_file'][unique_id]
        filepath = file_dict['path']

    if filepath == None:
        return {"error": -1, "error_str": "Could not retrieve file."}
    
    enc = getEncoding(filepath)

    new_tag = { "enc": enc, "num_docs": 1 }
    with shelve.open(DB_FILE) as db:
        db['tags'][tag_name] = new_tag

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

def main():
    with shelve.open(DB_FILE) as db:
        db['unique_id'] = 0
        db['id_to_file'] = collections.OrderedDict()
        db['tags'] = {}

    tags_encodes = {}
    with open(PICKLED_FILE, 'rb') as handle:
        tags_encodes = pickle.load(handle)

    name_to_label = collections.OrderedDict()
    for i, name in enumerate(newsgroups_train.target_names):
        name_to_label[name] = i

    tags_encodes = collections.OrderedDict(tags_encodes)

    with shelve.open(DB_FILE) as db:
        db['index_to_name'] = {}

        all_docs = []
        for i, (k, v) in enumerate(tags_encodes.items()):
            all_docs.append(v)
            index_to_name[i] = k

        db['docs_vec'] = np.array(all_docs)
    # app.run(port=4994, debug=False, threaded=True)
    socketio.run(app, port=4994, debug=False)

if __name__ == '__main__':
    main()
