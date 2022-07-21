from .engine import *

RELEASE_BUILD = False
SCREEN_TITLE = PROJECT_NAME + 'dev'
IMG_PATH = RESOURCE_PATH + 'art/'
SFX_PATH = RESOURCE_PATH + 'sfx/'

# Constants used to scale our sprites from their original size (arcade example - simple platformer)
CHARACTER_SCALING = 1
TILE_SCALING = 0.5
# Movement speed of player, in pixels per frame
PLAYER_MOVEMENT_SPEED = 2

GRAVITY = 1
PLAYER_JUMP_SPEED = 20