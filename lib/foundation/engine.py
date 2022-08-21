"""
framework wrapper for audio / video / control
might be coupled with base framwork(i.e. arcade, pygame, ...)
joonhyuk@me.com
"""
from __future__ import annotations

import os
import PIL.Image
import PIL.ImageOps
import PIL.ImageDraw

from dataclasses import dataclass
from typing import Union

import arcade

from lib.foundation.base import *
from lib.foundation.clock import *
from lib.foundation.physics import *
from lib.foundation.utils import *

from config.engine import *


class DebugTextLayer(dict, metaclass=SingletonType):
    '''
    use text_obj property to access text attributes
    
    bgcolor not working now
    
    '''
    def __init__(self, 
                 font_name = 'Kenney Mini Square', 
                 font_size = 10, 
                 color = (255,255,255,128),
                 bgcolor = None, 
                 topleft_position:Vector = Vector.diagonal(10) 
                 ):
        self.content = ''
        self._position = topleft_position
    
        self.font_name = font_name
        self.font_size = font_size
        self.color = color
        self.bgcolor = bgcolor
        self.text:arcade.Text = None
        self.width = CONFIG.screen_size.x
        
        self.setup()
    
    def setup(self):
        self.width = CONFIG.screen_size.x
        position = Vector(self._position.x, CONFIG.screen_size.y - self._position.y)
        # position.y = CONFIG.screen_size.y - position.y
        self.text = arcade.Text('', *position, self.color, self.font_size, 
                                font_name=self.font_name, 
                                width = self.width, 
                                anchor_y = 'top', 
                                multiline=True)
        print(position)
    
    def draw(self):
        text = ''
        for k, v in self.items():
            text += ' : '.join((k, str(v)))
            text += '\n'
        self.text.value = text
        self.text.draw()
    
    def _set_topleft_position(self, position:Vector):
        self._position = position
        self.setup()
    
    def _get_topleft_position(self):
        return self._position
    
    def perf_start(self, name:str = 'foo'):
        self[name] = CLOCK.perf
    
    def perf_end(self, name:str = 'foo'):
        self[name] = f'{round((CLOCK.perf - self[name]) * 1000,2)} ms'
    
    def perf_check(self, name:str = 'foo'):
        ''' kinda toggle function '''
        if name in self:
            if isinstance(self[name], float): return self.perf_end(name)
        return self.perf_start(name)
    
    position = property(_get_topleft_position, _set_topleft_position)
    ''' topleft position of text box '''


@dataclass
class Environment:
    ''' I/O for game
    
    - 디스플레이 정보
        - 렌더링 배율
    - 현재 뷰포트 중앙의 절대 좌표
    - 이동 조작, 카메라 조작
    - 게임패드 입력 raw
    - 마우스 입력 raw
        - 뷰포트 내 상대좌표
        - 월드상의 절대 좌표
    
    (나중에 Window 클래스에 통합시켜버릴 수도 있음)
    '''
    
    delta_time:float = 0.0
    physics_engine = None
    window:Window = None
    abs_screen_center:Vector = Vector()
    render_scale:float = 1.0
    mouse_screen_position:Vector = Vector()
    gamepad:arcade.joysticks.Joystick = None
    key_move:Vector = Vector()
    key = arcade.key
    key_inputs = []
    debug_text:DebugTextLayer = None
    
    last_abs_pos_mouse_lb_pressed:Vector = vectors.zero
    last_abs_pos_mouse_lb_released:Vector = vectors.zero
    
    window_shortside = None
    window_longside = None
    
    def __init__(self) -> None:
        self.set_gamepad()
    
    def set_gamepad(self):
        ''' 게임패드 접속/해제 대응 필요 '''
        self.gamepad = self.get_input_device()
    
    def get_input_device(self, id:int = 0):
        joysticks = arcade.get_joysticks()
        if joysticks:
            gamepad = joysticks[id]
            gamepad.open()
            gamepad.push_handlers(self)
            print(f'Gamepad[{id}] attached')
            return gamepad
        return None
    
    def set_screen(self, window:Window):
        ''' should be called after resizing, fullscreen, etc. '''
        self.window = window
        window_x = window.get_size()[0]
        window_y = window.get_size()[1]
        self.window_shortside = min(window_x, window_y)
        self.window_longside = max(window_x, window_y)
        
        self.render_scale = window.get_framebuffer_size()[0] / self.window_longside
    
    def on_key_press(self, key:int, modifiers:int):
        self.key_inputs.append(key)
        self.key_inputs.append(modifiers)
    
    def on_key_release(self, key:int, modifiers:int):
        self.key_inputs.remove(key)
        self.key_inputs.remove(modifiers)
    
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
            return self.key_move.clamp_length(1) * (0.5 if self.window.lctrl_applied else 1)

    move_input:Vector = property(_get_move_input)
    ''' returns movement direction vector (-1, -1) ~ (1, 1) '''
    
    def _get_direction_input(self):
        if self.gamepad:
            if self.rstick.length > 0.5:
                return (self.rstick.unit * CONFIG.screen_size.y / 2 + self.abs_screen_center) * self.render_scale
        else:
            return self.abs_cursor_position
    
    direction_input:Vector = property(_get_direction_input)
    ''' returns relative target point '''
    
    def _get_cursor_position(self) -> Vector:
        # if not self.mouse_input: return Vector()
        return self.mouse_screen_position * self.render_scale
    
    cursor_position:Vector = property(_get_cursor_position)
    ''' returns relative mouse cursor point '''
    
    def _get_abs_cursor_position(self) -> Vector:
        return self.mouse_screen_position + self.abs_screen_center - CONFIG.screen_size / 2
        # return self.mouse_input + self.window.current_camera.position
    
    abs_cursor_position:Vector = property(_get_abs_cursor_position)
    ''' get absolute position in world, pointed by mouse cursor '''


class MObject(object):
    def __init__(self, **kwargs) -> None:
        self.id:str = self.get_id()
        """set id by id()"""
        self._alive:bool = True
        """object alive state. if not, should be destroyed"""
        self._lifetime:float = None
        self._update_tick:bool = True
        self._spawned = False
        """tick optimization"""
        if kwargs:
            for k in kwargs:
                # setattr(self, k, kwargs[k])
                self.__setattr__(k, kwargs[k])
        
    def get_id(self) -> str:
        return str(id(self))
    
    def spawn(self, lifetime:float = None) -> None:
        
        if lifetime is not None:
            self._lifetime = lifetime
        
        if self._lifetime:
            CLOCK.timer_start(self.id)
        
        self._spawned = True
    
    def tick(self, delta_time:float) -> bool:
        """alive, ticking check\n
        if false, tick deactivated"""
        if not (self._spawned and self._update_tick and self._alive): return False
        if self._lifetime:
            if self._lifetime > CLOCK.timer_get(self.id):
                return True
            else:
                return self.destroy()
        else:
            '''additional lifecycle management could be here'''
            return True
    
    def set_update(self, switch = True):
        self._update_tick = switch
    
    def destroy(self) -> bool:
        self._alive = False
        CLOCK.timer_remove(self.id)
        # del self    # ????? do we need it?
        return False
    
    def set_kwargs(self, kwargs:dict, keyword:str, default:... = None):
        self.__dict__[keyword] = get_from_dict(kwargs, keyword, default)
    
    @property
    def remain_lifetime(self) -> float:
        if self._lifetime:
            return 1 - CLOCK.timer_get(self.id) / self._lifetime
        else: return 1
    
    @property
    def is_alive(self) -> bool:
        return self._alive


class ActorComponent(MObject):
    '''component base class'''
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.owner:Actor = None
        self._spawned = True
    
    def tick(self, delta_time:float) -> bool:
        return super().tick(delta_time)


class Actor(MObject):
    def __init__(self, 
                 sprite:Sprite,
                 size:Vector = None,
                 physics_engine:PhysicsEngine = None,
                 mass:float = 1.0,
                 body_type:int = None,
                 collision_type:int = None,
                 elasticity:float = None,
                 friction:float = 0.2,
                 shape_edge_radius:float = 0.0,
                 physics_shape = None,
                 name:Optional[str] = None,
                 **kwargs) -> None:
        super().__init__(**kwargs)
        self.body:Body = Body(sprite, 
                              size, 
                              physics_engine, 
                              mass, body_type, 
                              collision_type, 
                              elasticity, 
                              friction, 
                              shape_edge_radius, 
                              physics_shape)
        self.tick_group:list[ActorComponent] = []
    
    def spawn(self, 
              position:Vector = vectors.zero, 
              angle:float = 0.0, 
              velocity:Vector = None,
              visibility:bool = True,
              lifetime:float = 0.0
              ):
        super().spawn(lifetime)
        self.register_components()
        
        self.body.spawn()
        self.position = position
        self.angle = angle
        
        if velocity: self.velocity = velocity
        if not visibility: self.visibility = False
    
    def tick(self, delta_time:float = None) -> bool:
        if delta_time is None: delta_time = CLOCK.delta_time
        if not super().tick(delta_time): return False
        if self.tick_group:
            for ticker in self.tick_group:
                ticker.tick(delta_time)
                # print('character_tick', delta_time)
        return True
    
    def register_components(self):
        for k, v in self.__dict__.items():
            if isinstance(v, (ActorComponent, )):
                v.owner = self
                ''' set owner '''
            if hasattr(v, 'tick'):
                self.tick_group.append(v)
                ''' for components that have tick '''
    
    def draw(self):
        self.body.draw()
    
    def _get_visibility(self) -> bool:
        return self.body.visibility
    
    def _set_visibility(self, switch:bool):
        self.body.visibility = switch
    
    visibility:bool = property(_get_visibility, _set_visibility)
    
    def _get_position(self) -> Vector:
        return self.body.position
    
    def _set_position(self, position) -> None:
        self.body.position = position
    
    position:Vector = property(_get_position, _set_position)
    
    def _get_angle(self) -> float:
        return self.body.angle
    
    def _set_angle(self, angle:float):
        self.body.angle = angle
    
    angle:float = property(_get_angle, _set_angle)
    
    def _get_velocity(self) -> Vector:
        return self.body.velocity
    
    def _set_velocity(self, velocity):
        self.body.velocity = velocity
    
    velocity:Vector = property(_get_velocity, _set_velocity)
    
    @property
    def screen_position(self) -> Vector:
        ''' relative position in viewport '''
        return self.position - ENV.abs_screen_center + CONFIG.screen_size / 2
    
    @property
    def forward_vector(self) -> Vector:
        return self.body.forward_vector


class Body(ActorComponent):
    '''
    has size, sprite for draw, move(collision), hit(collision)
    based on pymunk physics engine
    가능한 엔진에 종속되지 않도록.
    '''
    
    def __init__(self, 
                 sprite:Sprite, 
                 size:Vector = None,
                 physics_engine:PhysicsEngine = None,
                 mass:float = 1.0,
                 body_type:int = None,
                 collision_type:int = None,
                 elasticity:float = None,
                 friction:float = None,
                 shape_edge_radius:float = 0.0,
                 physics_shape = None,
                 ) -> None:
        super().__init__()
        self.sprite:Sprite = None
        ''' for draw. should be expanded for attachment and vfx '''
        self.physics:PhysicsObject = None
        ''' for move, hit check
        body : [mass, moment, type(STATIC, DYNAMIC, KINEMATIC)]
        shape : [body, size or vertices, radius, collision_type, elasticity, friction]
        hitbox : use shape or sprite poly
        '''
        self._physics_engine:PhysicsEngine = None
        self.mass_mul:float = 1.0
        self.mass_add:float = 0.0
        self.friction_mul:float = 1.0
        self.friction_add:float = 0.0
        self.elasticity_mul:float = 1.0
        self.elasticity_add:float = 0.0
        
        if physics_shape is physics_types.circle:
            rad = max(size.x, size.y) / 2
            shape = physics_types.circle(body = None, radius = rad)
            # moment = pymunk.moment_for_circle(mass, 0, rad)
            moment = PhysicsEngine.MOMENT_INF
        else:
            shape = None
            moment = None
        self.setup(sprite = sprite, 
                   physics_engine = physics_engine, 
                   mass = mass, 
                   moment = moment, 
                   body_type = body_type, 
                   shape = shape, 
                   collision_type = collision_type, 
                   elasticity = elasticity, 
                   friction = friction, 
                   shape_edge_radius = shape_edge_radius
                   )
    
    def setup(self,
              sprite:Sprite,
              physics_engine:PhysicsEngine = None,
              mass:float = 1,
              moment:float = 0,
              body_type:int = None,
              shape:physics_types.shape = None,
              collision_type:int = collision.default,
              elasticity:float = None,
              friction:float = 0.2,
              shape_edge_radius:float = 0.0,
              ):
        self.sprite = sprite
        self._physics_engine = physics_engine
        if self._physics_engine:
            self.physics = self._physics_engine.add_sprite(sprite = self.sprite,
                                                           mass = mass,
                                                           moment_of_inertia = moment,
                                                           body_type = body_type,
                                                           shape = shape,
                                                           elasticity = elasticity,
                                                           friction = friction,
                                                           radius = shape_edge_radius,
                                                           collision_type = collision_type,
                                                           spawn = False,
                                                           )
        
    @property
    def has_physics(self) -> bool:
        if self._physics_engine: return True
        return False
    
    def spawn(self, object_layer:ObjectLayer = None):
        if self.has_physics:
            self._physics_engine.add(self.sprite)
        if object_layer:
            object_layer.add(self.sprite)
    
    def remove(self):
        if self.has_physics: self._physics_engine.remove_sprite(self.sprite)
        if self.sprite: self.sprite.remove_from_sprite_lists()
        # if self.physics: self.physics
        # if self.hit_collision: self.hit_collision.remove_from_sprite_lists()
    
    def draw(self):
        self.sprite.draw()
        if CONFIG.debug_draw: 
            self.physics.draw()
    
    def tick(self, delta_time: float) -> bool:
        if not super().tick(delta_time): return False
        # self.sync()       ## no. use PhysicsEngine.step() first.
        ''' code implementation for body manipulation will be here '''
        ENV.debug_text['player_speed'] = round(self.speed, 1)
        # ENV.debug_text['player_velocity'] = self.velocity
    
    def apply_force(self, force:Vector = vectors.zero):
        if not self.has_physics: self.velocity += force / self.physics.body.mass
        else: return self.physics.body.apply_force_at_local_point(force)
    
    def apply_impulse(self, impulse:Vector = vectors.zero):
        if not self.has_physics: PhysicsException('Can\'t apply impulse to non-physics object')
        return self.physics.body.apply_impulse_at_local_point(impulse)
    
    def apply_force_world(self, force:Vector = vectors.zero):
        if not self.has_physics: self.velocity += force / self.physics.body.mass    ### should revisit later
        return self.physics.body.apply_force_at_world_point(force, self.position)
    
    def apply_impulse_world(self, impulse:Vector = vectors.zero):
        if not self.has_physics: PhysicsException('Can\'t apply impulse to non-physics object')
        return self.physics.body.apply_impulse_at_world_point(impulse, self.position)
    
    def sync(self):
        ''' mostly not used manually '''
        if not self.physics: return False
        if self.physics.body.is_sleeping: return False
        
        pos_diff = self.position - self.sprite.position
        ang_diff = self.angle - self.sprite.angle
        
        self.sprite.position = self.position
        self.sprite.angle = self.angle
        
        self.sprite.pymunk_moved(self.physics, pos_diff, ang_diff)
        return True
    
    def _get_visibility(self) -> bool:
        return self.sprite.visible
    
    def _set_visibility(self, switch:bool):
        self.sprite.visible = switch
    
    visibility:bool = property(_get_visibility, _set_visibility)
        
    def _get_position(self) -> Vector:
        if self.physics:
            return Vector(self.physics.body.position)
        return Vector(self.sprite.position)
    
    def _set_position(self, position) -> None:
        if self.physics:
            self.physics.body.position = position
        else: self.sprite.position = position
    
    position:Vector = property(_get_position, _set_position)
    
    def _get_angle(self) -> float:
        if self.physics:
            return math.degrees(self.physics.body.angle)
        return self.sprite.angle
    
    def _set_angle(self, angle:float = 0.0):
        if self.physics:
            self.physics.body.angle = math.radians(angle)
        else: self.sprite.angle = angle
    
    angle:float = property(_get_angle, _set_angle)
    
    def _get_velocity(self) -> Vector:
        if self.physics:
            return Vector(self.physics.body.velocity)
        return Vector(self.sprite.velocity)
    
    def _set_velocity(self, velocity):
        if self.physics:
            self.physics.body.velocity = velocity   ### physics.body.velocity is tuple
        else: self.sprite.velocity[:] = velocity[:] ### trivial optimization for list
    
    velocity:Vector = property(_get_velocity, _set_velocity)
    
    def _get_mass(self):
        return self.physics.body.mass * self.mass_mul + self.mass_add
    
    def _set_mass(self, mass:float):
        self.physics.body.mass = mass
    
    mass:float = property(_get_mass, _set_mass)
    
    def _get_damping(self):
        return self.sprite.pymunk.damping
    
    def _set_damping(self, damping:float):
        self.sprite.pymunk.damping = damping
    
    damping:float = property(_get_damping, _set_damping)
    
    def _get_max_speed(self):
        return self.sprite.pymunk.max_velocity
    
    def _set_max_speed(self, max_speed:int):
        self.sprite.pymunk.max_velocity = max_speed
    
    max_speed:int = property(_get_max_speed, _set_max_speed)
    
    @property
    def forward_vector(self) -> Vector:
        return vectors.right.rotate(self.angle)
    
    @property
    def speed(self):
        ''' different from physics or sprite 
        
        :physics = per sec
        :sprite = per tick
        '''
        return self.velocity.length


class Window(arcade.Window):
    
    ### class variables : are they needed?
    lshift_applied = False
    lctrl_applied = False
    current_camera:arcade.Camera = None
    
    def on_show(self):
        # print('window_show')
        ENV.set_screen(self)
        # self.direction_input = Vector()
        # self.get_input_device()
        if ENV.gamepad: self.set_mouse_visible(False)
        ENV.debug_text = DebugTextLayer()
        ENV.debug_text['fps'] = 0
        
    def on_key_press(self, key: int, modifiers: int):
        # ENV.key_inputs.append(key)
        if key in (arcade.key.W, arcade.key.UP): ENV.key_move += (0,1)
        if key in (arcade.key.S, arcade.key.DOWN): ENV.key_move += (0,-1)
        if key in (arcade.key.A, arcade.key.LEFT): ENV.key_move += (-1,0)
        if key in (arcade.key.D, arcade.key.RIGHT): ENV.key_move += (1,0)
        if key == arcade.key.LSHIFT: self.lshift_applied = True
        if key == arcade.key.LCTRL: self.lctrl_applied = True
        
        if key == arcade.key.F2: CONFIG.debug_draw = not CONFIG.debug_draw
        
        ENV.on_key_press(key, modifiers)
        
    def on_key_release(self, key: int, modifiers: int):
        # ENV.key_inputs.remove(key)
        if key in (arcade.key.W, arcade.key.UP): ENV.key_move -= (0,1)
        if key in (arcade.key.S, arcade.key.DOWN): ENV.key_move -= (0,-1)
        if key in (arcade.key.A, arcade.key.LEFT): ENV.key_move -= (-1,0)
        if key in (arcade.key.D, arcade.key.RIGHT): ENV.key_move -= (1,0)
        if key == arcade.key.LSHIFT: self.lshift_applied = False
        if key == arcade.key.LCTRL: self.lctrl_applied = False

        ENV.on_key_release(key, modifiers)
        
    def on_update(self, delta_time: float):
        ENV.delta_time = delta_time
        ENV.debug_text['fps'] = CLOCK.fps_average
        # CLOCK.tick()
        
    def on_draw(self):
        # print('window_draw')
        ENV.debug_text.draw()
        pass
    
    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int):
        ENV.mouse_screen_position = Vector(x, y)
    
    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        if button == arcade.MOUSE_BUTTON_LEFT:
            ENV.last_abs_pos_mouse_lb_pressed = ENV.abs_cursor_position
    
    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int):
        if button == arcade.MOUSE_BUTTON_LEFT:
            ENV.last_abs_pos_mouse_lb_released = ENV.abs_cursor_position
    
    def run(self):
        arcade.run()
    
    @property
    def render_ratio(self):
        return self.get_framebuffer_size()[0] / self.get_size()[0]
    
    @property
    def cursor_position(self) -> Vector:
        return ENV.mouse_screen_position * ENV.render_scale


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
    
    def on_update(self, delta_time: float):
        ENV.delta_time = delta_time

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
        self.owner = None
        super().__init__(filename, scale, image_x, image_y, image_width, image_height, center_x, center_y, repeat_count_x, repeat_count_y, flipped_horizontally, flipped_vertically, flipped_diagonally, hit_box_algorithm, hit_box_detail, texture, angle)
        self.collides_with_radius = False

    def remove_from_sprite_lists(self, dt):
        return super().remove_from_sprite_lists()


class SpriteCircle(arcade.SpriteCircle):
    def __init__(self, 
                 radius: int = 16, 
                 color: arcade.Color = arcade.color.ALLOY_ORANGE, 
                 soft: bool = False):
        super().__init__(radius, color, soft)

    def remove_from_sprite_lists(self, dt):
        # print('REMOVING!')
        return super().remove_from_sprite_lists()


class Capsule(Sprite):
    
    def __init__(self, radius: int):
        super().__init__()
        
        diameter = radius * 2
        cache_name = arcade.sprite._build_cache_name("circle_texture", diameter, 255, 255, 255, 64, 0)
        texture = None
        
        # texture = make_circle_texture(diameter, color, name=cache_name)
        
        img = PIL.Image.new('RGBA', (diameter, diameter), (0,0,0,0))
        draw = PIL.ImageDraw.Draw(img)
        draw.ellipse((0, 0, diameter - 1, diameter - 1), fill=(255,255,255,64))
        texture = arcade.Texture(cache_name, img, 'Detailed', 1.0)
        
        arcade.texture.load_texture.texture_cache[cache_name] = texture
        
        self.texture = texture
        self._points = self.texture.hit_box_points
        self.collision_radius = radius
        self.collides_with_radius = True
        
        print('points : ', self._points)

    def draw_hit_box(self, color: arcade.Color = ..., line_thickness: float = 1):
        return debug_draw_circle(self.position, self.collision_radius, color, line_thickness)


class ObjectLayer(arcade.SpriteList):
    
    def add(self, sprite):
        self.append(sprite)
    
    pass


class ActorLayer:
    
    def __init__(self) -> None:
        self.sprite_list:ObjectLayer = None
        self.actors:list = None
        
        
# class ObjectLayer:
    
#     def __init__(self) -> None:
#         self.sprite_list:SpriteLayer = None
    
#     def add(self, element:object):
#         for k, v in element.__dict__.items():
#             if isinstance(v, (Sprite)):
#                 pass


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
    ENV = Environment()
    
    # DEBUG = DebugTextLayer()