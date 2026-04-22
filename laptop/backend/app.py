# app.py
import pika
import json
from flask import Flask, jsonify, render_template
from classifier import BirdClassifier
from store import DetectionStore

# ------- config -------
CLOUDAMQP_URL = 'YOUR_CLOUDAMQP_URL'
QUEUE_NAME = 'birdwatch_detections'
# ----------------------

app = Flask(__name__)
store = DetectionStore(max_size=100)
classifier = BirdClassifier()

def get_channel():
    params = pika.URLParameters(CLOUDAMQP_URL)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    return connection, channel

@app.route('/poll')
def poll():
    """Pull one message from queue, classify it, store it"""
    try:
        connection, channel = get_channel()
        method, _, body = channel.basic_get(
            queue=QUEUE_NAME,
            auto_ack=False
        )

        if method is None:
            connection.close()
            return jsonify({'status': 'empty'})

        # parse the message from the Pi
        data = json.loads(body)

        # classify the bird
        classification = classifier.classify(data['image'])

        detection = {
            'timestamp': data['timestamp'],
            'pi_confidence': data['confidence'],
            'species': classification['species'],
            'species_confidence': classification['score'],
            'top_3': classification['top_3'],
            'image': data['image'],
        }

        store.add(detection)

        # only ack after successful classification
        channel.basic_ack(delivery_tag=method.delivery_tag)
        connection.close()

        return jsonify({'status': 'new', 'detection': detection})

    except Exception as e:
        print(f"Poll error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/detections')
def get_detections():
    return jsonify(store.get_all())

@app.route('/latest')
def get_latest():
    latest = store.get_latest()
    if latest is None:
        return jsonify({'status': 'empty'})
    return jsonify({'status': 'ok', 'detection': latest})

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)