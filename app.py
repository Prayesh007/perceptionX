# import sys
# import time
# import asyncio
# import base64
# from motor.motor_asyncio import AsyncIOMotorClient
# from ultralytics import YOLO
# from PIL import Image
# import numpy as np
# import cv2
# import tempfile
# import subprocess
# import os
# import imageio_ffmpeg as ffmpeg
# from io import BytesIO
# from bson import ObjectId  

# # 🔹 MongoDB Connection
# MONGO_URI = "mongodb+srv://aitools2104:kDTRxzV6MgO4nicA@cluster0.tqkyb.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0&tls=true&tlsInsecure=false"
# DATABASE_NAME = "test"
# COLLECTION_NAME = "files"

# #  Connect to MongoDB
# client = AsyncIOMotorClient(MONGO_URI)
# db = client[DATABASE_NAME]
# collection = db[COLLECTION_NAME]

# weights_path = "./yolov11/best.pt"

# def load_model():
#     print(f"🔍 Checking if model exists: {weights_path}")
#     if not os.path.exists(weights_path):
#         print(f" Model NOT FOUND at {weights_path}")
#         exit(1)
#     print(f" Model exists: {weights_path}")    
#     model = YOLO(weights_path)
#     print(" YOLO model loaded successfully!")
#     return model

# async def fetch_file_from_mongo(file_id):
#     """Fetch file from MongoDB using a valid ObjectId."""
#     print(f" Searching for file ID: {file_id}")

#     try:
#         object_id = ObjectId(file_id)
#     except Exception as e:
#         print(f" Invalid ObjectId format: {e}")
#         return None

#     file = await collection.find_one({"_id": object_id})

#     if file:
#         print(f" File Found: {file['filename']}")
#         file_data = file.get("data")
#         if not file_data:
#             print(" File data is missing in MongoDB")
#             return None
#         return file_data
#     else:
#         print(" File not found in MongoDB - Verify ID and Storage")
#         return None

# async def process_image(file_id, model):
#     """Processes an image using YOLO and updates MongoDB."""
#     image_data = await fetch_file_from_mongo(file_id)

#     if not image_data:
#         print(" Image data is missing")
#         return

#     try:
#         image = Image.open(BytesIO(image_data))
#         image.verify()  # Check for corruption
#         image = Image.open(BytesIO(image_data)).convert("RGB")  
#     except Exception as e:
#         print(f" Image decoding error: {e}")
#         return

#     image_np = np.array(image)

#     # 🔹 Run YOLO Detection
#     results = model(image_np)
#     annotated_image = results[0].plot()

#     #  Encode Processed Image
#     _, buffer = cv2.imencode(".jpg", cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR))
#     processed_image_binary = buffer.tobytes()  #  Convert to binary

#     await save_processed_file(file_id, processed_image_binary)

# async def save_processed_file(file_id, processed_data):
#     """Saves the processed file back to MongoDB as binary."""
#     try:
#         object_id = ObjectId(file_id)
#     except Exception as e:
#         print(f" Invalid ObjectId format: {e}")
#         return

#     result = await collection.update_one(
#         {"_id": object_id},
#         {"$set": {"processedData": processed_data}}  #  Store binary directly
#     )

#     if result.modified_count > 0:
#         print(f" Processed file saved to MongoDB for file ID: {file_id}")
#     else:
#         print(" Failed to save processed file in MongoDB")

# async def process_video(file_id, model):
#     """Processes a video using YOLO and updates MongoDB."""
#     file_data = await fetch_file_from_mongo(file_id)

#     #  Video data is directly available as bytes
#     video_binary = file_data

#     if not video_binary:
#         print(" Video data is missing in MongoDB")
#         return

#     #  Store video in a temporary file
#     temp_video_path = os.path.join(tempfile.gettempdir(), "temp_video.mp4")
#     with open(temp_video_path, "wb") as f:
#         f.write(video_binary)

#     # Open video file
#     cap = cv2.VideoCapture(temp_video_path)
#     if not cap.isOpened():
#         print(" Error opening video file")
#         return

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
#         print(f"Progress: {progress}%")

#     cap.release()
#     out.release()

#     #  Convert video to MP4
#     processed_video_path = convert_to_mp4(temp_output)

#     #  Read processed video
#     with open(processed_video_path, "rb") as f:
#         processed_video_binary = f.read()

#     #  Save processed video to MongoDB
#     await save_processed_file(file_id, processed_video_binary)

# def convert_to_mp4(input_file):
#     ffmpeg_command = ffmpeg.get_ffmpeg_exe()
#     output_file = input_file.replace(".avi", ".mp4")
#     command = [ffmpeg_command, "-y", "-i", input_file, "-vcodec", "libx264", "-crf", "23", "-preset", "fast", output_file]
#     subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#     return output_file

# if __name__ == "__main__":
#     if len(sys.argv) < 3:
#         print("Usage: python app.py <file_id> <file_type>")
#         sys.exit(1)

#     file_id = sys.argv[1]
#     file_type = sys.argv[2]
#     model = load_model()

#     #  Fix Event Loop Issue
#     try:
#         loop = asyncio.get_running_loop()
#     except RuntimeError:
#         loop = asyncio.new_event_loop()
#         asyncio.set_event_loop(loop)

#     if file_type.startswith("image"):
#         loop.run_until_complete(process_image(file_id, model))
#     elif file_type.startswith("video"):
#         loop.run_until_complete(process_video(file_id, model))
#     else:
#         print("Invalid file type. Use 'image' or 'video'.")





import sys
import time
import asyncio
import base64
from motor.motor_asyncio import AsyncIOMotorClient
from ultralytics import YOLO
from PIL import Image
import numpy as np
import cv2
import tempfile
import subprocess
import os
import imageio_ffmpeg as ffmpeg
from io import BytesIO
from bson import ObjectId  

# 🔹 MongoDB Connection
MONGO_URI = "mongodb+srv://aitools2104:kDTRxzV6MgO4nicA@cluster0.tqkyb.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0&tls=true&tlsInsecure=false"
DATABASE_NAME = "test"
COLLECTION_NAME = "files"

#  Connect to MongoDB
client = AsyncIOMotorClient(MONGO_URI)
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]

# **UPDATED:** Path to YOLO weights
weights_path = "./yolov11/best.pt"

def load_model():
    print(f"🔍 Checking if model exists: {weights_path}")
    if not os.path.exists(weights_path):
        print(f" Model NOT FOUND at {weights_path}")
        exit(1)
    print(f" Model exists: {weights_path}")    
    model = YOLO(weights_path)
    print(" YOLO model loaded successfully!")
    return model

async def fetch_file_from_mongo(file_id):
    """Fetch file from MongoDB using a valid ObjectId."""
    print(f" Searching for file ID: {file_id}")

    try:
        object_id = ObjectId(file_id)
    except Exception as e:
        print(f" Invalid ObjectId format: {e}")
        return None

    file = await collection.find_one({"_id": object_id})

    if file:
        print(f" File Found: {file['filename']}")
        file_data = file.get("data")
        if not file_data:
            print(" File data is missing in MongoDB")
            return None
        return file_data
    else:
        print(" File not found in MongoDB - Verify ID and Storage")
        return None

async def process_image(file_id, model):
    """Processes an image using YOLO and updates MongoDB."""
    image_data = await fetch_file_from_mongo(file_id)

    if not image_data:
        print(" Image data is missing")
        return

    try:
        image = Image.open(BytesIO(image_data))
        image.verify()  # Check for corruption
        image = Image.open(BytesIO(image_data)).convert("RGB")  
    except Exception as e:
        print(f" Image decoding error: {e}")
        return

    image_np = np.array(image)

    # 🔹 Run YOLO Detection
    results = model(image_np)
    annotated_image = results[0].plot()

    #  Encode Processed Image
    _, buffer = cv2.imencode(".jpg", cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR))
    processed_image_binary = buffer.tobytes()  #  Convert to binary

    await save_processed_file(file_id, processed_image_binary)

async def save_processed_file(file_id, processed_data):
    """Saves the processed file back to MongoDB as binary."""
    try:
        object_id = ObjectId(file_id)
    except Exception as e:
        print(f" Invalid ObjectId format: {e}")
        return

    result = await collection.update_one(
        {"_id": object_id},
        {"$set": {"processedData": processed_data}}  #  Store binary directly
    )

    if result.modified_count > 0:
        print(f" Processed file saved to MongoDB for file ID: {file_id}")
    else:
        print(" Failed to save processed file in MongoDB")

async def process_video(file_id, model):
    """Processes a video using YOLO and updates MongoDB."""
    file_data = await fetch_file_from_mongo(file_id)

    if not file_data:
        print(" Video data is missing in MongoDB")
        return

    #  Store video in a temporary file
    temp_video_path = os.path.join(tempfile.gettempdir(), "temp_video.mp4")
    with open(temp_video_path, "wb") as f:
        f.write(file_data)

    cap = cv2.VideoCapture(temp_video_path)
    if not cap.isOpened():
        print(" Error opening video file")
        return

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

    processed_video_path = convert_to_mp4(temp_output)

    with open(processed_video_path, "rb") as f:
        processed_video_binary = f.read()

    await save_processed_file(file_id, processed_video_binary)

def convert_to_mp4(input_file):
    ffmpeg_command = ffmpeg.get_ffmpeg_exe()
    output_file = input_file.replace(".avi", ".mp4")
    command = [ffmpeg_command, "-y", "-i", input_file, "-vcodec", "libx264", "-crf", "23", "-preset", "fast", output_file]
    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return output_file

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python app.py <file_id> <file_type>")
        sys.exit(1)

    file_id = sys.argv[1]
    file_type = sys.argv[2]
    model = load_model()

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if file_type.startswith("image"):
        loop.run_until_complete(process_image(file_id, model))
    elif file_type.startswith("video"):
        loop.run_until_complete(process_video(file_id, model))
    else:
        print("Invalid file type. Use 'image' or 'video'.")
