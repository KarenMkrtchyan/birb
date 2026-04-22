import os
import time

import cv2

from detect import bird_detection_result
from stream import BirdWatchQueue

# Run inference every Nth frame to limit CPU on the Pi.
FRAME_STRIDE = 5
PI_STATE_INTERVAL_SEC = 5


def main():
    """
    Connects to the RabbitMQ queue, checks each frame for bird. if bird exists pushes frame to queue
    """
    
    amqp_url = "amqps://aagqarjc:Vrbywwd09gaR-V7RuMFfkmzI2--i7TrO@duck.lmq.cloudamqp.com/aagqarjc"
   
    bird_watch_queue = BirdWatchQueue(amqp_url)
    cam_index = int(os.environ.get("CAMERA_INDEX", "0"))
    cap = cv2.VideoCapture(cam_index)
    try:
        if not cap.isOpened():
            raise SystemExit(f"Could not open camera index {cam_index}")

        bird_watch_queue.push_pi_state_on()
        last_state_push = time.monotonic()
        frame_i = 0
        try:
            while True:
                ok, frame = cap.read()
                if not ok:
                    break

                now = time.monotonic()
                if now - last_state_push >= PI_STATE_INTERVAL_SEC:
                    bird_watch_queue.push_pi_state_on()
                    last_state_push = now

                frame_i += 1
                if frame_i % FRAME_STRIDE != 0:
                    continue

                present, confidence = bird_detection_result(frame)
                if present:
                    bird_watch_queue.push_frame(frame, confidence)
        except KeyboardInterrupt:
            pass
    finally:
        cap.release()
        bird_watch_queue.close()


if __name__ == "__main__":
    main()
