📦 PLC Video Controller – Unified Installer Packaging Instructions

✅ CONTENTS:
- install_script.iss           → Inno Setup script to generate final installer
- prereq_installer.bat         → Batch script to install Python dependencies
- [PLACE FILE] PLCVideoController.exe → Built EXE from PyInstaller
- [PLACE FILE] python-3.10.11-amd64.exe → Python 3.10 installer (download manually)

📋 STEPS TO BUILD THE FINAL INSTALLER:

1. Build your app EXE:
   - Run this in your project folder:
     pyinstaller --noconfirm --onefile --add-data "videos;videos" plc_video_controller.py

2. Move files into this folder:
   - Copy `dist\PLCVideoController.exe` here
   - Download and copy `python-3.10.11-amd64.exe` from:
     https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe

3. Open Inno Setup
   - Load `install_script.iss`
   - Click “Compile”

4. Result:
   - `Output\PLCVideoControllerInstaller.exe` → your unified, single-step installer

💡 Notes:
- Installer will silently install Python if not present.
- Installer installs required Python packages automatically.
- Final app is installed in `C:\Program Files\PLCVideoController\`
- Desktop and Start Menu shortcuts are created.

Optional:
- Replace `icon.ico` with your own app icon.
