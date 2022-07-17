"""
framework wrapper for audio / video / control
might be coupled with base framwork(i.e. arcade, pygame, ...)
joonhyuk@me.com
"""
import os
from dataclasses import dataclass

import arcade
from arcade.experimental import Shadertoy, lights

from lib.foundation.base import *

def load_shader(file_path:str, target_window:arcade.Window, channels:list[arcade.Texture]):
    
    window_size = target_window.get_framebuffer_size()
    render_ratio = window_size[0] / target_window.get_size()[0] # need to be revised
    shadertoy = Shadertoy.create_from_file(window_size, file_path)
    
    if len(channels) > 4:
        raise 'ShaderToy channels limited to 4'
    
    for i in range(len(channels)):
        channels[i] = shadertoy.ctx.framebuffer(color_attachments=[shadertoy.ctx.texture(window_size, components=4)])
        setattr(shadertoy, f'channel_{i}', channels[i].color_attachments[0])
    
    return shadertoy


@dataclass
class appio:
    
    render_scale:float = 1.0
    mouse_input:Vector = Vector(0, 0)
    
    
    def _get_cursor_position(self) -> Vector:
        # return tuple(x * self.render_scale for x in self._cursor_position) 
        return self.mouse_input * self.render_scale
    
    def _set_cursor_position(self, position:Vector):
        return
    
    cursor_position:Vector = property(_get_cursor_position, _set_cursor_position)


class Window(arcade.Window):
    
    def on_show(self):
        appio.render_scale = self.get_framebuffer_size()[0] / self.get_size()[0]
        
    def on_key_press(self, symbol: int, modifiers: int):
        print('key input :', symbol)
        pass
    
    def on_update(self, delta_time: float):
        # return super().on_update(delta_time)
        # print(delta_time)
        pass
    
    def on_draw(self):
        pass
    
    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int):
        appio.mouse_input = Vector(x, y)
    
    @property
    def render_ratio(self):
        return self.get_framebuffer_size()[0] / self.get_size()[0]
    
    @property
    def cursor_position(self) -> Vector:
        return appio.mouse_input * appio.render_scale

class View(arcade.View):
    
    def __init__(self, window: Window = None):
        super().__init__(window)
        self.fade_out = 0.0
        self.fade_in = 0.0
        self.fade_alpha = 1

    def draw_tint(self, alpha = 0.0, color = (0, 0, 0)):
        arcade.draw_rectangle_filled(self.window.width / 2, self.window.height / 2,
                                     self.window.width, self.window.height,
                                     (*color, alpha * 255))
    
    def draw_contents(self):
        pass
    
    def on_draw(self):
        self.clear()
        self.draw_contents()
        if self.fade_in > 0 or self.fade_out > 0:
            # self.fade_alpha = finterp_to(self.fade_alpha, )
            self.draw_tint()
    
    def go_next(self, next_screen:arcade.View):
        if self.fade_out:
            pass
        
    def go_after_fade_out(self, next_screen:arcade.View):
        pass

class Sprite(arcade.Sprite):
    def __init__(self, 
                 filename: str = None, 
                 scale: float = 1, 
                 image_x: float = 0, image_y: float = 0, image_width: float = 0, image_height: float = 0, 
                 center_x: float = 0, center_y: float = 0, 
                 repeat_count_x: int = 1, repeat_count_y: int = 1, 
                 flipped_horizontally: bool = False, flipped_vertically: bool = False, flipped_diagonally: bool = False, 
                 hit_box_algorithm: str = "Simple", hit_box_detail: float = 4.5, 
                 texture: arcade.Texture = None, 
                 angle: float = 0):
        super().__init__(filename, scale, image_x, image_y, image_width, image_height, center_x, center_y, repeat_count_x, repeat_count_y, flipped_horizontally, flipped_vertically, flipped_diagonally, hit_box_algorithm, hit_box_detail, texture, angle)
        
class SpriteCircle(arcade.SpriteCircle):
    def __init__(self, 
                 radius: int = 16, 
                 color: arcade.Color = arcade.color.ALLOY_ORANGE, 
                 soft: bool = False):
        super().__init__(radius, color, soft)

class Objects:
    '''
    Singleton class for manage game objects(like actor) and SpriteList
    Has full list of every objects spawned, SpriteLists for drawing
    '''
    def __init__(self) -> None:
        self.layers:list[arcade.SpriteList] = []
        self.hidden_layers:list[arcade.SpriteList] = []
    
    def draw(self):
        for layer in self.layers:
            layer.draw()

class SoundBank:
    def __init__(self, path:str) -> None:
        self.path:str = path
        self.filenames:list = []
        self.sounds:dict[str, arcade.Sound] = {}
        self.mute:bool = False
        self.volume_master:float = 0.5
        print('hello-sound')
        self.load()
        
    def load(self, path:str = None):
        sfxpath = path or self.path
        try:
            self.filenames = os.listdir(get_path(sfxpath))
        except FileNotFoundError:
            print(f'no sound file found on "{sfxpath}"')
            return None
        
        if not self.filenames:
            print(f'no sound file found on "{sfxpath}"')
            return None
        
        for filename in self.filenames:
            namespaces = filename.split('.')
            if namespaces[1] in ('wav', 'ogg', 'mp3'):
                self.sounds[namespaces[0]] = arcade.Sound(get_path(sfxpath + filename))
        return self.sounds
    
    def play(self, name:str, volume:float = 0.2, repeat:int = 1) -> float:
        if self.mute: return None
        if name not in self.sounds:
            print(f'no sound file "{name}"')
            return None
        
        sound = self.sounds[name]
        # self.sounds[name].set_volume(volume)
        sound.play(volume)
        return sound.get_length()
    
    def set_mute(self, switch:bool = None):
        if switch is None: switch = not self.mute
        self.mute = switch
        return self.mute
    
    def set_volume_master(self, amount:float):
        self.volume_master = amount

if __name__ != "__main__":
    SOUND = SoundBank('resources/sfx/')
    print("include", __name__, ":", __file__)