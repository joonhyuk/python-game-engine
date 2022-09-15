"""
build script for windows, linux

Usage:
    just press F5
"""
import PyInstaller.__main__
import sys

os_id = sys.platform

icon_file_ext = {'darwin' : 'icns', 
                 'win32' : 'ico'
                 }.get(os_id, 'png')
add_path_separator = {'win32' : ';'
                      }.get(os_id, ':')

PyInstaller.__main__.run([
    'test-physics.py',
    '--onefile',
    '--windowed',
    '--icon=app-assets/icons/snake.' + icon_file_ext,
    '--add-binary=resources' + add_path_separator + 'resources',
    '--add-data=data' + add_path_separator + 'data'
])