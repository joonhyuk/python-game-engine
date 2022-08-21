from __future__ import annotations

import math, functools
from config.engine import *

from lib.foundation.base import *
from lib.foundation.clock import *
from lib.foundation.engine import *
from lib.foundation.physics import *


class Projectile(Actor):
    
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
    
    
class AIController(ActorComponent):
    
    def __init__(self) -> None:
        super().__init__()
        self.move_path = None
    
    def tick(self, delta_time: float) -> bool:
        if not super().tick(delta_time): return False
        # self.owner.movement.turn_toward(self.move_path[0])
        # self.owner.movement.move_toward(self.move_path[0])



class InteractionHandler(ActorComponent):
    '''
    handling interaction for actor
    그냥 언리얼처럼 컬리전에서 하는게 낫지 않을지?
    '''
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.others:list[Actor2D] = []
        
    def begin_overlap(self, other:Actor2D):
        self.others.append(other)
    
    def end_overlap(self, other:Actor2D):
        self.others.remove(other)
      

class CameraHandler(ActorComponent):
    '''handling actor camera
    should be possesed by engine camera system'''
    
    def __init__(self) -> None:
        super().__init__()
        self._spawned = False
        self.offset:Vector = Vector(0,0)
        self.camera = Camera(*CONFIG.screen_size)
        self.camera_interp_speed = 0.05
        self.boom_length = 200.0
    
    def tick(self, delta_time: float) -> bool:
        if not super().tick(delta_time): return False
        self.center = self.owner.position
        ENV.abs_screen_center = self.center # not cool...
        self._spawned = False
        # print('camera_tick')
    
    def use(self):
        self._spawned = True
        self.camera.use()
    
    def _get_center(self) -> Vector:
        return self.camera.position + CONFIG.screen_size / 2
    
    def _set_center(self, new_center:Vector = Vector()):
        self.camera.move_to(new_center - CONFIG.screen_size / 2 + self.offset + self._get_boom_vector(), self.camera_interp_speed)
    
    center:Vector = property(_get_center, _set_center)
    
    def _get_boom_vector(self) -> Vector:
        # distv = ENV.cursor_position - ENV.scren_center
        distv = self.owner.position - ENV.abs_cursor_position
        # print(self.owner.rel_position, ENV.cursor_position)
        # return Vector()
        in_min = ENV.window_shortside // 5
        in_max = ENV.window_shortside // 1.2
        ''' 최적화 필요 '''
        return self.owner.forward_vector.unit * self.boom_length * map_range(distv.length, in_min, in_max, 0, 1, clamped=True)


class CharacterMovement(ActorComponent):
    '''movement component for character'''
    def __init__(self, 
                 capsule_radius = 16, 
                 max_speed_run = 250, 
                 max_speed_walk = 70, 
                 acceleration = 25, 
                 braking = 20, 
                 max_rotation_speed = 1080, 
                 rotation_interp_speed = 3, 
                 ) -> None:
        super().__init__()
        self.size = capsule_radius
        
        self.max_speed_run = max_speed_run
        ''' pixel per sec '''
        self.max_speed_walk = max_speed_walk
        ''' pixel per sec '''
        self.max_rotation_speed = max_rotation_speed
        ''' degree per sec '''
        self.rotation_interp_speed = rotation_interp_speed
        
        self.acceleration = acceleration
        ''' speed per sec^2 '''
        self._braking = braking if braking is not None else acceleration
        ''' default braking friction. if set to 0, no braking '''
        self._last_tick_speed = 0.0
        self.move_input:Vector = Vector()
        self.desired_rotation:float = 0.0
        
        self._speed_debug_val = avg_generator(0, 60)
        next(self._speed_debug_val)
        self._debug_speedq = []
        self._debug_braking_time = 0
        
    def tick(self, delta_time:float = None) -> bool:
        if not delta_time: return False
        if not super().tick(delta_time): return False
        
        self._set_movement(delta_time)
        self._set_heading(delta_time)
        
        ENV.debug_text['player_speed'] = self.speed_avg // delta_time
        # ENV.debug_text['player_heading'] = self.rotation
    
    def _set_movement(self, delta_time:float):
        ''' set movement of tick by user input '''
        # self._debug_check_speed(delta_time)
        # print(self.speed_avg)
        if self.move_input is None: return False
        if self.move_input.near_zero():
            ''' stop / braking '''
            if self.velocity.is_zero: return False
            # if not self._braking_start_speed:
            #     self._braking_start_speed = self.velocity.length
            
            # if not self.velocity.near_zero(0.01):
            if not math.isclose(self._last_tick_speed, 0, abs_tol=0.01):
                # self.velocity += -1 * self.velocity.unit * min(self.braking * delta_time, self.speed)
                braking_ratio = clamp((1 - self.braking * delta_time / self._last_tick_speed), 0.0, 1.0)
                # print(round(self._debug_braking_time,1) ,braking_ratio)
                self.velocity *= braking_ratio
                # self.velocity = self.velocity - self.velocity.unit * self.braking * delta_time
                self._debug_braking_time += delta_time
                # print(self.speed, round(self.sec_counter, 1))
                return True
            else:
                self.velocity = Vector()
                return False
        
        accel = self.acceleration
        
        max_speed = map_range_attenuation(self.move_input.length, 0.7, 1, 0, self.max_speed_walk, self.max_speed_run)
        max_speed *= self._get_directional_speed_multiplier()
        ''' apply directional speed limit '''
        self.velocity = (self.velocity + self.move_input.unit * accel * delta_time).clamp_length(max_speed * delta_time)
        self._last_tick_speed = self.velocity.length
        self._debug_braking_time = 0.0
        
        ### debug start
        # a = max_speed * delta_time
        # b = self.velocity.length
        # if abs(a - b) > 0.001:
        #     if b > 150:
        #         print('missing something')
        ### debug end
        
        return True
        
    def _debug_check_speed(self, delta_time):
        if len(self._debug_speedq) > 10: self._debug_speedq.pop(0)
        self._debug_speedq.append(self.velocity.length / delta_time)
        print(round(self._debug_braking_time, 1), sum(self._debug_speedq) // len(self._debug_speedq))
    
    @property
    def speed_avg(self):
        return self._speed_debug_val.send(self.velocity.length)
    
    def _set_heading(self, delta_time:float):
        ''' set player rotation per tick '''
        if self.rotation == self.desired_rotation: return False
        if math.isclose(self.rotation, self.desired_rotation):
            self.rotation = self.desired_rotation
            return False

        rot = rinterp_to(self.rotation, self.desired_rotation, delta_time, self.rotation_interp_speed)
        # rot = self.desired_rotation
        self.rotation = get_positive_angle(rot)
        return True
    
    def _get_directional_speed_multiplier(self):
        angle = abs(get_shortest_angle(self.rotation, self.velocity.argument()))
        return get_curve_value(angle, CONFIG.directional_speed)
    
    def move(self, input:Vector = Vector()):
        self.move_input = input
        # if not self.desired_velocity.almost_there(input * self.max_speed):
        # if self.velocity.almost_there(self.desired_velocity): return False
        
        # if velocity.is_zero: accel = self.braking
        # else: accel = self.acceleration
    
    def turn_toward(self, abs_position:Vector = Vector()):
        ''' turn character to an absolute position '''
        # print(f'player position {self.owner.position}, mouse position {abs_position}')
        angle = (abs_position - self.owner.position).argument()
        self.turn(angle)
    
    def turn_toward_rel(self, rel_position:Vector = Vector()):
        angle = ()
    
    def turn_angle(self, angle:float = 0.0):
        if not angle: return False
        self.desired_rotation += angle
    
    def turn_left(self, angle:float = 0.0):
        ''' turn counter clockwise '''
        return self.turn_angle(angle)
    
    def turn_right(self, angle:float = 0.0):
        ''' turn clockwise '''
        return self.turn_angle(-angle)
    
    def turn(self, rotation:float = 0.0):
        self.desired_rotation = rotation
    
    def stop(self):
        self.move()
    
    # def move_forward(self, speed):
    #     self.owner.body.forward(speed)
    
    def _get_velocity(self) -> Vector:
        return self.owner.velocity
    
    def _set_velocity(self, velocity:Vector = Vector()):
        self.owner.velocity = velocity
    
    velocity:Vector = property(_get_velocity, _set_velocity)
    
    def _get_rotation(self):
        return get_positive_angle(self.owner.angle)
    
    def _set_rotation(self, rotation:float):
        self.owner.angle = get_positive_angle(rotation)
    
    rotation:float = property(_get_rotation, _set_rotation)
    angle:float = property(_get_rotation, _set_rotation)
    
    @property
    def speed(self) -> float:
        ''' speed per sec '''
        return self.speed_tick / CLOCK.delta_time   # need to be removed
    
    @property
    def speed_tick(self) -> float:
        ''' speed per tick '''
        return self.owner.velocity.length
    
    @property
    def braking(self) -> float:
        if hasattr(self.owner, 'braking_friction'):
            return self._braking * self.owner.braking_friction
        else: return self._braking
    

class PhysicsMovement(ActorComponent):
    ''' movement handler for actor based on pymunk physics engine '''
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.move_direction:Vector = None
        self.desired_angle:float = 0.0
        self.rotation_interp_speed = 3.0
    
    def tick(self, delta_time: float) -> bool:
        if not super().tick(delta_time): return False
        self._set_movement(delta_time)
        self._set_heading(delta_time)
    
    def _set_movement(self, delta_time:float):
        if not self.move_direction: return False
        if self.move_direction.near_zero():
            ''' stop '''
            if self.owner.velocity.is_zero: return False
            if self.owner.velocity.near_zero(): self.owner.velocity = vectors.zero
        else:
            # self.owner.velocity = self.move_direction * 250
            angle = abs(get_shortest_angle(self.owner.angle, self.owner.velocity.argument()))
            speed = 1000 * get_curve_value(angle, CONFIG.directional_speed)
            self.owner.body.apply_force_world(self.move_direction * speed)
    
    def _set_heading(self, delta_time:float):
        ''' set player rotation per tick '''
        if self.owner.angle == self.desired_angle: return False
        if math.isclose(self.owner.angle, self.desired_angle):
            self.owner.angle = self.desired_angle
            return False

        rot = rinterp_to(self.owner.angle, self.desired_angle, delta_time, self.rotation_interp_speed)
        # rot = self.desired_rotation
        self.owner.angle = get_positive_angle(rot)
        return True
    
    def move(self, direction:Vector = vectors.zero):
        self.move_direction = direction
    
    def turn(self, angle:float = 0.0):
        self.desired_angle = angle
    
    def turn_toward(self, abs_position:Vector = Vector()):
        ''' turn character to an absolute position '''
        # print(f'player position {self.owner.position}, mouse position {abs_position}')
        angle = (abs_position - self.owner.position).argument()
        self.turn(angle)
    

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
        if delta_time is None: delta_time = CLOCK.delta_time
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
        return Vector(1,0).rotate(self.angle)
    
    @property
    def rel_position(self) -> Vector:
        ''' relative position in viewport '''
        return self.position - ENV.abs_screen_center + CONFIG.screen_size / 2


class Door(Actor2D):
    def __init__(self, body: Sprite = None, hp:float = 1000, **kwargs) -> None:
        super().__init__(body, **kwargs)
        self.hp = hp
        self._open = False
        self._locked = False
        self._sealed = False
    
    def _set_open(self):
        if self._open: return False
        if self._locked or self._sealed: return False
        
        self._open = True
        return self._open
    
    def _get_open(self):
        return self._open
    
    open = property(_get_open, _set_open)
        

class Character2D(Actor2D):
    
    def __init__(self, body: Sprite = None, hp: float = 100, **kwargs) -> None:
        super().__init__(body, **kwargs)
        self.hp = hp
        self.movement = CharacterMovement()
        self.camera = CameraHandler()
        self.action = None
        self.controller = None
        
        self.constructor()
    
    def constructor(self):
        pass
    
    def get_physics_body(self) -> Sprite:
        return Capsule(self.size // 2)
    
    def tick(self, delta_time: float = None) -> bool:
        if not super().tick(delta_time): return False
        direction = ENV.direction_input
        if direction: self.movement.turn_toward(direction)
        self.movement.move(ENV.move_input)
        
    def apply_damage(self, damage:float):
        self.hp -= damage
    
    @property
    def is_alive(self) -> bool:
        if self.hp <= 0: return False
        return super().is_alive


class NPC(Character2D):
    
    def constructor(self):
        self.controller = AIController()
        
    def get_physics_body(self) -> Sprite:
        return None


class Player(Actor):
    
    def __init__(self, physics_engine: PhysicsEngine = None, **kwargs) -> None:
        super().__init__(sprite = Sprite(IMG_PATH + 'player_handgun_original.png'), 
                         size = Vector(32, 32), 
                         physics_engine = physics_engine, 
                         mass = 1, 
                         body_type = physics_types.dynamic, 
                         collision_type = collision.character, 
                         physics_shape = physics_types.circle, 
                         **kwargs)
        self.hp = 100
        self.camera = CameraHandler()
        self.movement = PhysicsMovement()

    def tick(self, delta_time: float = None) -> bool:
        if not super().tick(delta_time): return False
        direction = ENV.direction_input
        if direction: self.movement.turn_toward(direction)
        self.movement.move(ENV.move_input)
        
    def apply_damage(self, damage:float):
        self.hp -= damage
    
    @property
    def is_alive(self) -> bool:
        if self.hp <= 0: return False
        return super().is_alive
