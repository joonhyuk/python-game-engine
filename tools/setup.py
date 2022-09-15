"""
This is a setup.py script generated by py2applet

Usage:
    python tools/setup.py py2app
"""

from setuptools import setup

APP = ['PythonByte.py']
DATA_FILES = []
OPTIONS = {'iconfile': 'app-assets/icons/snake.icns', 'resources': ['resources', 'data']}

setup(
    name='PythonByte', 
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
