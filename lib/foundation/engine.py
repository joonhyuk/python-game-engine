"""
framework wrapper for audio / video / control
might be coupled with base framwork(i.e. arcade, pygame, ...)
joonhyuk@me.com
"""
from __future__ import annotations

import os
from dataclasses import dataclass

import arcade
from arcade.experimental import Shadertoy, lights

from lib.foundation.base import *
from config.game import *

def load_shader(file_path:str, target_window:arcade.Window, channels:list[arcade.Texture]):
    
    window_size = target_window.get_framebuffer_size()
    # render_ratio = window_size[0] / target_window.get_size()[0] # need to be revised
    shadertoy = Shadertoy.create_from_file(window_size, file_path)
    
    if len(channels) > 4:
        raise 'ShaderToy channels limited to 4'
    
    for i in range(len(channels)):
        channels[i] = shadertoy.ctx.framebuffer(color_attachments=[shadertoy.ctx.texture(window_size, components=4)])
        setattr(shadertoy, f'channel_{i}', channels[i].color_attachments[0])
    
    return shadertoy

def debug_draw_line(start:Vector = Vector(), end:Vector = Vector(), color = arcade.color.WHITE, thickness = 1):
    if not CONFIG.debug_draw: return False
    return arcade.draw_line(start.x, start.y, end.x, end.y, color, thickness)

def debug_draw_circle(center:Vector = Vector(), 
                      radius:float = DEFAULT_TILE_SIZE, 
                      line_color = arcade.color.WHITE, 
                      line_thickness = 1, 
                      fill_color = None):
    if not CONFIG.debug_draw: return False
    if fill_color is not None: arcade.draw_circle_filled(center.x, center.y, radius - line_thickness, fill_color)
    return arcade.draw_circle_outline(center.x, center.y, radius, line_color, line_thickness)

def debug_draw_marker(position:Vector = Vector(), 
                      radius:float = DEFAULT_TILE_SIZE, 
                      color = arcade.color.RED):
    if not CONFIG.debug_draw: return False
    debug_draw_circle(position, radius, color)
    corner_point = Vector.diagonal(radius)
    debug_draw_line(position, position + corner_point, color)
    debug_draw_line(position, position - corner_point, color)
    debug_draw_line(position, position + corner_point.rotate(90), color)
    debug_draw_line(position, position + corner_point.rotate(-90), color)
    

@dataclass
class Environment:
    ''' I/O for game
    디스플레이 정보
        - 렌더링 배율
    현재 뷰포트 중앙의 절대 좌표
    게임패드 입력 raw
    마우스 입력 raw
        - 뷰포트 내 상대좌표
        - 월드상의 절대 좌표
    '''
    window:Window = None
    abs_screen_center:Vector = Vector()
    render_scale:float = 1.0
    mouse_input:Vector = Vector()
    gamepad:arcade.joysticks.Joystick = None
    key = arcade.key
    key_inputs = []
    
    def __init__(self) -> None:
        self.gamepad = self.get_input_device()
    
    def get_input_device(self, id:int = 0):
        joysticks = arcade.get_joysticks()
        if joysticks:
            gamepad = joysticks[id]
            gamepad.open()
            gamepad.push_handlers(self)
            print('Gamepad attached')
            return gamepad
        return None
    
    def set_screen(self, window:Window):
        self.window = window
        self.render_scale = window.get_framebuffer_size()[0] / window.get_size()[0]
    
    def on_key_presse(self, key:int, modifiers:int):
        pass
    
    @property
    def lstick(self) -> Vector:
        ''' returns raw info of left stick (-1, -1) ~ (1, 1) '''
        if not self.gamepad: return None
        x = map_range_abs(self.gamepad.x, CONFIG.gamepad_deadzone_lstick, 1, 0, 1, True)
        y = map_range_abs(self.gamepad.y, CONFIG.gamepad_deadzone_lstick, 1, 0, 1, True) * -1
        return Vector(x, y)
    
    @property
    def rstick(self) -> Vector:
        ''' returns raw info of left stick (-1, -1) ~ (1, 1) '''
        if not self.gamepad: return None
        x = map_range_abs(self.gamepad.rx, CONFIG.gamepad_deadzone_rstick, 1, 0, 1, True)
        y = map_range_abs(self.gamepad.ry, CONFIG.gamepad_deadzone_rstick, 1, 0, 1, True) * -1
        return Vector(x, y)
    
    def _get_move_input(self):
        if self.gamepad:
            return self.lstick
        else:
            return self.window.lstick_vector.clamp_length(1) * (0.5 if self.window.lctrl_applied else 1)

    move_input:Vector = property(_get_move_input)
    ''' returns movement direction vector (-1, -1) ~ (1, 1) '''
    
    def _get_direction_input(self):
        if self.gamepad:
            if self.rstick.length > 0.25:
                return (self.rstick.unit * CONFIG.screen_size.y / 2 + CONFIG.screen_size) * self.render_scale
            return Vector()
        else:
            return self.cursor_position
    
    direction_input:Vector = property(_get_direction_input)
    ''' returns relative target point '''
    
    def _get_cursor_position(self) -> Vector:
        # if not self.mouse_input: return Vector()
        return self.mouse_input * self.render_scale
    
    cursor_position:Vector = property(_get_cursor_position)
    
    def _get_abs_cursor_position(self) -> Vector:
        return self.mouse_input + self.abs_screen_center - CONFIG.screen_size / 2
        # return self.mouse_input + self.window.current_camera.position
    
    abs_cursor_position:Vector = property(_get_abs_cursor_position)
    ''' get absolute position in world, pointed by mouse cursor '''

ENV = Environment()


class Window(arcade.Window):
    
    lstick_vector = Vector()
    rstick_vector = Vector()
    joystick:arcade.joysticks.Joystick = None
    lshift_applied = False
    lctrl_applied = False
    currnet_camera:arcade.Camera = None
    
    def on_show(self):
        ENV.set_screen(self)
        # self.direction_input = Vector()
        # self.get_input_device()
        if self.joystick: self.set_mouse_visible(False)
        
    def on_key_press(self, key: int, modifiers: int):
        print('[window]key input')
        # self.lstick_vector = Vector()
        ENV.key_inputs.append(key)
        if key in (arcade.key.W, arcade.key.UP): self.lstick_vector += (0,1)
        if key in (arcade.key.S, arcade.key.DOWN): self.lstick_vector += (0,-1)
        if key in (arcade.key.A, arcade.key.LEFT): self.lstick_vector += (-1,0)
        if key in (arcade.key.D, arcade.key.RIGHT): self.lstick_vector += (1,0)
        if key == arcade.key.LSHIFT: self.lshift_applied = True
        if key == arcade.key.LCTRL: self.lctrl_applied = True
        
        if key == arcade.key.F2: CONFIG.debug_draw = not CONFIG.debug_draw
        
    def on_key_release(self, key: int, modifiers: int):
        ENV.key_inputs.remove(key)
        if key in (arcade.key.W, arcade.key.UP): self.lstick_vector -= (0,1)
        if key in (arcade.key.S, arcade.key.DOWN): self.lstick_vector -= (0,-1)
        if key in (arcade.key.A, arcade.key.LEFT): self.lstick_vector -= (-1,0)
        if key in (arcade.key.D, arcade.key.RIGHT): self.lstick_vector -= (1,0)
        if key == arcade.key.LSHIFT: self.lshift_applied = False
        if key == arcade.key.LCTRL: self.lctrl_applied = False
        
    def on_update(self, delta_time: float):
        # return super().on_update(delta_time)

        # if self.joystick:
        #     x = map_range_abs(self.joystick.x, 0.1, 1, 0, 1, True)
        #     y = map_range_abs(self.joystick.y, 0.1, 1, 0, 1, True) * -1
        #     self.move_input = Vector(x, y).clamp_length()
        #     if abs(self.joystick.rx) > 0.25 or abs(self.joystick.ry) > 0.25:
        #         rx = map_range_abs(self.joystick.rx, 0.25, 1, 0, 300, True)
        #         ry = map_range_abs(self.joystick.ry, 0.25, 1, 0, 300, True) * -1
        #         ar = Vector(-1 * self.joystick.rx, -1 * self.joystick.ry).argument()
        #         rv = Vector(0, 300).rotate(ar)
        #         self.direction_input = (rv + Vector(self.size) / 2) * ENV.render_scale
        # else:
        #     self.move_input = self.lstick_vector.clamp_length(1) * (0.5 if self.lctrl_applied else 1)
        #     self.direction_input = ENV.mouse_input * ENV.render_scale
        #     pass
        # print(ENV.get_current_window())
        CLOCK.tick()
        
    def on_draw(self):
        pass
    
    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int):
        ENV.mouse_input = Vector(x, y)
    
    # def get_input_device(self):
    #     joysticks = arcade.get_joysticks()
    #     if joysticks:
    #         self.joystick = joysticks[0]
    #         self.joystick.open()
    #         self.joystick.push_handlers(self)
    #         print('Gamepad attached')
    #     else: self.joystick = None
    
    @property
    def render_ratio(self):
        return self.get_framebuffer_size()[0] / self.get_size()[0]
    
    @property
    def cursor_position(self) -> Vector:
        return ENV.mouse_input * ENV.render_scale


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


class Layer(arcade.SpriteList):
    pass


class Camera(arcade.Camera):
    pass


class GLTexture(arcade.Texture):
    pass


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
        print('SOUND initialized')
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
    print("include", __name__, ":", __file__)
    SOUND = SoundBank(SFX_PATH)