# 🏗️ KSB Video Playback System – Deployment Guide

This guide explains how to set up the **server and client** system for centralized video playback based on data from a Siemens S7-1200 PLC.

---

## 📁 Folder Structure (On Server)

```
C:\KSB_Server\
├── client_app.exe          # ✅ Compiled client app (runs on clients)
├── version.txt             # ✅ SHA256 hash of the exe for update checking
├── start_server.bat        # ✅ Launches HTTP server to host app + videos
├── start_client.py         # ✅ Script for clients to fetch and run app
└── videos\
    ├── video1.mp4
    └── video2.mp4
```

---

## 🖥️ SERVER SETUP INSTRUCTIONS

### ✅ Step 1: Create `client_app.exe`

1. Install Python 3.10
2. Install dependencies:
   ```bash
   pip install python-snap7 requests
   ```
3. Create the EXE:
   ```bash
   pyinstaller --noconsole --onefile client_app.py
   ```
4. Copy the generated `dist/client_app.exe` to `C:\KSB_Server\`

---

### ✅ Step 2: Generate `version.txt`

1. Open Command Prompt in `C:\KSB_Server\`
2. Run:
   ```bash
   certutil -hashfile client_app.exe SHA256
   ```
3. Copy the hash and save it in a new file named `version.txt` in the same folder

---

### ✅ Step 3: Add Video Files

Put all your `videoX.mp4` files into:
```
C:\KSB_Server\videos\
```

---

### ✅ Step 4: Start HTTP Server

1. In `C:\KSB_Server\`, run:
   ```bash
   start_server.bat
   ```
2. This starts a server at:  
   `http://<server-ip>:8000/`

Test in browser:  
- `http://<server-ip>:8000/client_app.exe`  
- `http://<server-ip>:8000/videos/video1.mp4`

---

## 💻 CLIENT SETUP INSTRUCTIONS

### ✅ Step 1: Copy `start_client.py` to Client

1. On the client PC, open `start_client.py`
2. Change the IP:
   ```python
   SERVER_IP = "192.168.0.100"  # Replace with actual server IP
   ```

---

### ✅ Step 2: (Optional) Compile Launcher to EXE

```bash
pyinstaller --noconsole --onefile start_client.py
```

---

### ✅ Step 3: Auto-Start on Boot

1. Press `Win + R`, type:
   ```
   shell:startup
   ```
2. Paste a shortcut to:
   - `start_client.exe` OR
   - `python start_client.py`

---

### 🔄 How It Works

- Client checks `version.txt` on server
- If the EXE hash changed, it downloads the latest `client_app.exe`
- Then runs it silently in background
- App reads PLC data, plays videos, and logs activity locally

---

## ✅ Notes

- VLC must be installed at: `C:\Program Files\VideoLAN\VLC\vlc.exe`
- Firewall must allow port **8000**
- PLC must be reachable on its IP (default: `192.168.0.1`)
- Client stores logs in `playback_log.csv`

---