import base64
import numpy as np
import cv2
from PIL import Image
from transformers import pipeline

class BirdClassifier:
    def __init__(self):
        print("Loading bird classifier")
        self.pipe = pipeline(
            task='image-classification',
            model='chriamue/bird-species-classifier',
        )
        print("Classifier ready")

    def classify(self, image_b64: str) -> dict:
        img_bytes = base64.b64decode(image_b64)
        np_arr = np.frombuffer(img_bytes, dtype=np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(frame_rgb)

        results = self.pipe(pil_image)
        top = results[0]

        return {
            'species': top['label'],
            'score': round(top['score'], 3),
            'top_3': [
                {'species': r['label'], 'score': round(r['score'], 3)}
                for r in results[:3]
            ]
        }