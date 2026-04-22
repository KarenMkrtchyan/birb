# store.py
from collections import deque

class DetectionStore:
    def __init__(self, max_size: int = 100):
        # deque automatically drops oldest when full
        self.detections = deque(maxlen=max_size)

    def add(self, detection: dict):
        self.detections.appendleft(detection)

    def get_all(self) -> list:
        return list(self.detections)

    def get_latest(self) -> dict | None:
        return self.detections[0] if self.detections else None