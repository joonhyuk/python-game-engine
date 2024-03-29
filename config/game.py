# from .engine import *
from config.engine import *
import arcade.key as keys
from dataclasses import dataclass

PROJECT_NAME = 'ESCAPE'
RELEASE_BUILD = False
SCREEN_TITLE = PROJECT_NAME

# Constants used to scale our sprites from their original size (arcade example - simple platformer)
DEFAULT_TILE_SIZE = 32
CHARACTER_SCALING = 1
TILE_SCALING = 0.5

DEFAULT_GRAVITY = 980
PLAYER_JUMP_SPEED = 20

@dataclass
class inputs:
    dpad_up = keys.UP
    dpad_down = keys.DOWN
    dpad_left = keys.LEFT
    dpad_right = keys.RIGHT
    
    act_interaction = keys.F
    
    mod_sprint = keys.MOD_SHIFT
    mod_walk = keys.MOD_CTRL

@dataclass
class settings(default_settings):
    screen_title = 'ESCAPE DEV'

CONFIG = settings()
