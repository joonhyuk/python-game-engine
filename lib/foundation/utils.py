'''
utils coupled with arcade, pymunk, pyglet, etc

'''
import functools

import arcade
from arcade.experimental import Shadertoy, lights
from lib.foundation.base import *
from config.engine import *
from pyglet.clock import schedule, schedule_once, schedule_interval, schedule_interval_soft, unschedule
from pyglet.clock import _default as pyglet_clock


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

def debug_draw_segment(start:Vector = vectors.zero, end:Vector = vectors.right, color = arcade.color.WHITE, thickness = 1):
    if not CONFIG.debug_draw: return False
    return arcade.draw_line(start.x, start.y, end.x, end.y, color, thickness)

def debug_draw_circle(center:Vector = vectors.zero, 
                      radius:float = DEFAULT_TILE_SIZE, 
                      line_color = arcade.color.WHITE, 
                      line_thickness = 1, 
                      fill_color = None):
    if not CONFIG.debug_draw: return False
    if fill_color is not None: arcade.draw_circle_filled(center.x, center.y, radius - line_thickness, fill_color)
    return arcade.draw_circle_outline(*center, radius, line_color, line_thickness)

def debug_draw_poly(center:Vector = vectors.zero,
                    points:arcade.PointList = None,
                    line_color = arcade.color.WHITE, 
                    line_thickness = 1, 
                    fill_color = None
                    ):
    if not CONFIG.debug_draw: return False
    if not points: return False
    
    new_poly = []
    for point in points:
        new_poly.append(point + center)
    
    if fill_color is not None: return arcade.draw_polygon_filled(new_poly, fill_color)
    return arcade.draw_polygon_outline(new_poly, line_color, line_thickness)

def debug_draw_marker(position:Vector = Vector(), 
                      radius:float = DEFAULT_TILE_SIZE, 
                      color = arcade.color.RED):
    if not CONFIG.debug_draw: return False
    debug_draw_circle(position, radius, color)
    corner_point = Vector.diagonal(radius)
    debug_draw_segment(position, position + corner_point, color)
    debug_draw_segment(position, position - corner_point, color)
    debug_draw_segment(position, position + corner_point.rotate(90), color)
    debug_draw_segment(position, position + corner_point.rotate(-90), color)

def add_sprite_timeout(sprite:arcade.Sprite, location:Vector, layer:arcade.SpriteList, timeout:float = 0.0):
    sprite.position = location
    layer.append(sprite)
    
    schedule_once(sprite.scheduled_remove_from_sprite_lists, timeout)

scheduled_functions = {}

def delay_run(delay:float, func, *args, **kwargs):
    if not isinstance(delay, (float, int)): return False
    if delay <= 0: return func(*args, **kwargs)
    
    ### 아래처럼 래핑하면 인스턴스 메소드의 레퍼런스로 참조되는게 아닌, 클래스의 메소드로만 참조된다.
    @functools.wraps(func)
    def _wrapper(dt, func=func, *args, **kwargs):
        return func(*args, **kwargs)
    
    scheduled_functions[func] = _wrapper
    
    return schedule_once(_wrapper, delay, *args, **kwargs)

def delay_cancel(func):
    unschedule(scheduled_functions[func])
    scheduled_functions.pop(func, None)
    
def is_scheduled_item(func):
    for it in pyglet_clock._schedule_interval_items:
        if func == it.func:
            return True
    return False

def tick_for(tick_func, duration:float, interval:float = 1/DEFAULT_FPS, *args, **kwargs):
    ''' run tick func immediately 
    
    tick function should have delta_time as first arg like, tick(self, delta_time)
    '''
    # print(*args)
    if is_scheduled_item(tick_func):
        print('-------------tick-function-unscheduled', tick_func)
        unschedule(tick_func)
        print('-------------delayed-unschedule-unscheduled', delayed_unschedule)
        unschedule(delayed_unschedule, tick_func)
    
    print('+++++++++++++++++++++schedule', tick_func)
    schedule_interval(tick_func, interval, *args, **kwargs)
    print('+++++++++++++++++++++schedule', delayed_unschedule)
    schedule_once(delayed_unschedule, duration, tick_func)

def delayed_unschedule(dt, func):
    unschedule(func)



def delayed_func(dt, func, *args, **kwargs):
    return func(*args, **kwargs)

def reserve_run(func, delay:float, *args, **kwargs):
    
    if is_scheduled_item(func):
        unschedule(func)
    # print(*args)
    schedule_once(func, delay, *args, **kwargs)

def reserve_tick_for(tick_func, delay:float, duration:float, interval:float = 1/DEFAULT_FPS, *args, **kwargs):
    
    def reserved(dt):
        return tick_for(tick_func, duration, interval, *args, **kwargs)
    
    reserve_run(reserved, delay)
