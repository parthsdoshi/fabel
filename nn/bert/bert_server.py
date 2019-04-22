from os import path
import random
import collections
import re

import numpy as np

from flask import Flask, request, jsonify

import tensorflow as tf

# pip install bert-tensorflow
import bert
from bert import modeling
from bert import tokenization

import nltk
from nltk.tokenize import sent_tokenize
# uncomment this to initialize nltk on first install
# nltk.download(punkt)

uncased = True
BERT_MODEL_DIR = path.normpath("pretrained/uncased_L-12_H-768_A-12")
layer_indices = [-2]
TPU = False
TPU_ADDRESS = None
TPU_CORES = 8
BATCH_SIZE = 32
SEQ_LENGTH = 512

tokenizer = None
estimator = None

app = Flask(__name__)

@app.route('/', methods=['POST'])
def receiveDocument():
    content = request.json
    # content[doc] should just be a string
    sentences = sent_tokenize(content['doc'])
    sentences = random.sample(sentences, min(len(sentences), 100))

    cleaned_sentences = clean_sentences(sentences)

    features = convert_sentences_to_features(cleaned_sentences, SEQ_LENGTH, tokenizer)

    unique_id_to_feature = {}
    for feature in features:
        unique_id_to_feature[feature.unique_id] = feature

    input_fn = input_fn_builder(features, SEQ_LENGTH)

    averaged_sentences = avgPredict(estimator, unique_id_to_feature, input_fn)

    return jsonify({"features": averaged_sentences})

def avgPredict(estimator, unique_id_to_feature, input_fn):
    sentences = []
    for result in estimator.predict(input_fn, yield_single_examples=True):
        unique_id = int(result['unique_id'])
        feature = unique_id_to_feature[unique_id]
        all_features = []
        for i, token in enumerate(feature.tokens):
            all_layers = []
            for j, layer_index in enumerate(layer_indices):
                layer_output = result["layer_output_%d" % j]
                layers = [
                    round(float(x), 6) for x in layer_output[i:(i + 1)].flat
                ]
                all_layers.append(layers)

            # this takes the average of a single token's layers
            all_layers_mean = np.array(all_layers).mean(axis=0).tolist()
            all_features.append(all_layers_mean)

        # takes the average of tokens in a sentence
        sentences.append(np.array(all_features).mean(axis=0).tolist())

    # takes the average of sentences
    return np.array(sentences).mean(axis=0).tolist()

def predict(estimator, unique_id_to_feature, input_fn):
    arr = []
    for result in estimator.predict(input_fn, yield_single_examples=True):
        unique_id = int(result['unique_id'])
        feature = unique_id_to_feature[unique_id]
        output_json = collections.OrderedDict()
        output_json['sentence_index'] = unique_id
        all_features = []
        for i, token in enumerate(feature.tokens):
            all_layers = []
            for j, layer_index in enumerate(layer_indices):
                layer_output = result["layer_output_%d" % j]
                layers = collections.OrderedDict()
                layers["index"] = layer_index
                layers["values"] = [
                    round(float(x), 6) for x in layer_output[i:(i + 1)].flat
                ]
                all_layers.append(layers)
            features = collections.OrderedDict()
            features["token"] = token
            features["layers"] = all_layers
            all_features.append(features)
        output_json['features'] = all_features
        arr.append(output_json)
    return arr

class InputSentence(object):
  def __init__(self, unique_id, text_a, text_b):
    self.unique_id = unique_id
    self.text_a = text_a
    self.text_b = text_b

def clean_sentences(sentences):
    cleaned_sentences = []
    i = 0
    for sentence in sentences:
        sentence = sentence.strip()
        text_a = None
        text_b = None

        # matches triple pipes for adding separator tokens in between pairs of sentences
        m = re.match(r"^(.*) \|\|\| (.*)$", sentence)

        if m is None:
            text_a = sentence
        else:
            text_a = m.group(1)
            text_b = m.group(2)
        cleaned_sentences.append(InputSentence(i, text_a, text_b))
        i += 1
    return cleaned_sentences

def truncate_seq_pair(tokens_a, tokens_b, max_length):
  """Truncates a sequence pair in place to the maximum length."""

  # This is a simple heuristic which will always truncate the longer sequence
  # one token at a time. This makes more sense than truncating an equal percent
  # of tokens from each, since if one sequence is very short then each token
  # that's truncated likely contains more information than a longer sequence.
  while True:
    total_length = len(tokens_a) + len(tokens_b)
    if total_length <= max_length:
      break
    if len(tokens_a) > len(tokens_b):
      tokens_a.pop()
    else:
      tokens_b.pop()

def input_fn_builder(features, seq_length):
    """Creates an `input_fn` closure to be passed to TPUEstimator."""
    all_unique_ids = []
    all_input_ids = []
    all_input_mask = []
    all_input_type_ids = []

    for feature in features:
        all_unique_ids.append(feature.unique_id)
        all_input_ids.append(feature.input_ids)
        all_input_mask.append(feature.input_mask)
        all_input_type_ids.append(feature.input_type_ids)
  
    def input_fn(params):
        """The actual input function."""
        batch_size = params["batch_size"]
  
        num_examples = len(features)
  
        # This is for demo purposes and does NOT scale to large data sets. We do
        # not use Dataset.from_generator() because that uses tf.py_func which is
        # not TPU compatible. The right way to load data is with TFRecordReader.
        d = tf.data.Dataset.from_tensor_slices({
            "unique_ids":
                tf.constant(all_unique_ids, shape=[num_examples], dtype=tf.int32),
            "input_ids":
                tf.constant(
                    all_input_ids, shape=[num_examples, seq_length],
                    dtype=tf.int32),
            "input_mask":
                tf.constant(
                    all_input_mask,
                    shape=[num_examples, seq_length],
                    dtype=tf.int32),
            "input_type_ids":
                tf.constant(
                    all_input_type_ids,
                    shape=[num_examples, seq_length],
                    dtype=tf.int32),
        })
  
        d = d.batch(batch_size=batch_size, drop_remainder=False)
        return d
  
    return input_fn

class InputFeatures(object):
  """A single set of features of data."""

  def __init__(self, unique_id, tokens, input_ids, input_mask, input_type_ids):
    self.unique_id = unique_id
    self.tokens = tokens
    self.input_ids = input_ids
    self.input_mask = input_mask
    self.input_type_ids = input_type_ids

def convert_sentences_to_features(cleaned_sentences, seq_length, tokenizer):
    features = []
    for (i, sentence) in enumerate(cleaned_sentences):
        tokens_a = tokenizer.tokenize(sentence.text_a)

        tokens_b = None
        if sentence.text_b:
            tokens_b = tokenizer.tokenize(sentence.text_b)

        if tokens_b:
            # minus 3 for CLS, SEP, SEP tokens since those 3 must be there
            # if there is a triple pipe (this if statement won't happen if
            # there is not a triple pipe)
            truncate_seq_pair(tokens_a, tokens_b, seq_length - 3)
        else:
            # account for CLS and SEP tokens with minus 2
            if len(tokens_a) > seq_length - 2:
                tokens_a = tokens_a[0:(seq_length - 2)]

        tokens = []
        input_type_ids = []
        tokens.append("[CLS]")
        input_type_ids.append(0)
        for token in tokens_a:
            tokens.append(token)
            input_type_ids.append(0)
        tokens.append("[SEP]")
        input_type_ids.append(0)

        if tokens_b:
            for token in tokens_b:
                tokens.append(token)
                input_type_ids.append(1)
            tokens.append("[SEP]")
            input_type_ids.append(1)

        input_ids = tokenizer.convert_tokens_to_ids(tokens)

        # The mask has 1 for real tokens and 0 for padding tokens. Only real
        # tokens are attended to.
        input_mask = [1] * len(input_ids)

        # Zero-pad up to the sequence length.
        while len(input_ids) < seq_length:
            input_ids.append(0)
            input_mask.append(0)
            input_type_ids.append(0)

        assert len(input_ids) == seq_length
        assert len(input_mask) == seq_length
        assert len(input_type_ids) == seq_length

        if i < 5:
            tf.logging.info("*** Example ***")
            tf.logging.info("unique_id: %s" % (sentence.unique_id))
            tf.logging.info("tokens: %s" % " ".join(
                [tokenization.printable_text(x) for x in tokens]))
            tf.logging.info("input_ids: %s" % " ".join([str(x) for x in input_ids]))
            tf.logging.info("input_mask: %s" % " ".join([str(x) for x in input_mask]))
            tf.logging.info(
                "input_type_ids: %s" % " ".join([str(x) for x in input_type_ids]))

        features.append(
            InputFeatures(
                unique_id=sentence.unique_id,
                tokens=tokens,
                input_ids=input_ids,
                input_mask=input_mask,
                input_type_ids=input_type_ids))
    return features

def bert_builder(bert_config, init_checkpoint, layer_indices, use_tpu, use_one_hot_embeddings):
    """Returns `model_fn` closure for TPUEstimator."""

    def bert_fn(features, labels, mode, params):
        """The `model_fn` for TPUEstimator."""

        unique_ids = features["unique_ids"]
        input_ids = features["input_ids"]
        input_mask = features["input_mask"]
        input_type_ids = features["input_type_ids"]

        model = modeling.BertModel(
            config=bert_config,
            is_training=False,
            input_ids=input_ids,
            input_mask=input_mask,
            token_type_ids=input_type_ids,
            use_one_hot_embeddings=use_one_hot_embeddings)

        tvars = tf.trainable_variables()
        scaffold_fn = None
        (assignment_map,
         initialized_variable_names) = modeling.get_assignment_map_from_checkpoint(
             tvars, init_checkpoint)

        if use_tpu:
            def tpu_scaffold():
                tf.train.init_from_checkpoint(init_checkpoint, assignment_map)
                return tf.train.Scaffold()

            scaffold_fn = tpu_scaffold
        else:
            tf.train.init_from_checkpoint(init_checkpoint, assignment_map)

        tf.logging.info("**** Trainable Variables ****")
        for var in tvars:
            init_string = ""
            if var.name in initialized_variable_names:
                init_string = ", *INIT_FROM_CKPT*"
            tf.logging.info("  name = %s, shape = %s%s", var.name, var.shape,
                            init_string)

        # grabs all encoder layers from transformer
        all_layers = model.get_all_encoder_layers()

        predictions = {
            "unique_id": unique_ids,
        }

        for (i, layer_index) in enumerate(layer_indices):
              predictions["layer_output_%d" % i] = all_layers[layer_index]

        output_spec = tf.contrib.tpu.TPUEstimatorSpec(
            mode=mode, predictions=predictions, scaffold_fn=scaffold_fn)
        return output_spec

    return bert_fn

def load_bert():
    tf.logging.set_verbosity(tf.logging.INFO)
    json_file = path.join(BERT_MODEL_DIR, 'bert_config.json')
    bert_config = modeling.BertConfig.from_json_file(json_file)

    vocab_file = path.join(BERT_MODEL_DIR, 'vocab.txt')

    global tokenizer
    tokenizer = tokenization.FullTokenizer(vocab_file=vocab_file, do_lower_case=uncased)

    model_fn = bert_builder(bert_config=bert_config,
                            init_checkpoint=path.join(BERT_MODEL_DIR, 'bert_model.ckpt'),
                            layer_indices=layer_indices,
                            use_tpu=TPU,
                            use_one_hot_embeddings=TPU)

    is_per_host = tf.contrib.tpu.InputPipelineConfig.PER_HOST_V2
    run_config = tf.contrib.tpu.RunConfig(master=TPU_ADDRESS,
                                          tpu_config=tf.contrib.tpu.TPUConfig(
                                              num_shards=TPU_CORES,
                                              per_host_input_for_training=is_per_host))

    global estimator
    estimator = tf.contrib.tpu.TPUEstimator(use_tpu=TPU,
                                            model_fn=model_fn,
                                            config=run_config,
                                            predict_batch_size=BATCH_SIZE)

    tf.logging.info("Done setting up Bert estimator.")

if __name__ == '__main__':
    load_bert()
    app.run(port=6666)
