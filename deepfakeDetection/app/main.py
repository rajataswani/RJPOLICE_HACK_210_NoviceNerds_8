from flask import Flask, render_template, request
import os
import cv2
import numpy as np
import requests
import io
import random

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def extract_sophisticated_face(source_png_file):
    try:
        # Load the image using OpenCV
        image = cv2.imread(source_png_file)

        # Ensure image is loaded successfully
        if image is None:
            raise ValueError(f"Failed to load image: {source_png_file}")

        # Load the pre-trained Haar cascade classifier for face detection
        face_cascade = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")

        # Convert the image to grayscale for face detection
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Detect faces in the image
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )

        # Extract the first detected face (if any)
        if len(faces) > 0:
            (x, y, w, h) = faces[0]
            face_image = image[y:y+h, x:x+w]

            # Apply sophistication techniques to the extracted face
            gray_face = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
            blur_face = cv2.GaussianBlur(gray_face, (5, 5), 0)
            edges_face = cv2.Canny(blur_face, 100, 200)

            return edges_face
        else:
            print("No face detected in the image.")
            return source_png_file

    except Exception as e:
        print(f"Error during face extraction: {e}")
        return source_png_file


def extract_random_frame(video_path):
    vidcap = cv2.VideoCapture(video_path)
    # get total number of frames
    total_frames = int(vidcap.get(cv2.CAP_PROP_FRAME_COUNT))
    random_frame_number = 1
    # set frame position
    vidcap.set(cv2.CAP_PROP_POS_FRAMES, random_frame_number)
    success, frame = vidcap.read()
    if success:
        # Convert the frame to PNG format
        _, buffer = cv2.imencode(".png", frame)
        png_image = np.array(buffer).tobytes()
    return extract_sophisticated_face(png_image)

def detect_deepfake(png_image):
    url = "https://api.faceonlive.com/zmmss2fybc25ysk9/api/liveness"
    files = {'image': ('frame.png', png_image)}  # Pass the bytes directly
    headers = {"X-BLOBR-KEY": "9FdlnmKAPM16frwwAK2RSK4DWlRNIHWv"}
    response = requests.post(url, files=files, headers=headers)
    x = response.json()
    return x["data"]["result"]

def get_next_video_id():
    existing_ids = [int(file.split('_')[0]) for file in os.listdir(app.config['UPLOAD_FOLDER']) if file.endswith('.mp4')]
    return max(existing_ids, default=0) + 1

@app.route('/upload', methods=['POST'])
def upload():
    if 'video' not in request.files:
        return render_template('index.html', result='Error: No video file provided')

    video_file = request.files['video']

    if video_file.filename == '':
        return render_template('index.html', result='Error: No selected file')

    # Get the next available video ID
    video_id = get_next_video_id()

    # Save the uploaded video data to a file in the 'uploads' folder with an incrementing ID
    video_filename = f"{video_id}_temp_video.mp4"
    temp_video_path = os.path.join(app.config['UPLOAD_FOLDER'], video_filename)
    video_file.save(temp_video_path)

    # If it's a video, extract a random frame
    png_image = extract_random_frame(temp_video_path)

    # Perform deepfake detection using the temporary file
    result = detect_deepfake(png_image)
    if result in ["small face", "spoof"]:
        result="deepfake"

    # Display the result immediately after uploading
    return render_template('results.html', result=result)

@app.route('/')
def index():
    return render_template('index.html', result=None)

if __name__ == '__main__':
    app.run(debug=True)