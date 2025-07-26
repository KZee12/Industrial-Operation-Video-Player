import snap7
from snap7.util import get_byte
import requests
import time
import csv
import os
import subprocess
from datetime import datetime

# PLC Configuration
PLC_IP = '192.168.0.1'
RACK = 0
SLOT = 1
DB_NUMBER = 1
START_ADDRESS = 0
SIZE = 2

# Server video base URL
VIDEO_SERVER_URL = "http://192.168.0.100:8000/videos/"

# Video list (index-based)
VIDEO_LIST = [
    "video1.mp4",
    "video2.mp4",
    "video3.mp4"
]

# VLC command path
VLC_PATH = "C:\Program Files\VideoLAN\VLC\vlc.exe"

# Logging file path
LOG_FILE = "playback_log.csv"

def log_event(video_name, status):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([now, video_name, status])

def connect_to_plc():
    client = snap7.client.Client()
    client.connect(PLC_IP, RACK, SLOT)
    return client

def read_bytes(client):
    data = client.db_read(DB_NUMBER, START_ADDRESS, SIZE)
    byte0 = get_byte(data, 0)
    byte1 = get_byte(data, 1)
    return byte0, byte1

def play_video(video_index):
    video_name = VIDEO_LIST[video_index] if video_index < len(VIDEO_LIST) else None
    if not video_name:
        return None
    video_url = VIDEO_SERVER_URL + video_name
    subprocess.Popen([VLC_PATH, "--intf", "dummy", "--play-and-exit", video_url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    log_event(video_name, "PLAY")
    return video_name

def main():
    plc = connect_to_plc()
    current_video = None
    playing = False

    while True:
        try:
            byte0, byte1 = read_bytes(plc)
            if byte0 == 1 and not playing:
                current_video = play_video(byte1)
                playing = True
            elif byte0 == 0 and playing:
                subprocess.call(["taskkill", "/IM", "vlc.exe", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if current_video:
                    log_event(current_video, "STOP")
                playing = False
            time.sleep(1)
        except Exception as e:
            log_event("Error", str(e))
            time.sleep(2)

if __name__ == "__main__":
    main()
