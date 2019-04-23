import os
import collections
import time
import pickle
import platform
import subprocess

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
unique_id = 0

index_to_name = None
docs_vec = None

FRONTEND_BUILD_FOLDER = os.path.normpath('frontend/build')

app = Flask(__name__, static_folder=FRONTEND_BUILD_FOLDER)
socketio = SocketIO(app)

@socketio.on('openFile')
def openFile(filepath):
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

@app.route('/rcv', methods=['POST'])
def receiveDownloadData():
    content = request.json

    if content['state'] != 'complete':
        return jsonify({"error": True})
    
    filepath = os.path.normpath(content['filename'])
    if not os.path.exists(filepath):
        return jsonify({"error": True})

    mimetype = content['mime']
    print(mimetype)

    raw = tikaParse(filepath)
    if raw['status'] != 200:
        return jsonify({"error": "Unsupported content."})

    content = raw['content']
    print(content)

    # if 'pdf' in mimetype:
    #     content = tikaParse(filepath)
    # elif 'officedocument' in mimetype:
    #     content = tikaParse(filepath)
    # elif 'text/html' in mimetype:
    #     content = readFile(filepath)
    # elif 'text/plain' in mimetype:
    #     content = readFile(filepath)

    if content:
        topk = 5
        r = requests.post(BERT_SERVER, json={"doc": content, "sample_size": SAMPLE_SIZE})
        enc = r.json()['features']

        global index_to_name
        global docs_vec

        if index_to_name is None:
            print("Index to Name vector not properly initialized.")
        if docs_vec is None:
            print("Docs Vector not properly initialized.")

        score = np.sum(enc * docs_vec, axis=1) / np.linalg.norm(docs_vec, axis=1)
        topk_idx = np.argsort(score)[::-1][:topk]

        names = []
        sorted_score = np.sort(score)[::-1]
        for i, idx in enumerate(topk_idx[:5]):
            name = index_to_name[idx]
            print(f'Score: {sorted_score[i]}\t\tPred: {name}')
            names.append(name)

    global unique_id
    file_dict = {
            'id': unique_id,
            'name': os.path.basename(filepath),
            'path': filepath,
            'tags': names
            }
    unique_id += 1

    socketio.emit('newFile', file_dict)

    return jsonify({"error": False})

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
    newsgroups_train = fetch_20newsgroups(subset='train',
                                          remove=('headers', 'footers', 'quotes'))
    newsgroups_test = fetch_20newsgroups(subset='test',
                                         remove=('headers', 'footers', 'quotes'))

    tags_encodes = {}
    if not os.path.exists(PICKLED_FILE):

        NUM_TAGS = len(newsgroups_train.target_names)

        # group tags
        tags_data = {}
        for name in newsgroups_train.target_names:
            tags_data[name] = []
        for i, doc in enumerate(newsgroups_train.data):
            label = newsgroups_train.target[i]
            name = newsgroups_train.target_names[label]
            tags_data[name].append(doc)

        # Combine docs
        for key in tags_data:
            val = tags_data[key]
            tags_data[key] = '. '.join(val)

        for key in tags_data:
            val = tags_data[key]
            r = requests.post(BERT_SERVER, json={"doc": val, "sample_size": SAMPLE_SIZE})
            tags_encodes[key] = r.json()['features']
            print(r.json()['features'])

        with open(PICKLED_FILE, 'wb') as handle:
            pickle.dump(tags_encodes, handle)
    else:
        with open(PICKLED_FILE, 'rb') as handle:
            tags_encodes = pickle.load(handle)

    name_to_label = collections.OrderedDict()
    for i, name in enumerate(newsgroups_train.target_names):
        name_to_label[name] = i

    # num_tags_encodes = {}
    # for k, v in tags_encodes.items():
    #     label = name_to_label[k]
    #     num_tags_encodes[label] = v

    tags_encodes = collections.OrderedDict(tags_encodes)

    global index_to_name
    index_to_name = {}

    all_docs = []
    for i, (k, v) in enumerate(tags_encodes.items()):
        all_docs.append(v)
        index_to_name[i] = k

    global docs_vec
    docs_vec = np.array(all_docs)

    # topk = 10
    # predictions = []
    # scores = []
    # for i, doc in enumerate(newsgroups_test.data):
    #     label = newsgroups_test.target[i]
    #     name = newsgroups_test.target_names[label]
    #     r = requests.post(BERT_SERVER, json={"doc": doc, "sample_size": SAMPLE_SIZE})
    #     enc = np.array(r.json()['features'])

    #     # is NaN
    #     if np.isnan(enc).any():
    #         scores.append(np.zeros((len(newsgroups_test.target_names), 1)))
    #         predictions.append([0] * topk)
    #         print('Found NaN')
    #         continue

    #     score = np.sum(enc * docs_vec, axis=1) / np.linalg.norm(docs_vec, axis=1)
    #     scores.append(score)

    #     topk_idx = np.argsort(score)[::-1][:topk]
    #     predictions.append(topk_idx)

    #     if i % 1 == 0:
    #         print(f'{i}/{len(newsgroups_test.data)}')
    #         print(f'Correct: {name}')

    #         names = []
    #         sorted_score = np.sort(score)[::-1]
    #         for i, idx in enumerate(topk_idx[:5]):
    #             name = index_to_name[idx]
    #             print(f'Score: {sorted_score[i]}\t\tPred: {name}')

    #         print(f'Document: {doc[:100]}\n')

    # f1_score = metrics.f1_score(newsgroups_test.target, pred, average='macro')
    # print(f1_score)

    # with open("predictions", 'wb') as handle:
    #     pickle.dump(predictions, handle)

    # with open("scores", 'wb') as handle:
    #     pickle.dump(scores, handle)


    # app.run(port=4994, debug=False, threaded=True)
    socketio.run(app, port=4994, debug=False)

if __name__ == '__main__':
    main()
