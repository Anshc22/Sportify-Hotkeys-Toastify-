# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

# Get the current working directory
application_path = os.getcwd()

# Define icon path
icon_path = os.path.join(application_path, 'icon.ico')
if not os.path.exists(icon_path):
    raise FileNotFoundError(f"Icon file not found at {icon_path}")

# Collect all tkinter submodules
tkinter_submodules = collect_submodules('tkinter')

a = Analysis(
    ['main.py'],
    pathex=[application_path],
    binaries=[],
    datas=[
        ('src/*.py', 'src'),
        (icon_path, '.'),  # Always include icon
        ('spotify_config.json', '.'),
        ('.custom_color', '.') if os.path.exists('.custom_color') else None,
        ('.window_position', '.') if os.path.exists('.window_position') else None,
    ],
    hiddenimports=[
        # Tkinter modules
        'tkinter',
        'tkinter.ttk',
        'tkinter.colorchooser',
        'tkinter.font',
        'tkinter.messagebox',
        '_tkinter',
        *tkinter_submodules,
        
        # PIL modules
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'PIL._tkinter_finder',
        
        # Spotify modules
        'spotipy',
        'spotipy.oauth2',
        'spotipy.util',
        'spotipy.client',
        
        # Other dependencies
        'requests',
        'colorthief',
        'python_dotenv',
        'webbrowser',
        'json',
        'ctypes',
        'urllib3',
        'certifi'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)

# Remove None entries from datas
a.datas = [d for d in a.datas if d is not None]

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Toastify',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Temporarily set to True to see errors
    icon=icon_path
) 