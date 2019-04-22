from os import path
import time
import pickle

import requests
from flask import Flask, request, jsonify
from sklearn.datasets import fetch_20newsgroups

from tika import parser

BERT_SERVER = 'http://127.0.0.1:6666'

app = Flask(__name__)

@app.route('/', methods=['POST'])
def receiveDownloadData():
    content = request.json

    if content['state'] != 'complete':
        return jsonify({"error": True})
    
    filepath = path.normcase(path.normpath(content['filename']))
    if not path.exists(filepath):
        return jsonify({"error": True})

    mimetype = content['mime']

    content = None
    if 'pdf' in mimetype:
        raw = parser.from_file(filepath)
        content = raw['content']
    elif 'text/html' in mimetype:
        with open(filepath, 'r') as f:
            content = f.read()

    if content:
        r = requests.post(BERT_SERVER, json={"doc": content})
        print(r.json()['features'])

    return jsonify({"error": False})

if __name__ == '__main__':
    newsgroups_train = fetch_20newsgroups(subset='train',
                                          remove=('headers', 'footers', 'quotes'))
    newsgroups_test = fetch_20newsgroups(subset='test',
                                         remove=('headers', 'footers', 'quotes'))

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

    tags_encodes = {}
    for key in tags_data:
        val = tags_data[key]
        r = requests.post(BERT_SERVER, json={"doc": val})
        tags_encodes[key] = r.json()['features']
        print(r.json()['features'])

    with open('20newsgroups_train_encoded', 'wb') as handle:
        pickle.dump(tags_encodes, handle)

    exit()

    app.run(port=4994, debug=True)
