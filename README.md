# Fabel

## Team members
Parth Doshi (parthsdoshi), Max Lin (maxlincode)

## Goals
Tag files with multiple classes to easily index new downloads.
User can train the program as it indexes their files.

## Running this repo
1. First, download the Bert pretrained model from https://storage.googleapis.com/bert_models/2018_10_18/uncased_L-12_H-768_A-12.zip
2. Place the unzipped pretrained model in the `nn/bert/pretrained/` folder.
3. Navigate to the root of this repo and run `pip install -r requirements.txt`.
4. Run `cd nn/bert/ && python3 bert_server.py`.
5. This will load the Bert model and creates a REST API around it to respond to external requests.
6. Next, edit `app/server.py` and change the value of `BERT_SERVER` to the appropriate ip address and port.
7. Finally, navigate to `./app` and run `python3 main.py`. This will launch the frontend.
8. Drag and drop the chrome extension under `./chrome_extension/dist` in to chrome which will allow us to automatically run downloaded documents through the app and tag them.
