import sys
import time

# Install ultralytics if not available
try:
    import ultralytics
except ModuleNotFoundError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "ultralytics"])
    import ultralytics

# Now import YOLO
from ultralytics import YOLO
from PIL import Image
import numpy as np
import cv2
import tempfile
import subprocess
import os
import imageio_ffmpeg as ffmpeg

# Load the YOLO model
def load_model():
    weights_path = "./runs/detect/train/weights/best.pt"
    model = YOLO(weights_path)
    return model

# Process the image
def process_image(image_path, output_path, model):
    image = Image.open(image_path)
    image_np = np.array(image)
    results = model(image_np)
    annotated_image = results[0].plot()
    cv2.imwrite(output_path, cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR))
    print("Progress: 100%")  # Send progress update
    print(f"Image processed and saved to {output_path}")

# Process the video
def process_video(video_path, output_path, model):
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    processed_frames = 0
    temp_output = os.path.join(tempfile.gettempdir(), "temp_output.avi")

    fourcc = cv2.VideoWriter_fourcc(*"XVID")
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    out = cv2.VideoWriter(temp_output, fourcc, fps, (width, height))

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        results = model(frame)
        annotated_frame = results[0].plot()
        out.write(annotated_frame)
        
        processed_frames += 1
        progress = int((processed_frames / total_frames) * 100)
        print(f"Progress: {progress}%")  # Send progress update

    cap.release()
    out.release()

    convert_to_mp4(temp_output, output_path)
    print(f"Video processed and saved to {output_path}")

# Convert video to MP4
def convert_to_mp4(input_file, output_file):
    ffmpeg_command = ffmpeg.get_ffmpeg_exe()
    command = [ffmpeg_command, "-y", "-i", input_file, "-vcodec", "libx264", "-crf", "23", "-preset", "fast", output_file]
    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python app.py <input_path> <output_path> <type>")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]
    file_type = sys.argv[3]

    model = load_model()

    if file_type == "image":
        process_image(input_path, output_path, model)
    elif file_type == "video":
        process_video(input_path, output_path, model)
    else:
        print("Invalid file type. Use 'image' or 'video'.")

