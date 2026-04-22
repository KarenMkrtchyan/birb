import pika
import base64
import json
import cv2
from datetime import datetime


class BirdWatchQueue:

    def __init__(self, url: str, queue_name: str = 'birdwatch_detections'):
        self.url = url
        self.queue_name = queue_name
        self.connection = None
        self.channel = None
        self._connect()

    def _connect(self):
        params = pika.URLParameters(self.url)
        self.connection = pika.BlockingConnection(params)
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=self.queue_name, durable=True)
        print(f"Connected to RabbitMQ queue: {self.queue_name}")

    def _ensure_connection(self):
        try:
            self.connection.process_data_events()
        except (pika.exceptions.AMQPConnectionError,
                pika.exceptions.StreamLostError,
                AttributeError):
            print("Connection lost, reconnecting...")
            self._connect()

    def push_frame(self, frame, confidence: float, detections: list = None):
        self._ensure_connection()

        _, buffer = cv2.imencode(
            '.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
        image_b64 = base64.b64encode(buffer).decode('utf-8')

        payload = json.dumps({
            'timestamp': datetime.now().isoformat(),
            'confidence': confidence,
            'image': image_b64,
            'detections': detections or [],
        })

        self.channel.basic_publish(
            exchange='',
            routing_key=self.queue_name,
            body=payload,
            properties=pika.BasicProperties(delivery_mode=2)
        )
        print(f"Bird detected (conf={confidence:.2f}) — frame pushed at {datetime.now().isoformat()}")

    def close(self):
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            print("RabbitMQ connection closed")
