from __future__ import annotations

import PIL.Image
import PIL.ImageOps
import PIL.ImageDraw

import arcade
import arcade.key as keys
import arcade.color as colors

from lib.foundation.physics import *
from .object import *
# from .body import *


class GLTexture(arcade.Texture):
    pass


class Sprite(GameObject, arcade.Sprite):
    
    __slots__ = ('_initial_scale', '_relative_scale')
    
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
                 ):
        arcade.Sprite().__init__(filename, scale, image_x, image_y, image_width, image_height, center_x, center_y, repeat_count_x, repeat_count_y, flipped_horizontally, flipped_vertically, flipped_diagonally, hit_box_algorithm, hit_box_detail, texture, angle)
        self._initial_scale = scale
        self._relative_scale = 1.0

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


class ObjectLayer(arcade.SpriteList):
    """ extended spritelist with actor, body """
    def __init__(self, 
                 physics_instance:PhysicsEngine = None,
                 use_spatial_hash=None, spatial_hash_cell_size=128, is_static=False, atlas: arcade.TextureAtlas = None, capacity: int = 100, lazy: bool = False, visible: bool = True):
        super().__init__(use_spatial_hash, spatial_hash_cell_size, is_static, atlas, capacity, lazy, visible)
        self._physics_instance = physics_instance
    
    def get_obj_tree(self, obj):
        actor:GameObject = None
        body:Body = None
        sprites:Sprite = None
        
        if isinstance(obj, (Sprite, SpriteCircle)):
            sprites = [obj, ]
        
        elif isinstance(obj, (Body, )):
            body = obj
            sprites = body.get_members(Sprite)    ### could be list
        
        elif isinstance(obj, GameObject):
            actor = obj
            body = obj.get_members(Body)[0]
            sprites = body.get_members(Sprite)    ### could be list
        
        else: raise Exception('ObjectLayer only accept Sprite, Body, Actor')
        
        return actor, body, sprites
        
    def add(self, obj:Union[GameObject, Body, Sprite, SpriteCircle]):
        
        actor, body, sprite = self.get_obj_tree(obj)
        
        if sprite:
            try:
                self.extend(sprite)
            except ValueError:
                pass
        
        if self._physics_instance:
            if body:
                if body.physics:
                    self._add_to_physics(sprite, body.physics)
                    # self._physics_instance.add_physics_object(sprite, body.physics)  ### add sprite-physics pair to engine for refering
                    # self._physics_instance.add_to_space(sprite)      ### add physics to space
    
    def _add_to_physics(self, sprite:Sprite, physics:PhysicsObject):
        self.physics_instance.add_physics_object(sprite, physics)
        self.physics_instance.add_to_space(sprite)
    
    def remove(self, obj:Union[GameObject, Body, Sprite, SpriteCircle]):
        
        actor, body, sprite = self.get_obj_tree(obj)
        
        ''' 
        Because arcade spritelist remove method automatically remove body from physics,
        we don't need it
        
        if body:
           if body.physics:
               self.physics_instance.remove_sprite(sprite)
        '''
        return super().remove(sprite)
    
    def step(self, delta_time:float = 1/60, sync:bool = True):
        ''' Don't use it usually. For better performance, call directly from physics instance '''
        self._physics_instance.step(delta_time=delta_time, resync_objects=sync)
    
    def _get_physics(self):
        return self._physics_instance
    
    def _set_physics(self, physics_instance):
        #TODO : add feature of registreing sprites to another physics instance
        
        self._physics_instance = physics_instance
    
    physics_instance:PhysicsEngine = property(_get_physics, _set_physics)