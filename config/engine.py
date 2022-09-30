import math
from dataclasses import dataclass
from enum import Enum, IntEnum, auto, IntFlag
from lib.foundation.base import *
from lib.foundation.vector import Vector

PROJECT_NAME = 'mash python game engine'
SCREEN_TITLE = PROJECT_NAME

DEFAULT_SCREEN_WIDTH = 1024
DEFAULT_SCREEN_HEIGHT = 768
DEFAULT_TILE_SIZE = 32
DEFAULT_FPS = 60
DEFAULT_UI_SCALE = 100

RESOURCE_PATH = 'resources/'
IMG_PATH = RESOURCE_PATH + 'art/'
SFX_PATH = RESOURCE_PATH + 'sfx/'

DEFAULT_PAWN_MOVE_SPEEDS = (100, 250, 400)
GAMEZONE_POS_MIN = -65536
GAMEZONE_POS_MAX = 65536


@dataclass
class default_settings:
    screen_title = SCREEN_TITLE
    ''' default setting of mutable config variables '''
    screen_size = Vector(DEFAULT_SCREEN_WIDTH, DEFAULT_SCREEN_HEIGHT)
    ''' current app resolution '''
    fog_of_war = True
    ''' draw shadow switch '''
    terminal_speed = 60000 // DEFAULT_FPS
    ''' maximum speed possible '''
    gamepad_deadzone_lstick = 0.1
    gamepad_deadzone_rstick = 0.1
    
    debug_draw = True
    directional_speed = {0:1.0, 30:1.0, 90:0.75, 120:0.75, 180:0.5}
    ''' directional speed multiplier '''
    
    debug_f_keys = [False] * 13
    ''' 0: tilde, 1 ~ 12: F1 ~ F12 '''
    
    walkable_angle = 45


@dataclass
class vectors:
    ''' prepare basic vectors '''
    zero = Vector()
    
    right = Vector(1,0)
    left = Vector(-1,0)
    up = Vector(0,1)
    down = Vector(0,-1)
    
    forward = right
    backward = left
    rightside = down
    leftside = up
    
    upperright = (up + right).unit
    lowerright = (down + right).unit
    upperleft = (up + left).unit
    lowerleft = (down + left).unit
    
    walkable_limit = right.rotate(default_settings.walkable_angle)


class collision(IntFlag):
    ''' collision types '''
    none = 0
    default = auto()
    character = auto()
    enemy = auto()
    wall = auto()
    debris = auto()
    projectile = auto()
    test = wall | character
    

CONFIG = default_settings()
