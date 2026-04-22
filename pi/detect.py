from tflite_runtime.interpreter import Interpreter
import numpy as np
import cv2

interpreter = Interpreter(model_path='bird_classifier.tflite')
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

def _bird_score(frame):
    img = cv2.resize(frame, (224, 224))
    img = np.expand_dims(img / 255.0, axis=0).astype(np.float32)

    interpreter.set_tensor(input_details[0]['index'], img)
    interpreter.invoke()

    return float(interpreter.get_tensor(output_details[0]['index'])[0][0])


def bird_detection_result(frame, threshold=0.7):
    score = _bird_score(frame)
    return (score > threshold, score)


def is_bird_present(frame, threshold=0.7):
    return bird_detection_result(frame, threshold)[0]