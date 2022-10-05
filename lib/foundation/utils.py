'''
utils coupled with arcade, pymunk, pyglet, etc

...and some injections
'''
import functools
from typing import Tuple

import arcade
from arcade.experimental import Shadertoy, lights
from .base import *
from config.engine import *
from pyglet.clock import schedule, schedule_once, schedule_interval, schedule_interval_soft, unschedule
from pyglet.clock import _default as pyglet_clock

import pyglet
import pymunk

### for in-house physics engine

### for code injection of simple physics engine
# will be deprecated after moved to pymunk
import arcade
from arcade import (Point, 
                    PointList, 
                    is_point_in_polygon, 
                    get_distance, 
                    Sprite, 
                    are_polygons_intersecting
                    )
### for code injection of simple physics engine

def is_polygon_intersecting_with_circle(poly: PointList, p: Point, radius: float):  ### function added to arcade simple physics engine
    ''' for legacy simple physics engine '''
    if is_point_in_polygon(*p, poly): return True   # 중심이 안에 있으면 충돌
    
    for i in range(-len(poly), 0):
        if get_distance(*poly[i], *p) <= radius: return True    # 모서리 충돌
        
        p1 = poly[i]
        p2 = poly[i + 1]

        # v12 = (p2[0] - p1[0], p2[1] - p1[1])
        # v21 = (p1[0] - p2[0], p1[1] - p2[1])
        # v1 = (p[0] - p1[0], p[1] - p1[1])
        # v2 = (p[0] - p2[0], p[1] - p2[1])

        # def dot(a:tuple, b:tuple):
        #     return sum(i * j for i, j in zip(a, b))
        
        dot1 = (p2[0] - p1[0]) * (p[0] - p1[0]) + (p2[1] - p1[1]) * (p[1] - p1[1]) >= 0
        dot2 = (p2[0] - p1[0]) * (p[0] - p2[0]) + (p2[1] - p1[1]) * (p[1] - p2[1]) < 0
        
        # if dot(v12, v1) >=0 and dot(v21, v2) >=0:
        if dot1 and dot2:
            projection = ((p2[0] - p1[0]) * (p1[1] - p[1]) - (p1[0] - p[0]) * (p2[1] - p1[1])) / get_distance(*p1, *p2)
        
        # if 0 < projection <= d12:
            if abs(projection) <= radius:
                # print('sides check [colliding]')
                return True
            # print('sides check [not colliding]')
            
        # if projection <= radius: 
        #     print(p, p1, p2, d12, projection)
        #     return True
        
    
    return False

def is_sprite_intersecting_with_line(start:tuple, end:tuple, sprite:arcade.Sprite):
    
    pass

def _check_for_collision(sprite1: Sprite, sprite2: Sprite) -> bool:
    """
    Check for collision between two sprites.

    :param Sprite sprite1: Sprite 1
    :param Sprite sprite2: Sprite 2

    :returns: True if sprites overlap.
    :rtype: bool
    """
    collision_radius_sum = sprite1.collision_radius + sprite2.collision_radius

    diff_x = sprite1.position[0] - sprite2.position[0]
    diff_x2 = diff_x * diff_x

    if diff_x2 > collision_radius_sum * collision_radius_sum:
        return False

    diff_y = sprite1.position[1] - sprite2.position[1]
    diff_y2 = diff_y * diff_y
    if diff_y2 > collision_radius_sum * collision_radius_sum:
        return False

    distance = diff_x2 + diff_y2
    if distance > collision_radius_sum * collision_radius_sum:
        return False

    ### mash custom starts
    if getattr(sprite1, 'collides_with_radius', False):
        if getattr(sprite2, 'collides_with_radius', False):
            # print('collision case 0')
            return True
        else:
            # print('collision case 1')
            return is_polygon_intersecting_with_circle(sprite2.get_adjusted_hit_box(), sprite1.position, sprite1.collision_radius)
    else:
        if getattr(sprite2, 'collides_with_radius', False):
            # print('collision case 2')
            return is_polygon_intersecting_with_circle(sprite1.get_adjusted_hit_box(), sprite2.position, sprite2.collision_radius)
    ### mash custom ends
    
    return are_polygons_intersecting(
        sprite1.get_adjusted_hit_box(), sprite2.get_adjusted_hit_box()
    )

### code injection
arcade.sprite_list.spatial_hash._check_for_collision = _check_for_collision

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

def debug_draw_poly(points:list[Tuple[float, float]],
                    center:Vector = vectors.zero,
                    angle:float = 0.0,
                    line_color = arcade.color.WHITE, 
                    line_thickness = 1, 
                    fill_color = None,
                    radian = False,
                    ):
    if not CONFIG.debug_draw: return False
    
    new_poly = []
    for point in points:
        if angle: point = Vector(point).rotate(angle, radian)
        new_poly.append(point + center)
    
    if fill_color is not None: return arcade.draw_polygon_filled(new_poly, fill_color)
    return arcade.draw_polygon_outline(new_poly, line_color, line_thickness)

def debug_draw_physics(
    body:pymunk.Body,
    line_color = arcade.color.MAGENTA,
    line_thickness = 1,
    fill_color = None,
    ):
    center = Vector(body.position)
    angle = body.angle  ### in radian
    for shape in body.shapes:
        if isinstance(shape, pymunk.Circle):
            center += shape.offset
            debug_draw_circle(center, shape.radius, line_color, line_thickness, fill_color)
        elif isinstance(shape, pymunk.Segment):
            debug_draw_segment(center + shape.a, center + shape.b, line_color, line_thickness)
        else:
            debug_draw_poly(shape.get_vertices(), center, angle, line_color, line_thickness, fill_color, radian=True)
            

def debug_draw_shape(shape:pymunk.Shape,
                     body:pymunk.Body = None,
                     line_color = arcade.color.WHITE, 
                     line_thickness = 1, 
                     fill_color = None,):
    if body is None:
        center = vectors.zero
        angle = 0.0
    else:
        center = body.position
        angle = body.angle  # in radian
    if isinstance(shape, pymunk.Poly):
        debug_draw_poly(shape.get_vertices(), center, angle, line_color, line_thickness, fill_color, radian=True)
    if isinstance(shape, pymunk.Circle):
        center += shape.offset
        debug_draw_circle(center, shape.radius, line_color, line_thickness, fill_color)
    if isinstance(shape, pymunk.Segment):
        debug_draw_segment(center + shape.a, center + shape.b, line_color, line_thickness)

def debug_draw_multi_shape(shapelist:list[pymunk.Poly],
                    body:pymunk.Body,
                    line_color = arcade.color.WHITE, 
                    line_thickness = 1, 
                    fill_color = None
                    ):
    
    for shape in shapelist:
        debug_draw_shape(shape, body, line_color, line_thickness, fill_color)

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

def patched_unschedule_in_clock(self, func, *args):
    
    if args:
        valid_items = set(item for item in self._schedule_interval_items if item.func == func and item.args == args)
    else:
        valid_items = set(item for item in self._schedule_interval_items if item.func == func)

    if self._current_interval_item:
        if self._current_interval_item.func == func:
            valid_items.add(self._current_interval_item)
    # else: print(f'unschedule : {func} not found')

    for item in valid_items:
        item.interval = 0
        item.func = lambda x, *args, **kwargs: x

    self._schedule_items = [i for i in self._schedule_items if i.func != func]

def patched_unschedule(func, *args):
    pyglet_clock.unschedule(func, *args)

pyglet.clock.Clock.unschedule = patched_unschedule_in_clock
unschedule = patched_unschedule
