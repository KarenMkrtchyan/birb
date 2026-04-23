import time
from picamera2 import Picamera2
from detect import bird_detection_result
from stream import BirdWatchQueue

# Run inference every Nth frame to limit CPU on the Pi.
FRAME_STRIDE = 5
PI_STATE_INTERVAL_SEC = 5


def main():
    """
    Connects to the RabbitMQ queue, checks each frame for bird.
    If bird exists, pushes frame + bounding box data to queue.
    """
    amqp_url = "amqps://aagqarjc:Vrbywwd09gaR-V7RuMFfkmzI2--i7TrO@duck.lmq.cloudamqp.com/aagqarjc"

    bird_watch_queue = BirdWatchQueue(amqp_url)

    picam2 = Picamera2()
    config = picam2.create_still_configuration(
        main={"size": (640, 480), "format": "RGB888"}
    )
    picam2.configure(config)
    picam2.start()
    time.sleep(2)  # camera warm-up

    try:
        frame_i = 0
        try:
            while True:
                frame = picam2.capture_array()

                now = time.monotonic()
                if now - last_state_push >= PI_STATE_INTERVAL_SEC:
                    bird_watch_queue.push_pi_state_on()
                    last_state_push = now

                frame_i += 1
                if frame_i % FRAME_STRIDE != 0:
                    continue

                present, confidence, detections = bird_detection_result(frame)
                if present:
                    bird_watch_queue.push_frame(frame, confidence, detections)
        except KeyboardInterrupt:
            pass
    finally:
        picam2.stop()
        bird_watch_queue.close()


if __name__ == "__main__":
    main()