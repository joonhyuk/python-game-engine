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
        """tick optimization"""
        # self._update_render:bool = True
        # """rendering optimization"""
        if kwargs:
            for k in kwargs:
                setattr(self, k, kwargs[k])
        
    def get_id(self) -> str:
        return str(id(self))
    
    def spawn(self, lifetime = 0.0) -> None:
        if lifetime:
            self._lifetime:float = lifetime
            CLOCK.timer_start(self.id)
    
    def tick(self) -> bool:
        """alive, ticking check\n
        if false, tick deactivated"""
        if not (self._update_tick and self._alive): return False
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
        return True

    def check_super(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            if not super().f(*args, **kwargs): return False
            return f(*args, **kwargs)
        return wrapper
        
    @property
    def remain_lifetime(self) -> float:
        if self._lifetime:
            return 1 - CLOCK.timer_get(self.id) / self._lifetime
        else: return 1
    
    @property
    def is_alive(self) -> bool:
        return self._alive


class ActorComponent:
    '''component base class'''
    def __init__(self) -> None:
        # self.owner = owner
        pass
    
    def tick(self, delta_time:float = None):
        return True


class CameraHandler(ActorComponent):
    '''handling actor camera
    should be possesed by engine camera system'''
    def __init__(self) -> None:
        super().__init__()
        self.offset = Vector()
        
        

class CharacterMovement(ActorComponent):
    '''movement component for character'''
    def __init__(self, 
                 body:Sprite, 
                 max_speed = 100, 
                 acceleration = 100, 
                 braking = None, 
                 max_rotation_speed = 360
                 ) -> None:
        super().__init__()
        self.body = body
        self.max_speed = max_speed
        self.max_rotation_speed = max_rotation_speed
        self.acceleration = acceleration
        self.braking = braking if braking is not None else acceleration
    
    def tick(self, delta_time:float = None) -> bool:
        if not super().tick(): return False
        if delta_time is None: delta_time = CLOCK.delta_time
        
    
    def move_forward(self, speed):
        self.body.forward(speed)
        self.velocity
    
    def _get_velocity(self):
        return self.body.velocity
    
    def _set_velocity(self, velocity:Vector = Vector()):
        self.body.velocity = velocity.clamp_length(self.max_speed)
    
    velocity = property(_get_velocity, _set_velocity)
    
    def _get_rotation(self):
        return get_positive_angle(self.body.angle)
    
    def _set_rotation(self, rotation:float):
        self.body.angle = get_positive_angle(rotation)
    
    rotation = property(_get_rotation, _set_rotation)
    
    @property
    def speed(self):
        return Vector(self.body.velocity).length
    

class Actor2D(MObject):
    '''top-down, 위치, 방향, 컬리전을 가지는 객체'''
    def __init__(self, 
                 body:Sprite = None, 
                 **kwargs) -> None:
        super().__init__(**kwargs)
        self.set_body(body)
        """actual body to be rendered. (i.e. pygame.Surface, arcade.Sprite, ...)"""
        
        if 'visibility' in kwargs: visibility = kwargs['visibility']
        else: visibility = True
        self.visibility = visibility
        self.ticker = []
    
    def set_body(self, body:Sprite = None) -> None:
        self.body = body or SpriteCircle()
    
    def register_components(self):
        for k in self.__dict__:
            if isinstance(self.__dict__[k], (ActorComponent, )):
                self.ticker.append(self.__dict__[k])
    
    def spawn(self, 
              position:Vector = Vector(), 
              rotation:float = None, 
              sprite_list:arcade.SpriteList = None, 
              lifetime=0) -> None:
        self.position = position
        self.rotation = rotation
        if sprite_list: self.register_body(sprite_list)
        self.register_components()
        return super().spawn(lifetime)
    
    def tick(self, delta_time:float = None) -> bool:
        if delta_time is None: delta_time = CLOCK.delta_time
        if not super().tick(): return False
        if self.ticker:
            for ticker in self.ticker:
                ticker.tick(delta_time)
        return True
    
    def destroy(self) -> bool:
        self.remove_body()
        return super().destroy()
    
    def _get_position(self) -> Vector:
        return Vector(self.body.position)
    
    def _set_position(self, new_position:Vector = Vector(0., 0.)) -> bool:
        self.body.position = new_position
        return True
    
    def _get_rotation(self) -> float:
        return self.body.angle
    
    def _set_rotation(self, rotation:float = 0.0) -> bool:
        self.body.angle = rotation
        return True
    
    def _get_visibility(self) -> bool:
        return self.body.visible
    
    def _set_visibility(self, switch:bool = None):
        if switch is None: switch = not switch
        self.body.visible = switch
    
    def register_body(self, sprite_list:arcade.SpriteList):
        return sprite_list.append(self.body)
    
    def remove_body(self):
        return self.body.remove_from_sprite_lists()
    
    visibility = property(_get_visibility, _set_visibility)
    position = property(_get_position, _set_position)
    rotation = property(_get_rotation, _set_rotation)


class Pawn2D(Actor2D):
    
    def __init__(self, 
                 body: Sprite = None, 
                 **kwargs) -> None:
        super().__init__(body, **kwargs)
        self.max_velocity = kwargs['max_velocity'] or 100
        self.rotation_speed = kwargs['rotation_speed'] or 90
        self.acceleration = kwargs['acceleration'] or 1
        self.braking = kwargs['braking'] or self.acceleration
        
        '''rotation speed in degrees per second'''
        
    def tick(self, delta_time:float = None) -> bool:
        if not super().tick(): return False
        if delta_time is None: delta_time = CLOCK.delta_time
        if self.velocity < self.max_velocity: self.velocity += self.acceleration
        
    
    def turn_to(self, rotation:float):
        self.rotation = rotation
    
    def turn_left(self, rotation_speed:float = None, delta_time:float = None):
        '''if delta_time is 1, will turn immediately'''
        if delta_time is None: delta_time = CLOCK.delta_time
        if rotation_speed is None: rotation_speed = self.rotation_speed
        
        theta = rotation_speed * delta_time
        return self.body.turn_left(theta)
    

class Character2D(Actor2D):
    
    def __init__(self, body: Sprite = None, hp: float = 100, **kwargs) -> None:
        super().__init__(body, **kwargs)
        self.hp = hp
        self.movement = CharacterMovement(self.body)
        self.camera = CameraHandler()
    
    def tick(self, delta_time: float = None) -> bool:
        if not super().tick(): return False
        
    