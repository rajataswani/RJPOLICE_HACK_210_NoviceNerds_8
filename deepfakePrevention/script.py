from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import hashlib
from datetime import datetime
import json
from typing import Optional

app = FastAPI()

# Define the path to the JSON database file
DB_FILE = "hash_database.json"

# Schema for video data
class VideoData:
    def __init__(self, video_name: str, video_hash: str, timestamp: str):
        self.video_name = video_name
        self.video_hash = video_hash
        self.timestamp = timestamp

def read_database():
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def write_database(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)

@app.post("/timestamp_video/")
async def timestamp_video(file: UploadFile = File(...), video_name: str = "Unnamed"):
    try:
        # Read the video file content
        video_content = await file.read()

        # Generate a cryptographic hash of the video content
        video_hash = hashlib.sha256(video_content).hexdigest()

        # Get the current date and time in UTC
        current_datetime = datetime.utcnow().isoformat()

        # Read the existing database
        database = read_database()

        # Store the hash, video name, and timestamp in the database
        database[video_hash] = {"video_name": video_name, "timestamp": current_datetime}

        # Write the updated database back to the file
        write_database(database)

        # Create a timestamped result
        timestamped_result = {
            "video_name": video_name,
            "video_hash": video_hash,
            "timestamp": current_datetime,
        }

        return JSONResponse(content=timestamped_result, status_code=200)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

@app.get("/get_database/")
async def get_database():
    # Read and return the entire database
    database = read_database()
    return database

@app.get("/verify_video/")
async def verify_video(video_hash: str):
    # Check if the given video hash is present in the database
    database = read_database()
    video_data = database.get(video_hash)

    if video_data:
        return {"status": "verified", "video_data": video_data}
    else:
        return {"status": "unverified"}
