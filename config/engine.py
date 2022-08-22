# import arcade
from dataclasses import dataclass
from enum import Enum, IntEnum, auto, IntFlag
from lib.foundation.base import *


PROJECT_NAME = 'mash python game engine'
SCREEN_TITLE = PROJECT_NAME + 'dev'

DEFAULT_SCREEN_WIDTH = 1024
DEFAULT_SCREEN_HEIGHT = 768
DEFAULT_TILE_SIZE = 32
DEFAULT_FPS = 60
DEFAULT_UI_SCALE = 100

RESOURCE_PATH = 'resources/'
IMG_PATH = RESOURCE_PATH + 'art/'
SFX_PATH = RESOURCE_PATH + 'sfx/'


@dataclass
class default_settings:
    ''' default setting of mutable config variables '''
    screen_size = Vector(DEFAULT_SCREEN_WIDTH, DEFAULT_SCREEN_HEIGHT)
    '''  '''
    fog_of_war = True
    ''' draw shadow switch '''
    terminal_speed = 60000 // DEFAULT_FPS
    ''' maximum speed possible '''
    gamepad_deadzone_lstick = 0.1
    gamepad_deadzone_rstick = 0.1
    
    debug_draw = True
    directional_speed = {0:1.0, 30:1.0, 90:0.75, 120:0.75, 180:0.5}
    ''' directional speed multiplier '''

@dataclass
class vectors:
    ''' prepare basic vectors '''
    zero = Vector()
    right = Vector(1,0)
    left = Vector(-1,0)
    up = Vector(0,1)
    down = Vector(0,-1)
    
    upright = (up + right).unit

# class direction(EnumVector):
#     zero = Vector()
#     up = Vector(0, 1)
#     down = Vector(0, -1)
#     left = Vector(1, 0)
#     right = Vector(-1, 0)
#     upleft = (up + left).normalize()
#     upright = (up + right).normalize()
#     downleft = (down + left).normalize()
#     downright = (down + right).normalize()

CONFIG = default_settings()

class collision(IntFlag):
    ''' collision types '''
    default = auto()
    character = auto()
    enemy = auto()
    wall = auto()
    debris = auto()
    projectile = auto()
    test = wall | character
    
    