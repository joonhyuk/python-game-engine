from json.encoder import ESCAPE
from config import *
from .units import *
import arcade

from lib.foundation import *
# from lib.foundation.engine import SoundBank

class Player(Actor2D):
    def __init__(self) -> None:
        super().__init__()
        
        self._init_snake_texture()
    
    def update(self):
        pass
    
    def _init_snake_texture(self):
        textures = arcade.load_spritesheet(get_path(RESOURCE_PATH + 'art/snake-graphics.png'), 64, 64, 5, 20)
        snake_textures = {'head':{(0, 1):textures[3],
                             (-1, 0):textures[4],
                             (1, 0):textures[8],
                             (0, -1):textures[9]},
                     'tail':{8:textures[13],
                             6:textures[14],
                             4:textures[18],
                             2:textures[19]},
                     'body':{(-1, -1):textures[0],
                             (1, -1):textures[2],
                             (-1, 1):textures[5],
                             (1, 1):textures[12],
                             (0, 1):textures[7],
                             (1, 0):textures[1],
                             (0, -1):textures[7],
                             (-1, 0):textures[1]}}
        self.direction = direction.right
        # self.body = Sprite(texture = snake_textures['head'][self.direction.value.values])
        self.body = SnakeHead(snake_textures['head'])
    
    

class SnakeHead(Sprite):
    def __init__(self, sprites):
        self.direction = direction.down
        self.sprites = sprites
        super().__init__(texture = self.sprites[self.direction.value.values])
    
    def update(self):
        print('update')
        return super().update()
    
    def on_update(self, delta_time: float = 1 / 60):
        print('on_update')
        return super().on_update(delta_time)
    
        
    

class GameManager(arcade.Window):
    """
    Main application class.
    """
    def __init__(self):

        # Call the parent class and set up the window
        super().__init__(DEFAULT_SCREEN_WIDTH, DEFAULT_SCREEN_HEIGHT, SCREEN_TITLE)
        
        self.scene = None
        self.characters = None
        self.player_sprite = None
        self.player_direction = None
        self.physics_engine = None
        
        arcade.set_background_color(arcade.csscolor.CORNFLOWER_BLUE)
        

    def setup(self):
        """Set up the game here. Call this function to restart the game."""
        
        # init camera, scene, player, world
        layer_options = {
            'World': {
                'use_spatial_hash': True,
            },
        }
        self.player = Player()
        self.ball = Actor2D()
        self.ball.set_body()
        self.characters = arcade.SpriteList()
        self.characters.append(self.player.body)
        self.scene = arcade.Scene()
        self.scene.add_sprite_list('Player')
        self.scene.add_sprite_list('Ball')
        self.scene.add_sprite_list('World')
        
        self.player.body.position = Vector(64,64)
        self.ball.position = Vector(256,256)
        # self.player_list.append(self.player_sprite)
        self.scene.add_sprite('Player', self.player.body)
        self.scene.add_sprite('Ball', self.ball.body)
        
        self.physics_engine = arcade.PhysicsEngineSimple(self.ball.body, self.scene.get_sprite_list('World'))
        
    def on_draw(self):
        """Render the screen."""
        self.clear()
        # self.player_list.draw()
        self.scene.draw()
        
        # Code to draw the screen goes here
    
    def on_key_press(self, key, modifiers):
        """Called whenever a key is pressed."""
        if key == arcade.key.UP:
            self.player.body.change_y = 10
        
        if key in (arcade.key.Q, arcade.key.ESCAPE):
            arcade.exit()

    def on_key_release(self, key, modifiers):
        """Called when the user releases a key."""

    def on_update(self, delta_time):
        """Movement and game logic"""
        CLOCK.delta_time = delta_time   # not using custom clock tick and delta_time
        
        # PLAYER_MOVEMENT_SPEED * 
        # self.player_sprite.change_y = 10
        self.characters.on_update(delta_time)
        self.physics_engine.update()
    
    def on_tile_tick(self):
        print('tile tick')
    
