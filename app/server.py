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

import tkinter as tk
from tkinter import filedialog

# to grab text from things like pdf, ppt, docx, etc
# actually there may be a function to pass a file into tika and
# it tells us whether or not it can parse it...
from tika import parser
from mimetypes import MimeTypes

import html2text

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

BERT_SERVER = 'http://owl.maxl.in:6666'
# BERT_SERVER = 'http://localhost:6666'
PICKLED_FILE = '20newsgroups_train_encoded'
SAMPLE_SIZE = 10

FRONTEND_BUILD_FOLDER = os.path.normpath('frontend/build')

DB_FILE = 'db'

app = Flask(__name__, static_folder=FRONTEND_BUILD_FOLDER)
socketio = SocketIO(app)


@socketio.on('openFileDialog')
def open_file_dialog():
    # files = webview.create_file_dialog(dialog_type=webview.OPEN_DIALOG, directory='', allow_multiple=True)
    files = filedialog.askopenfilenames()

    if files is None:
        # TODO: error handle
        pass

    for f in files:
        receive_download_data(online=False, local_filepath=f)

@socketio.on('getAllFiles')
def get_all_files():
    with shelve.open(DB_FILE) as db:
        id_to_file = db['id_to_file']
        return {'payload': id_to_file, 'error': 0, 'error_str': 'Success'}

    return {'error': -1, 'error_str': 'Could not open DB.'}

@socketio.on('getFile')
def get_file(uid):
    with shelve.open(DB_FILE) as db:
        id_to_file = db['id_to_file']
        return {'payload': id_to_file[uid], 'error': 0, 'error_str': 'Success'}

    return {'error': -1, 'error_str': 'Could not open DB.'}

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
    return {'payload': True, 'error': 0, 'error_str': 'Successfully opened file.'}

def tikaParse(filepath):
    try:
        raw = parser.from_file(filepath)
    except UnicodeEncodeError as _:
        #TODO this is sus af
        raw = {
            "status": 200,
            "content": readFile(filepath)
        }
        return raw

    return raw

def readFile(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    return content

def getEncoding(filepath):
    m = MimeTypes()
    mime = m.guess_type(filepath)[0]
    raw = None
    if 'html' in mime:
        text = html2text.html2text(readFile(filepath))
        with open('test.txt', 'w') as f:
            f.write(text)
        raw = {
                'status': 200,
                'content': text
            }
    else:
        raw = tikaParse(filepath)
        if raw['status'] != 200 or not raw['content']:
            return jsonify({"error": "Unsupported content."})

    content = raw['content']
    r = requests.post(BERT_SERVER, json={
                      "doc": content, "sample_size": SAMPLE_SIZE})
    enc = r.json()['features']
    logging.info("Encoding: "+str(enc[:20]))
    return enc

@app.route('/rcv', methods=['POST'])
def receive_download_data(online=True, local_filepath=None):
    if online:
        content = request.json

        if content['state'] != 'complete':
            return jsonify({"error": True})

        filepath = os.path.normpath(content['filename'])
        if not os.path.exists(filepath):
            return jsonify({"error": True})

        mimetype = content['mime']
        logging.debug(mimetype)
    else:
        filepath = local_filepath

    unique_id = -1
    with shelve.open(DB_FILE) as db:
        unique_id = db['unique_id']
        db['unique_id'] += 1

    # Populate tags after
    file_dict = {
            'id': unique_id,
            'name': os.path.basename(filepath),
            'path': filepath,
            'tags': {},
            'timestamp': str(datetime.utcnow())
            }

    socketio.emit('newFile', file_dict)

    with shelve.open(DB_FILE) as db:
        o_dict = db['id_to_file']
        o_dict[unique_id] = file_dict
        db['id_to_file'] = o_dict
        logging.info(filepath +' file saved')
        
    # Load file
    enc = getEncoding(filepath)

    topk = 2 
    docs_names = []
    docs_vec = []
    with shelve.open(DB_FILE) as db:
        tags = db['tags']
        #TODO tags is empty
        if len(tags) == 0:
            logging.warning('There are no tags defined.')
            socketio.emit('updateFile', file_dict)
            if online:
                return jsonify({"error": False}) 
        #TODO change to constant
        # random key to get shape
        #embed_len = next(iter(tags))['enc'].shape[1]
        for key, val in tags.items():
            docs_names.append(key)
            docs_vec.append(val["enc"])

        docs_vec = np.array(docs_vec)

    if len(docs_vec) == 0:
        logging.error("Docs Vector not properly initialized.")
        socketio.emit('removeFile', unique_id)
        if online:
            return jsonify({"error": True}) 

    score = np.sum(enc * docs_vec, axis=1) / np.linalg.norm(docs_vec, axis=1)
    topk_idx = np.argsort(score)[::-1][:topk]

    names = {}
    for idx in topk_idx:
        name = docs_names[idx]
        logging.info(f'Score: {score[idx]}\t\tPred: {name}')
        names[name] = name
        update_tag_encoding(name, enc)

    # Update names in the db
    file_dict['tags'] = names 
    with shelve.open(DB_FILE) as db:
        id_to_file = db['id_to_file']
        id_to_file[unique_id] = file_dict
        db['id_to_file'] = id_to_file 

    socketio.emit('updateFile', file_dict)

    if online:
        return jsonify({"error": False})

@socketio.on('addTag')
def add_tag(unique_id, tag_name):
    logging.debug(f'unique_id: {unique_id} \t tag_name: {tag_name}')
    filepath = None
    file_dict = None
    isNewTag = True
    with shelve.open(DB_FILE) as db:
        file_dict = db['id_to_file'][unique_id]
        filepath = file_dict['path']
        # Check tag not already added
        if tag_name in file_dict['tags']:
            return {"error": -1, "error_str": "Tag already added!"}
        # Check tag doesn't exist in encoding list
        if tag_name in db['tags'].keys():
            # oldEnc, num_docs = db['tags'][tag_name].values()
            isNewTag = False

    # err if file_dict None
    if filepath is None or file_dict is None:
        return {"error": -1, "error_str": "Could not retrieve file.", "payload": file_dict}
    
    enc = getEncoding(filepath)
    if isNewTag:
        #TODO change to encoding
        new_tag = { "enc": enc, "num_docs": 1 }
        with shelve.open(DB_FILE) as db:
            tags = db['tags']
            tags[tag_name] = new_tag
            db['tags'] = tags
            logging.info('New tag: ' + tag_name)
    else:
        # Mean with previous encoding
        update_tag_encoding(tag_name, enc)
        

    # Add tag
    with shelve.open(DB_FILE) as db:
        id_to_file = db['id_to_file']
        file_dict = id_to_file[unique_id]
        file_dict['tags'][tag_name] = tag_name
        db['id_to_file'] = id_to_file

    return {"error": 0, "error_str": "Success adding tag.", "payload": file_dict}

@socketio.on('removeTag')
def remove_tag(unique_id, tag_name):
    logging.debug(f'unique_id: {unique_id} \t tag_name: {tag_name}')
    filepath = None
    file_dict = None
    with shelve.open(DB_FILE) as db:
        file_dict = db['id_to_file'][unique_id]
        filepath = file_dict['path']
        # Check tag not already added
        if tag_name not in file_dict['tags']:
            return {"error": -1, "error_str":  "Tag: <" + tag_name + "> wasn't in list.", "payload": file_dict}
        # Check tag exists in the encoding list
        if tag_name in db['tags'].keys():
            oldEnc, num_docs = db['tags'][tag_name].values()
        else:
           return {"error": -1, "error_str":  "Tag: <" + tag_name + "> doesn't exist!", "payload": file_dict}

    # err if file_dict None
    if filepath is None or file_dict is None:
        return {"error": -1, "error_str": "Could not retrieve file.", "payload": file_dict}
    
    # Remove all tags if last one
    if num_docs == 1:
        with shelve.open(DB_FILE) as db:
            tags = db['tags']
            logging.info('Deleted doc from tag: ' + tag_name)
            tags.pop(tag_name)
            db['tags'] = tags
    else:
        doc_enc = getEncoding(filepath)
        # Undo Mean with previous encoding
        # TODO this math is suspicious
        prev_enc = (oldEnc - (1 / num_docs) * np.array(doc_enc)) * (num_docs/(num_docs-1))
        with shelve.open(DB_FILE) as db:
            tags = db['tags']
            logging.info('Deleted doc from tag: ' + tag_name)
            tags[tag_name] = {"enc": prev_enc, "num_docs": num_docs-1}
            db['tags'] = tags

    # remove tag
    with shelve.open(DB_FILE) as db:
        id_to_file = db['id_to_file']
        file_dict = id_to_file[unique_id]
        file_dict['tags'].pop(tag_name, None)
        db['id_to_file'] = id_to_file

    socketio.emit('newFile', file_dict) 
    return {"error": 0, "error_str": "Success removing tag.", "payload": file_dict}

# returns True on success
def update_tag_encoding(tag_name, enc):
    with shelve.open(DB_FILE) as db:
        if tag_name in db['tags'].keys():
            oldEnc, num_docs = db['tags'][tag_name].values()
        else:
            return False

    newEnc = (num_docs/(num_docs+1)) * np.array(oldEnc) + (1/(num_docs+1)) * np.array(enc)
    with shelve.open(DB_FILE) as db:
        tags = db['tags']
        logging.info('Updated tag: ' + tag_name)
        tags[tag_name] = {"enc": newEnc, "num_docs": num_docs+1}
        db['tags'] = tags

    return True

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
    root = tk.Tk()
    root.withdraw()

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
