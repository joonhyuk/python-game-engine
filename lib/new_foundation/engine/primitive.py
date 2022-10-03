from __future__ import annotations

import PIL.Image
import PIL.ImageOps
import PIL.ImageDraw

import arcade
import arcade.key as keys
import arcade.color as colors

from ..physics import *
from .object import *


class GLTexture(arcade.Texture):
    pass


class Sprite(GameObject, arcade.Sprite):
    
    # __slots__ = ('_initial_scale', '_relative_scale')
    
    def __init__(self, 
                 filename: str = None, 
                 scale: float = 1, 
                 image_x: float = 0, image_y: float = 0, image_width: float = 0, image_height: float = 0, 
                 center_x: float = 0, center_y: float = 0, 
                 repeat_count_x: int = 1, repeat_count_y: int = 1, 
                 flipped_horizontally: bool = False, flipped_vertically: bool = False, flipped_diagonally: bool = False, 
                 hit_box_algorithm: str = "Detailed", hit_box_detail: float = 4.5, 
                 texture: arcade.Texture = None, 
                 angle: float = 0,
                 position: Vector = None
                 ):
        GameObject.__init__(self)
        arcade.Sprite.__init__(self, filename, scale, image_x, image_y, image_width, image_height, center_x, center_y, repeat_count_x, repeat_count_y, flipped_horizontally, flipped_vertically, flipped_diagonally, hit_box_algorithm, hit_box_detail, texture, angle)
        self._initial_scale = scale
        self._relative_scale = 1.0
        if position is not None: self.position = position

    def scheduled_remove_from_sprite_lists(self, dt):
        # print('REMOVING!')
        return super().remove_from_sprite_lists()
    
    def _get_relative_scale(self) -> float:
        return self._relative_scale
    
    def _set_relative_scale(self, scale:float):
        self._relative_scale = scale
        self.scale = self._initial_scale * self._relative_scale
        # print(self, 'SCALE :::', self.scale)
    
    relative_scale = property(_get_relative_scale, _set_relative_scale)
    
    def _get_hidden(self):
        return not self.visible
    
    def _set_hidden(self, switch:bool = None):
        if switch is None: switch = self.visible
        self.visible = not switch
    
    hidden:bool = property(_get_hidden, _set_hidden)
    
    
class SpriteCircle(Sprite):
    ''' If ellipse, make sure to set physics_shape as poly '''
    # __slots__ = ['owner', 'texture', '_points']   ### sprite not works if set with slots.
    
    def __init__(self, 
                 radius: Union[int, Vector], 
                 color: arcade.Color = colors.ALIZARIN_CRIMSON, 
                 nose: bool = True):
        super().__init__()
        if isinstance(radius, int):
            radius = Vector.diagonal(radius)
        diameter = radius * 2

        # determine the texture's cache name
        # if soft:
            # cache_name = arcade.texture._build_cache_name("circle_texture_soft", diameter, color[0], color[1], color[2])
        # else:
        cache_name = arcade.texture._build_cache_name("circle_texture", diameter, color[0], color[1], color[2], 255, 0)

        # use the named texture if it was already made
        if cache_name in arcade.texture.load_texture.texture_cache:  # type: ignore
            texture = arcade.texture.load_texture.texture_cache[cache_name]  # type: ignore

        # generate the texture if it's not in the cache
        else:
            img = PIL.Image.new('RGBA', diameter, (0, 0, 0, 0))
            draw = PIL.ImageDraw.Draw(img)
            
            point_b:Vector = diameter - Vector(1, 1)
            
            draw.ellipse((0, 0, *point_b), fill = color)
            if nose: draw.line((*radius, point_b.x, radius.y), width = 1, fill = (0, 0, 0, 255))
            texture = GLTexture(cache_name, img)
            # if soft:
            #     texture = arcade.texture.make_soft_circle_texture(diameter, color, name=cache_name)
            # else:
            #     texture = arcade.texture.make_circle_texture(diameter, color, name=cache_name)

            arcade.texture.load_texture.texture_cache[cache_name] = texture  # type: ignore

        # apply results to the new sprite
        self.texture = texture
        self._points = self.texture.hit_box_points


class Camera(arcade.Camera):
    
    def __init__(self, viewport_width: int = 0, viewport_height: int = 0, window: Optional["arcade.Window"] = None, 
                 max_lag_distance:float = None,
                 ):
        if not viewport_width or not viewport_height:
            viewport_width, viewport_height = CONFIG.screen_size.x, CONFIG.screen_size.y
        super().__init__(viewport_width, viewport_height, window)
        self.max_lag_distance:float = max_lag_distance
    
    def update(self):
        # last_tick_pos = self.position
        super().update()
        
        if self.max_lag_distance:
            distv = self.position - self.goal_position
            if distv.mag > self.max_lag_distance:
                # print(distv.mag)
                self.position = self.goal_position + distv.limit(self.max_lag_distance)
                # self.position.lerp(self.goal_position + distv.limit(self.max_lag_distance * 0.75), 0.9)


class Layer(arcade.SpriteList):
    
    def add(self, obj):
        raise Exception('this object should not be called')
    
    def remove(self, obj):
        raise Exception('this object should not be called')