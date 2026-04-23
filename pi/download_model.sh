#!/bin/bash
# Run this once on your Pi to download the MobileNet SSD v2 model

set -e

MODEL_URL="https://storage.googleapis.com/download.tensorflow.org/models/tflite/coco_ssd_mobilenet_v1_1.0_quant_2018_06_29.zip"
ZIP_FILE="ssd_model.zip"

echo "Downloading MobileNet SSD model..."
wget -q "$MODEL_URL" -O "$ZIP_FILE"

echo "Extracting..."
unzip -o "$ZIP_FILE" detect.tflite
mv detect.tflite ssd_mobilenet_v2_coco.tflite

rm "$ZIP_FILE"
echo "Done! Model saved as ssd_mobilenet_v2_coco.tflite"
