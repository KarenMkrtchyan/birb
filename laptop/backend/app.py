import pika
import json
import time
from google import genai
from flask import Flask, jsonify, render_template, request
from classifier import BirdClassifier
from store import DetectionStore

# configs
CLOUDAMQP_URL = 'amqps://aagqarjc:Vrbywwd09gaR-V7RuMFfkmzI2--i7TrO@duck.lmq.cloudamqp.com/aagqarjc'
QUEUE_NAME = 'birdwatch_detections'
PI_STATE_QUEUE = 'birdwatch_pi_state'
PI_TIMEOUT_SEC = 12

last_pi_msg = 0
GEMINI_API_KEY = 'AIzaSyDwYXDAHmCTWDyCpQ6ESxQvZKhsj__361E'

gemini = genai.Client(api_key=GEMINI_API_KEY)
facts_cache = {}

def get_bird_facts(species: str) -> str:
    if species in facts_cache:
        return facts_cache[species]
    try:
        response = gemini.models.generate_content(
            model='gemini-2.5-flash-lite',
            contents=f"Give me 2-3 interesting facts about the {species} in 2-3 short sentences. Be concise and engaging."
        )
        facts_cache[species] = response.text.strip()
        return facts_cache[species]
    except Exception as e:
        print(f"Gemini error: {e}")
        return ""

app = Flask(__name__, template_folder='../frontend')
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
    # Pull one message from queue
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
            'facts': get_bird_facts(classification['species']),
        }

        store.add(detection)

        # only ack after successful classification
        channel.basic_ack(delivery_tag=method.delivery_tag)
        connection.close()

        return jsonify({'status': 'new', 'detection': detection})

    except Exception as e:
        print(f"Poll error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/pi_status')
def pi_status():
    global last_pi_msg
    try:
        params = pika.URLParameters(CLOUDAMQP_URL)
        connection = pika.BlockingConnection(params)
        channel = connection.channel()
        channel.queue_declare(queue=PI_STATE_QUEUE, durable=True)
        while True:
            method, _, body = channel.basic_get(queue=PI_STATE_QUEUE, auto_ack=True)
            if method is None:
                break
            last_pi_msg = time.time()
        connection.close()
    except Exception:
        pass
    online = (time.time() - last_pi_msg) < PI_TIMEOUT_SEC
    return jsonify({'online': online})

@app.route('/detections')
def get_detections():
    date = request.args.get('date')
    all_detections = store.get_all()
    if date:
        all_detections = [d for d in all_detections if d['timestamp'].startswith(date)]
    return jsonify(all_detections)

@app.route('/calendar')
def get_calendar():
    counts = {}
    for d in store.get_all():
        day = d['timestamp'][:10]
        counts[day] = counts.get(day, 0) + 1
    return jsonify(counts)

@app.route('/detections/<int:detection_id>', methods=['DELETE'])
def delete_detection(detection_id):
    store.delete(detection_id)
    return jsonify({'status': 'ok'})

@app.route('/detections', methods=['DELETE'])
def clear_detections():
    store.clear()
    return jsonify({'status': 'ok'})

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
    app.run(debug=True, port=5001)