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
        # self._update_render:bool = True
        # """rendering optimization"""
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
    
    def tick(self) -> bool:
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

    # def check_super(f):
    #     @functools.wraps(f)
    #     def wrapper(*args, **kwargs):
    #         if not super().f(*args, **kwargs): return False
    #         return f(*args, **kwargs)
    #     return wrapper
    
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
    
    def tick(self) -> bool:
        return super().tick()

class CameraHandler(ActorComponent):
    '''handling actor camera
    should be possesed by engine camera system'''
    def __init__(self) -> None:
        super().__init__()
        self.offset:Vector = None
        

class CharacterMovement(ActorComponent):
    '''movement component for character'''
    def __init__(self, 
                 max_speed = 200, 
                 acceleration = 10, 
                 braking = 5, 
                 max_rotation_speed = 360
                 ) -> None:
        super().__init__()
        self.max_speed = max_speed
        self.max_rotation_speed = max_rotation_speed
        self.acceleration = acceleration
        self._braking = braking if braking is not None else acceleration
        ''' default braking friction. if set to 0, no braking '''
        self.desired_velocity:Vector = Vector()
        self.move_input:Vector = Vector()
        self._spawned = True
        
    def tick(self, delta_time:float = None) -> bool:
        if not super().tick(): return False
        if delta_time is None: delta_time = CLOCK.delta_time
        
        if self.velocity.almost_there(self.desired_velocity, 0.1): return False
        
        if self.desired_velocity.is_zero:
            if not self.velocity.is_zero:
                # print(self.velocity.norm())
                self.velocity += self.velocity * -1 * self.braking * delta_time
        
        self.velocity = (self.velocity + self.desired_velocity * self.acceleration * delta_time).clamp_length(self.max_speed * delta_time)
        # accel = (-1 * self.braking if self.desired_velocity.is_zero else self.acceleration) * self.desired_velocity.normalize()
        # self.velocity = (self.velocity + accel * delta_time).clamp_length(self.max_speed * delta_time)
        # self.velocity = vinterp_to(self.velocity, self.desired_velocity, delta_time, 1).clamp_length(self.max_speed * delta_time)
        # print(self.desired_velocity, self.velocity)
        
    def move(self, input:Vector = Vector()):
        self.move_input = input
        if not self.desired_velocity.almost_there(input * self.max_speed):
            self.desired_velocity = input * self.max_speed
        # if self.velocity.almost_there(self.desired_velocity): return False
        
        # if velocity.is_zero: accel = self.braking
        # else: accel = self.acceleration
    
    def stop(self):
        # print('stop')
        self.move()
    
    def move_forward(self, speed):
        self.owner.body.forward(speed)
    
    def _get_velocity(self) -> Vector:
        return self.owner.velocity
    
    def _set_velocity(self, velocity:Vector = Vector()):
        self.owner.velocity = velocity.clamp_length(self.max_speed)
    
    velocity:Vector = property(_get_velocity, _set_velocity)
    
    def _get_rotation(self):
        return get_positive_angle(self.owner.rotation)
    
    def _set_rotation(self, rotation:float):
        self.owner.rotation = get_positive_angle(rotation)
    
    rotation = property(_get_rotation, _set_rotation)
    
    @property
    def speed(self):
        return Vector(self.owner.body.velocity).length
    
    @property
    def braking(self):
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
              sprite_list:arcade.SpriteList = None, 
              lifetime=0) -> None:
        self.position = position
        self.rotation = rotation
        # if sprite_list:
        self.register_body(sprite_list)
        self.register_components()
        return super().spawn(lifetime)
    
    def tick(self, delta_time:float = None) -> bool:
        if delta_time is None: delta_time = CLOCK.delta_time
        if not super().tick(): return False
        if self.tick_group:
            for ticker in self.tick_group:
                ticker.tick()
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
        
    @check_body
    def _get_velocity(self):
        return Vector(self.body.velocity)
    
    @check_body
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
    def register_body(self, sprite_list:arcade.SpriteList):
        return sprite_list.append(self.body)
    
    @check_body
    def remove_body(self):
        return self.body.remove_from_sprite_lists()
    
    visibility = property(_get_visibility, _set_visibility)
    position = property(_get_position, _set_position)
    rotation = property(_get_rotation, _set_rotation)
    velocity = property(_get_velocity, _set_velocity)
    
    @property
    @check_body
    def forward_vector(self):
        return Vector(0,1).rotate(self.body.angle)
    

class Pawn2D(Actor2D):
    
    def __init__(self, 
                 body: Sprite = None, 
                 **kwargs) -> None:
        super().__init__(body, **kwargs)
        # self.max_velocity = kwargs['max_velocity'] or 100
        self.max_velocity = get_from_dict(kwargs, 'max_velocity')
        # self.rotation_speed = kwargs['rotation_speed'] or 90
        self.set_kwargs(kwargs, 'rotation_speed', 90)
        # self.acceleration = kwargs['acceleration'] or 1
        # self.braking = kwargs['braking'] or self.acceleration
        
        '''rotation speed in degrees per second'''
        
    def tick(self, delta_time:float = None) -> bool:
        if not super().tick(): return False
        if delta_time is None: delta_time = CLOCK.delta_time
        # if self.velocity < self.max_velocity: self.velocity += self.acceleration
        
    
    def turn_to(self, rotation:float):
        self.rotation = rotation
    
    def turn_left(self, rotation_speed:float = None, delta_time:float = None):
        '''if delta_time is 1, will turn immediately'''
        if delta_time is None: delta_time = CLOCK.delta_time
        # if rotation_speed is None: rotation_speed = self.rotation_speed
        
        theta = rotation_speed * delta_time
        return self.body.turn_left(theta)
    

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