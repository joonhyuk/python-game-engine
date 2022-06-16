import arcade
from enum import Enum
from lib.foundation.base import *

PROJECT_NAME = 'python arcade test'
DEFAULT_SCREEN_WIDTH = 1024
DEFAULT_SCREEN_HEIGHT = 768
DEFAULT_TILE_SIZE = 32
DEFAULT_FPS = 60
DEFAULT_UI_SCALE = 100

RESOURCE_PATH = 'resources/'

class settings(int, Enum):
    screen_width = DEFAULT_SCREEN_WIDTH
    screen_height = DEFAULT_SCREEN_HEIGHT
    tile_size = DEFAULT_TILE_SIZE
    fps = DEFAULT_FPS

class direction(EnumVector):
    up = Vector(0, 1)
    down = Vector(0, -1)
    left = Vector(1, 0)
    right = Vector(-1, 0)
    upleft = up + left
    upright = up + right
    downleft = down + left
    downright = down + right