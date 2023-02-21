import base64
from flask import Flask, request, jsonify
import json
from summarizer import summarize_text

app = Flask(__name__)


@app.route('/')
def answer_to_everything():
    return '42'


@app.route('/summarize', methods=['POST'])
def summarize():
    if request.content_encoding == 'base64':
        # Decode the base64-encoded message body
        encoded_body = request.get_data()
        decoded_body = base64.b64decode(encoded_body)
        decoded_string = decoded_body.decode('ascii', 'ignore')
        print(decoded_string)
        data = json.loads(decoded_string)
    else:
        data = request.get_json()
    text = data['text']
    summary = summarize_text(text)
    response = {
        'summary': summary
    }
    return jsonify(response)


if __name__ == '__main__':
    app.run()
