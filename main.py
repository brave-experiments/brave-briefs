import base64
from flask import Flask, request, jsonify, render_template
import json
from summarizer import summarize_text, summarize_page, train

app = Flask(__name__)


def install_defaults(data):
    if 'max_length' not in data:
        data['max_length'] = 3000
    if 'min_length' not in data:
        data['min_length'] = 10
    if 'do_sample' not in data:
        data['do_sample'] = False
    return data


@app.route('/')
def index():
    return render_template('summarize.html')


@app.route('/page', methods=['POST'])
def summarize_a_page():
    data = request.get_json()
    data = install_defaults(data)

    url = data['url']
    summary = summarize_page(url, data)
    response = {
        'summary': summary
    }
    return jsonify(response)


@ app.route('/summarize', methods=['POST'])
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

    data = install_defaults(data)

    text = data['text']
    summary = summarize_text(text, data)
    response = {
        'summary': summary
    }
    return jsonify(response)


@app.route('/train', methods=['POST'])
def train_model():
    data = request.get_json()
    text = data['text']
    summary_text = data['summary_text']
    train(text, summary_text)
    return '', 200


if __name__ == '__main__':
    app.run()
