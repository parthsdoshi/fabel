from os import path
import collections
import time
import pickle

import numpy as np

import requests

from flask import Flask, request, jsonify

from sklearn.datasets import fetch_20newsgroups
from sklearn import metrics

from tika import parser

BERT_SERVER = 'http://10.0.0.11:6666'
PICKLED_FILE = '20newsgroups_train_encoded'
SAMPLE_SIZE = 10

index_to_name = None
docs_vec = None

app = Flask(__name__)

def tikaParse(filepath):
    raw = parser.from_file(filepath)
    content = raw['content']
    return content

def readFile(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    return content

@app.route('/', methods=['POST'])
def receiveDownloadData():
    content = request.json

    if content['state'] != 'complete':
        return jsonify({"error": True})
    
    filepath = path.normcase(path.normpath(content['filename']))
    if not path.exists(filepath):
        return jsonify({"error": True})

    mimetype = content['mime']
    print(mimetype)

    content = None
    if 'pdf' in mimetype:
        content = tikaParse(filepath)
    elif 'officedocument' in mimetype:
        content = tikaParse(filepath)
    elif 'text/html' in mimetype:
        content = readFile(filepath)
    elif 'text/plain' in mimetype:
        content = readFile(filepath)

    print(content)

    if content:
        topk = 5
        r = requests.post(BERT_SERVER, json={"doc": content, "sample_size": SAMPLE_SIZE})
        enc = r.json()['features']

        global index_to_name
        global docs_vec

        score = np.sum(enc * docs_vec, axis=1) / np.linalg.norm(docs_vec, axis=1)
        topk_idx = np.argsort(score)[::-1][:topk]

        names = []
        sorted_score = np.sort(score)[::-1]
        for i, idx in enumerate(topk_idx[:5]):
            name = index_to_name[idx]
            print(f'Score: {sorted_score[i]}\t\tPred: {name}')

    return jsonify({"error": False})

if __name__ == '__main__':
    newsgroups_train = fetch_20newsgroups(subset='train',
                                          remove=('headers', 'footers', 'quotes'))
    newsgroups_test = fetch_20newsgroups(subset='test',
                                         remove=('headers', 'footers', 'quotes'))

    tags_encodes = {}
    if not path.exists(PICKLED_FILE):

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
            r = requests.post(BERT_SERVER, json={"doc": val})
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

    index_to_name = {}

    all_docs = []
    for i, (k, v) in enumerate(tags_encodes.items()):
        all_docs.append(v)
        index_to_name[i] = k

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

    app.run(port=4994, debug=True)
