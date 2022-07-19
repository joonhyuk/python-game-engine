import arcade
from enum import Enum
from lib.foundation.base import *

from dataclasses import dataclass

PROJECT_NAME = 'python arcade test'
DEFAULT_SCREEN_WIDTH = 1024
DEFAULT_SCREEN_HEIGHT = 768
DEFAULT_TILE_SIZE = 32
DEFAULT_FPS = 60
DEFAULT_UI_SCALE = 100

RESOURCE_PATH = 'resources/'

@dataclass
class default_settings:
    screen_size = Vector(DEFAULT_SCREEN_WIDTH, DEFAULT_SCREEN_HEIGHT)
    '''  '''
    fog_of_war = True
    ''' draw shadow switch '''
    terminal_speed_per_tick = 4000 // DEFAULT_FPS
    ''' maximum speed possible '''
    
class direction(EnumVector):
    up = Vector(0, 1)
    down = Vector(0, -1)
    left = Vector(1, 0)
    right = Vector(-1, 0)
    upleft = (up + left).normalize()
    upright = (up + right).normalize()
    downleft = (down + left).normalize()
    downright = (down + right).normalize()

CONFIG = default_settings()
