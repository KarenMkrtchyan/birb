# queue_client.py
import pika
import base64
import json
import cv2
from datetime import datetime


class BirdWatchQueue:

    def __init__(
        self,
        url: str,
        queue_name: str = 'birdwatch_detections',
        state_queue_name: str = 'birdwatch_pi_state',
    ):
        self.url = url
        self.queue_name = queue_name
        self.state_queue_name = state_queue_name
        self.connection = None
        self.channel = None
        self._connect()

    def _connect(self):
        params = pika.URLParameters(self.url)
        self.connection = pika.BlockingConnection(params)
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=self.queue_name, durable=True)
        self.channel.queue_declare(queue=self.state_queue_name, durable=True)
        print(
            f"Connected to RabbitMQ queues: {self.queue_name}, "
            f"{self.state_queue_name}"
        )

    def _ensure_connection(self):
        try:
            self.connection.process_data_events()
        except (pika.exceptions.AMQPConnectionError,
                pika.exceptions.StreamLostError,
                AttributeError):
            print("Connection lost, reconnecting...")
            self._connect()

    def push_frame(self, frame, confidence: float):
        self._ensure_connection()

        _, buffer = cv2.imencode(
            '.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
        image_b64 = base64.b64encode(buffer).decode('utf-8')

        payload = json.dumps({
            'timestamp': datetime.now().isoformat(),
            'confidence': confidence,
            'image': image_b64,
        })

        self.channel.basic_publish(
            exchange='',
            routing_key=self.queue_name,
            body=payload,
            properties=pika.BasicProperties(delivery_mode=2)
        )
        print(f"Frame pushed to queue at {datetime.now().isoformat()}")

    def push_pi_state_on(self):
        self._ensure_connection()
        payload = json.dumps({
            'state': 'on',
            'timestamp': datetime.now().isoformat(),
        })
        self.channel.basic_publish(
            exchange='',
            routing_key=self.state_queue_name,
            body=payload,
            properties=pika.BasicProperties(delivery_mode=2),
        )
        print('on')

    def close(self):
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            print("RabbitMQ connection closed")