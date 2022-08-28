from config import *
from .units import *
import arcade

from lib.foundation import *
# from lib.foundation.engine import SoundBank


class Actor2D(MObject):
    ''' top-down based actor object which has body, position, rotation, collision '''
    def __init__(self, 
                 body:Sprite = None, 
                 **kwargs) -> None:
        super().__init__(**kwargs)
        self.body:Sprite = None
        self.body_movement:Sprite = None
        ''' actual body to be rendered. (i.e. pygame.Surface, arcade.Sprite, ...) '''
        # self.attachments:list[Sprite] = []
        self.size = get_from_dict(kwargs, 'size', DEFAULT_TILE_SIZE)
        
        self.set_body(body)
        self.visibility = get_from_dict(kwargs, 'visibility', True)
        ''' diameter '''
        self.tick_group = []
        ''' tick group '''
    
    def set_body(self, body:Sprite = None, body_movement:Sprite = None) -> None:
        if self.body: self.remove_body()
        self.body = body or SpriteCircle(self.size // 2)
        self.body_movement = self.get_physics_body()
        
        self.body.owner = self
    
    def get_physics_body(self) -> Sprite:
        '''
        could be override without super()
        
        like, return Capsule(self.size // 2)
        '''
        return None
        
    def spawn(self, 
              position:Vector = Vector(), 
              angle:float = None, 
              draw_layer:ObjectLayer = None, 
              movable_layer:ObjectLayer = None,
              lifetime=0) -> None:
        '''
        set position, rotation, register body and component
        '''
        self.position = position
        self.angle = angle
        # if sprite_list:
        self.register_body(draw_layer, movable_layer)
        self.register_components()
        return super().spawn(lifetime)
    
    def tick(self, delta_time:float = None) -> bool:
        if delta_time is None: delta_time = ENV.delta_time
        if not super().tick(delta_time): return False
        if self.tick_group:
            for ticker in self.tick_group:
                ticker.tick(delta_time)
                # print('character_tick', delta_time)
        return True
    
    def destroy(self) -> bool:
        if self.body:
            self.remove_body()
            self.body = None
        return super().destroy()
    
    # def add_attachment(self, )
    
    def _get_position(self) -> Vector:
        if not self.body: return False
        # if self.body_movement:
        #     return Vector(self.body_movement.position)
        return Vector(self.body.position)
    
    def _set_position(self, new_position:Vector = Vector(0., 0.)) -> bool:
        if not self.body: return False
        if self.body_movement:
            self.body_movement.position = new_position
            self.body.position = new_position
        else:
            self.body.position = new_position
        return True
    
    # @classmethod
    def check_body(f):
        @functools.wraps(f)
        def wrapper(self, *args, **kwargs):
            if not self.body: return False
            return f(self, *args, **kwargs)
        return wrapper

    
    @check_body
    def _get_rotation(self) -> float:
        if self.body_movement:
            return self.body_movement.angle
        return self.body.angle
    
    @check_body
    def _set_rotation(self, rotation:float = 0.0) -> bool:
        if self.body_movement:
            self.body_movement.angle = rotation
            self.body.angle = self.body_movement.angle
        else:
            self.body.angle = rotation
        return True
    
    @check_body
    def _get_visibility(self) -> bool:
        return self.body.visible
    
    @check_body
    def _set_visibility(self, switch:bool = None):
        if switch is None: switch = not switch
        self.body.visible = switch
        
    # @check_body
    def _get_velocity(self) -> Vector:
        if self.body_movement:
            return Vector(self.body_movement.velocity)
        return Vector(self.body.velocity)
    
    # @check_body
    def _set_velocity(self, velocity:Vector = Vector()):
        if self.body_movement:
            self.body_movement.velocity = list(velocity)
            # self.body.velocity = list(velocity)
            # self.body.velocity = self.body_movement.velocity
            self.body.position = self.body_movement.position    # 좋지 않음. 별도의 바디 컴포넌트를 만들어 붙여야겠음.
            # print(self.body.velocity)
        else:
            self.body.velocity = list(velocity)
        
    def register_components(self):
        for k in self.__dict__:
            if isinstance(self.__dict__[k], (ActorComponent, )): 
                if isinstance(self.__dict__[k], ActorComponent):
                    self.__dict__[k].owner = self
                    ''' for components that have owner '''
                if hasattr(self.__dict__[k], 'tick'):
                    self.tick_group.append(self.__dict__[k])
                    ''' for components that have tick '''
    
    @check_body
    def register_body(self, sprite_list:ObjectLayer, movable_list:ObjectLayer):
        self.body.collides_with_radius = True
        if self.body_movement is None:
            movable_list.append(self.body)
        else:
            movable_list.append(self.body_movement)
        return sprite_list.append(self.body)
    
    @check_body
    def remove_body(self):
        if self.body_movement:
            self.body_movement.remove_from_sprite_lists()
        return self.body.remove_from_sprite_lists()
    
    visibility:bool = property(_get_visibility, _set_visibility)
    position:Vector = property(_get_position, _set_position)
    angle:float = property(_get_rotation, _set_rotation)
    velocity:Vector = property(_get_velocity, _set_velocity)
    
    @property
    @check_body
    def forward_vector(self):
        return Vector.directional(self.angle)
    
    @property
    def rel_position(self) -> Vector:
        ''' relative position in viewport '''
        return self.position - ENV.abs_screen_center + CONFIG.screen_size / 2
    

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
        self.direction = vectors.right
        # self.body = Sprite(texture = snake_textures['head'][self.direction.value.values])
        self.body = SnakeHead(snake_textures['head'])
    
    

class SnakeHead(Sprite):
    def __init__(self, sprites):
        self.direction = vectors.down
        self.sprites = sprites
        super().__init__(texture = self.sprites[self.direction.value.values])
    
    def update(self):
        # print(CLOCK.delta_time)
        return super().update()
    
    def on_update(self, delta_time: float = 1 / 60):
        # print('on_update')
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
            CLOCK.reserve_exec(5, self.on_tile_tick)
            self.player.body.change_y = 10
        
        if key in (arcade.key.Q, arcade.key.ESCAPE):
            CLOCK.reserve_cancel()
            arcade.exit()

    def on_key_release(self, key, modifiers):
        """Called when the user releases a key."""

    def on_update(self, delta_time):
        """Movement and game logic"""
        CLOCK.delta_time = delta_time   # not using custom clock tick and delta_time
        
        # PLAYER_MOVEMENT_SPEED * 
        # self.player_sprite.change_y = 10
        self.characters.update()
        self.physics_engine.update()
    
    def on_tile_tick(self):
        print('tile tick')
    
