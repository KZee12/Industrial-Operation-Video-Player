import requests
import subprocess
import os
import hashlib

SERVER_IP = "192.168.0.100"  # <-- Replace with actual server IP
APP_NAME = "client_app.exe"
LOCAL_COPY = os.path.join(os.getcwd(), APP_NAME)
REMOTE_URL = f"http://{SERVER_IP}:8000/{APP_NAME}"
VERSION_URL = f"http://{SERVER_IP}:8000/version.txt"

def get_remote_hash():
    try:
        return requests.get(VERSION_URL).text.strip()
    except:
        return None

def get_local_hash():
    if not os.path.exists(LOCAL_COPY):
        return None
    with open(LOCAL_COPY, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

def download_app():
    with requests.get(REMOTE_URL, stream=True) as r:
        r.raise_for_status()
        with open(LOCAL_COPY, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

def main():
    remote_hash = get_remote_hash()
    local_hash = get_local_hash()

    if remote_hash != local_hash:
        print("Updating client app...")
        download_app()

    subprocess.Popen([LOCAL_COPY], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

if __name__ == "__main__":
    main()
