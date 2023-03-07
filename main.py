import base64
from flask import Flask, request, jsonify, render_template, make_response
import json
from summarizer import summarize_text, summarize_page, embed_text, closest_embeddings, cluster, get_job_status, visualize
import multiprocessing
import uuid
import io

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

@app.route('/cluster', methods=['POST'])
def cluster_api():
    data = request.get_json()
    batch_id = data['batch_id']
    k = data['k']

    # generate a unique uuid as the job id
    job_id = str(uuid.uuid4())

    process = multiprocessing.Process(target=cluster, args=(batch_id, k, job_id))
    process.start()

    response = {
        'status': 'ok',
        'job_id': job_id
    }
    return jsonify(response)

# return the status of a job from the jobs table in the database
@app.route('/jobs/<job_id>', methods=['GET'])
def jobs(job_id):
    status = get_job_status(job_id)

    # if the status is None, then the job_id was not found in the database and we should return a 404
    if status is None:
        return 'Not found', 404
    else:
        response = {
            'status': status
        }
        return jsonify(response)

@app.route('/embed', methods=['POST'])
def embed():
    data = request.get_json()
    text = data['text']
    batch_id = data['batch_id']

    embedding_id = embed_text(text, batch_id)

    response = {
        'embedding_id': embedding_id
    }
    return jsonify(response)

@app.route('/embed/closest', methods=['GET'])
def closest():
    embedding_id = request.args.get('id')
    n = request.args.get('n') or 5

    closest = closest_embeddings(embedding_id, n)

    response = closest 
    return jsonify(response)

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

    data = install_defaults(data)

    text = data['text']
    summary = summarize_text(text, data)
    response = {
        'summary': summary
    }
    return jsonify(response)

@app.route('/visualize/<batch_id>', methods=['GET'])
def reduce_vectors(batch_id):
    image = visualize(batch_id)

    # create a response object from the image data
    img_bytes = io.BytesIO()
    image.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    response = make_response(img_bytes.getvalue())
    response.headers.set('Content-Type', 'image/png')

    return response


if __name__ == '__main__':
    app.run()
