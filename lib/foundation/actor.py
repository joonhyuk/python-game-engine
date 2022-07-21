import math, functools
from config.engine import *

from lib.foundation.base import *
from lib.foundation.clock import *
from lib.foundation.engine import *

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
            # schedule_once(self.destroy, lifetime)
        
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
    def __init__(self) -> None:
        super().__init__()
        self.owner:Actor2D = None
    
    def tick(self, delta_time:float) -> bool:
        return super().tick(delta_time)

class CameraHandler(ActorComponent):
    '''handling actor camera
    should be possesed by engine camera system'''
    
    def __init__(self) -> None:
        super().__init__()
        self.offset:Vector = Vector(0,0)
        self.camera = Camera(*CONFIG.screen_size)
        self.camera_interp_speed = 0.1
        self.boom_length = 100.0
    
    def tick(self, delta_time: float) -> bool:
        if not super().tick(delta_time): return False
        self.center = self.owner.position
        ENV.abs_screen_center = self.center
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
        return self.owner.forward_vector.unit * self.boom_length


class CharacterMovement(ActorComponent):
    '''movement component for character'''
    def __init__(self, 
                 max_speed_run = 250, 
                 max_speed_walk = 70, 
                 acceleration = 25, 
                 braking = 20, 
                 max_rotation_speed = 1080, 
                 rotation_interp_speed = 3, 
                 ) -> None:
        super().__init__()
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
        
        self._spawned = True
        
        self._debug_speedq = []
        self._debug_braking_time = 0
        
    def tick(self, delta_time:float = None) -> bool:
        if not delta_time: return False
        if not super().tick(delta_time): return False
        
        self._set_movement(delta_time)
        self._set_heading(delta_time)
    
    def _set_movement(self, delta_time:float):
        ''' set movement by user input '''
        # self._debug_check_speed(delta_time)
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
        
        max_speed = map_range_attenuation(self.move_input.length, 0.7, 1, 0, self.max_speed_walk, self.max_speed_run)
        self.velocity = (self.velocity + self.move_input.unit * self.acceleration * delta_time).clamp_length(max_speed * delta_time)

        self._last_tick_speed = self.velocity.length
        # print(self._last_tick_speed)
        self._debug_braking_time = 0.0
        
        ### debug start
        a = max_speed * delta_time
        b = self.velocity.length
        if abs(a - b) > 0.001:
            if b > 150:
                print('missing something')
        ### debug end
        
        return True
        
    def _debug_check_speed(self, delta_time):
        
        if len(self._debug_speedq) > 10: self._debug_speedq.pop(0)
        self._debug_speedq.append(self.velocity.length / delta_time)
        print(round(self._debug_braking_time, 1), sum(self._debug_speedq) // len(self._debug_speedq))
    
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
    
    def move_forward(self, speed):
        self.owner.body.forward(speed)
    
    def _get_velocity(self) -> Vector:
        return self.owner.velocity
    
    def _set_velocity(self, velocity:Vector = Vector()):
        self.owner.velocity = velocity
    
    velocity:Vector = property(_get_velocity, _set_velocity)
    
    def _get_rotation(self):
        return get_positive_angle(self.owner.rotation)
    
    def _set_rotation(self, rotation:float):
        self.owner.rotation = get_positive_angle(rotation)
    
    rotation:float = property(_get_rotation, _set_rotation)
    
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
    

class Actor2D(MObject):
    ''' top-down based actor object which has position, rotation, collision '''
    def __init__(self, 
                 body:Sprite = None, 
                 **kwargs) -> None:
        super().__init__(**kwargs)
        self.body:Sprite = None
        ''' actual body to be rendered. (i.e. pygame.Surface, arcade.Sprite, ...) '''
        self.set_body(body)
        
        self.visibility = get_from_dict(kwargs, 'visibility', True)
        
        self.tick_group = []
        ''' tick group '''
    
    def set_body(self, body:Sprite = None) -> None:
        if self.body: self.remove_body()
        self.body = body or SpriteCircle()
    
    def spawn(self, 
              position:Vector = Vector(), 
              rotation:float = None, 
              layer:Layer = None, 
              lifetime=0) -> None:
        self.position = position
        self.rotation = rotation
        # if sprite_list:
        self.register_body(layer)
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
    
    def _get_position(self) -> Vector:
        if not self.body: return False
        return Vector(self.body.position)
    
    def _set_position(self, new_position:Vector = Vector(0., 0.)) -> bool:
        if not self.body: return False
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
        return self.body.angle
    
    @check_body
    def _set_rotation(self, rotation:float = 0.0) -> bool:
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
        return Vector(self.body.velocity)
    
    # @check_body
    def _set_velocity(self, velocity:Vector = Vector()):
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
    def register_body(self, sprite_list:Layer):
        return sprite_list.append(self.body)
    
    @check_body
    def remove_body(self):
        return self.body.remove_from_sprite_lists()
    
    visibility:bool = property(_get_visibility, _set_visibility)
    position:Vector = property(_get_position, _set_position)
    rotation:float = property(_get_rotation, _set_rotation)
    velocity:Vector = property(_get_velocity, _set_velocity)
    
    @property
    @check_body
    def forward_vector(self):
        return Vector(1,0).rotate(self.body.angle)
    
    @property
    def rel_position(self) -> Vector:
        return self.position - ENV.abs_screen_center + CONFIG.screen_size / 2
    

class Pawn2D(Actor2D):
    pass

class Character2D(Actor2D):
    
    def __init__(self, body: Sprite = None, hp: float = 100, **kwargs) -> None:
        super().__init__(body, **kwargs)
        self.hp = hp
        self.movement = CharacterMovement()
        self.camera = CameraHandler()
        
        self.constructor()
    
    def constructor(self):
        pass
    
    def tick(self, delta_time: float = None) -> bool:
        if not super().tick(delta_time): return False
        
    def apply_damage(self, damage:float):
        self.hp -= damage