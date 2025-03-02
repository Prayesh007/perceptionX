# import sys
# import time

# from ultralytics import YOLO

# from PIL import Image
# import numpy as np
# import cv2
# import tempfile
# import subprocess
# import os
# import imageio_ffmpeg as ffmpeg


# weights_path = "./yolov11/best.pt"

# def load_model():
#     print(f"🔍 Checking if model exists: {weights_path}")

#     if not os.path.exists(weights_path):
#         print(f"❌ Model NOT FOUND at {weights_path}")
#         exit(1)  # Stop execution if model is missing

#     print(f"✅ Model exists: {weights_path}")    
#     model = YOLO(weights_path)
#     print("🔥 YOLO model loaded successfully!")
#     return model



# # Process the image
# def process_image(image_path, output_path, model):
#     image = Image.open(image_path)
#     image_np = np.array(image)
#     results = model(image_np)
#     annotated_image = results[0].plot()
#     cv2.imwrite(output_path, cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR))
#     print("Progress: 100%")  # Send progress update
#     print(f"Image processed and saved to {output_path}")

# # Process the video
# def process_video(video_path, output_path, model):
#     cap = cv2.VideoCapture(video_path)
#     total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
#     processed_frames = 0
#     temp_output = os.path.join(tempfile.gettempdir(), "temp_output.avi")

#     fourcc = cv2.VideoWriter_fourcc(*"XVID")
#     fps = int(cap.get(cv2.CAP_PROP_FPS))
#     width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
#     height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
#     out = cv2.VideoWriter(temp_output, fourcc, fps, (width, height))

#     while cap.isOpened():
#         ret, frame = cap.read()
#         if not ret:
#             break
#         results = model(frame)
#         annotated_frame = results[0].plot()
#         out.write(annotated_frame)
        
#         processed_frames += 1
#         progress = int((processed_frames / total_frames) * 100)
#         print(f"Progress: {progress}%")  # Send progress update

#     cap.release()
#     out.release()

#     convert_to_mp4(temp_output, output_path)
#     print(f"Video processed and saved to {output_path}")

# # Convert video to MP4
# def convert_to_mp4(input_file, output_file):
#     ffmpeg_command = ffmpeg.get_ffmpeg_exe()
#     command = [ffmpeg_command, "-y", "-i", input_file, "-vcodec", "libx264", "-crf", "23", "-preset", "fast", output_file]
#     subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# if __name__ == "__main__":
#     if len(sys.argv) < 4:
#         print("Usage: python app.py <input_path> <output_path> <type>")
#         sys.exit(1)

#     input_path = sys.argv[1]
#     output_path = sys.argv[2]
#     file_type = sys.argv[3]

#     model = load_model()

#     if file_type == "image":
#         process_image(input_path, output_path, model)
#     elif file_type == "video":
#         process_video(input_path, output_path, model)
#     else:
#         print("Invalid file type. Use 'image' or 'video'.")


import sys
import time
import pymongo
import gridfs
from ultralytics import YOLO
from PIL import Image
import numpy as np
import cv2
import tempfile
import subprocess
import os
import imageio_ffmpeg as ffmpeg
from io import BytesIO

# MongoDB Connection
client = pymongo.MongoClient("mongodb+srv://aitools2104:zmS7A45hKzw4LdTb@cluster0.tqkyb.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0&tls=true&tlsInsecure=false")
db = client["perceptionX"]
fs = gridfs.GridFS(db)

weights_path = "./yolov11/best.pt"

def load_model():
    print(f"🔍 Checking if model exists: {weights_path}")
    if not os.path.exists(weights_path):
        print(f"❌ Model NOT FOUND at {weights_path}")
        exit(1)
    print(f"✅ Model exists: {weights_path}")    
    model = YOLO(weights_path)
    print("🔥 YOLO model loaded successfully!")
    return model

def process_image(file_id, output_path, model):
    file = fs.find_one({"_id": pymongo.ObjectId(file_id)})
    if not file:
        print("❌ Image not found in MongoDB")
        exit(1)
    
    image = Image.open(BytesIO(file.read()))
    image_np = np.array(image)
    results = model(image_np)
    annotated_image = results[0].plot()
    _, buffer = cv2.imencode(".jpg", cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR))
    fs.put(buffer.tobytes(), filename=f"processed_{file.filename}")
    print("Progress: 100%")
    print(f"Image processed and saved to MongoDB")

def process_video(file_id, output_path, model):
    file = fs.find_one({"_id": pymongo.ObjectId(file_id)})
    if not file:
        print("❌ Video not found in MongoDB")
        exit(1)
    
    temp_video_path = os.path.join(tempfile.gettempdir(), "temp_video.mp4")
    with open(temp_video_path, "wb") as f:
        f.write(file.read())
    
    cap = cv2.VideoCapture(temp_video_path)
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
        print(f"Progress: {progress}%")

    cap.release()
    out.release()
    convert_to_mp4(temp_output, output_path)
    with open(output_path, "rb") as f:
        fs.put(f.read(), filename=f"processed_{file.filename}")
    print(f"Video processed and saved to MongoDB")

def convert_to_mp4(input_file, output_file):
    ffmpeg_command = ffmpeg.get_ffmpeg_exe()
    command = [ffmpeg_command, "-y", "-i", input_file, "-vcodec", "libx264", "-crf", "23", "-preset", "fast", output_file]
    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python app.py <file_id> <file_type>")
        sys.exit(1)
    
    file_id = sys.argv[1]
    file_type = sys.argv[2]
    model = load_model()
    
    if file_type.startswith("image"):
        process_image(file_id, None, model)
    elif file_type.startswith("video"):
        process_video(file_id, None, model)
    else:
        print("Invalid file type. Use 'image' or 'video'.")
