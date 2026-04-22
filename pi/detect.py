import os
import numpy as np
import cv2
from tflite_runtime.interpreter import Interpreter

# COCO class ID for "bird" (1-indexed in the SSD output)
BIRD_CLASS_ID = 15

# Load model relative to this script's directory
_dir = os.path.dirname(__file__)
_model_path = os.path.join(_dir, 'ssd_mobilenet_v2_coco.tflite')

interpreter = Interpreter(model_path=_model_path)
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

# Expected input size (typically 300x300 for MobileNet SSD)
_input_h = input_details[0]['shape'][1]
_input_w = input_details[0]['shape'][2]


def detect_birds(frame, threshold=0.5):
    """
    Run MobileNet SSD on a frame and return any bird detections.

    Returns:
        list of dicts, each with:
            'confidence': float,
            'bbox': (x_min, y_min, x_max, y_max) in pixel coords
    """
    h, w, _ = frame.shape

    # Preprocess: resize and add batch dimension
    img = cv2.resize(frame, (_input_w, _input_h))
    input_data = np.expand_dims(img, axis=0).astype(np.uint8)

    interpreter.set_tensor(input_details[0]['index'], input_data)
    interpreter.invoke()

    # SSD outputs: boxes, classes, scores, num_detections
    boxes = interpreter.get_tensor(output_details[0]['index'])[0]    # [N, 4]
    classes = interpreter.get_tensor(output_details[1]['index'])[0]  # [N]
    scores = interpreter.get_tensor(output_details[2]['index'])[0]   # [N]

    detections = []
    for i in range(len(scores)):
        if scores[i] < threshold:
            continue
        if int(classes[i]) != BIRD_CLASS_ID:
            continue

        # Boxes are [y_min, x_min, y_max, x_max] normalized 0-1
        y_min, x_min, y_max, x_max = boxes[i]
        detections.append({
            'confidence': float(scores[i]),
            'bbox': (
                int(x_min * w),
                int(y_min * h),
                int(x_max * w),
                int(y_max * h),
            ),
        })

    return detections


def bird_detection_result(frame, threshold=0.5):
    """
    Backward-compatible wrapper used by main.py.

    Returns:
        (present: bool, best_confidence: float, detections: list)
    """
    dets = detect_birds(frame, threshold)
    if dets:
        best = max(dets, key=lambda d: d['confidence'])
        return (True, best['confidence'], dets)
    return (False, 0.0, [])
