# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['plc_video_controller.py'],
    pathex=[],
    binaries=[('D:\\00 BIZ\\00 FY 25-26\\04] Projects 25-26\\W2526004_KSB - AR Guided Digital SOP for Solar Pump Controller Assembly\\04 Engineering\\03 Programming\\Playback Software\\R06_Local Version with Simulation Controls (ChatGPT)\\snap7.dll', '.')],
    datas=[('videos', 'videos')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='plc_video_controller',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
