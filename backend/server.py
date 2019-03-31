from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/', methods=['POST'])
def receiveDownloadData():
    content = request.json
    print(content)
    return jsonify({"error": False})

if __name__ == '__main__':
    app.run(port=4994)