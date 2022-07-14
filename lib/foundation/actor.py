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
        return False

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

class Actor2D(MObject):
    '''위치, 방향, 컬리전을 가지는 객체'''
    def __init__(self, 
                 body:Sprite = None, 
                 **kwargs) -> None:
        super().__init__(**kwargs)
        self.set_body(body)
        """actual body to be rendered. (i.e. pygame.Surface, arcade.Sprite, ...)"""
    
    def set_body(self, body:Sprite = None) -> None:
        self.body = body or SpriteCircle()
        
    def spawn(self, 
              position:Vector = None, 
              rotation:float = None, 
              sprite_list:arcade.SpriteList = None, 
              lifetime=0) -> None:
        self.position = position
        self.rotation = rotation
        self.register(sprite_list)
        return super().spawn(lifetime)
    
    def _get_position(self) -> Vector:
        return Vector(self.body.position)
    
    def _set_position(self, new_position:Vector = Vector(0., 0.)) -> bool:
        self.body.position = new_position
        return True
    
    def _get_rotation(self) -> float:
        return self.body.angle
    
    def _set_rotation(self, new_rotation:float = 0.0) -> bool:
        self.body.angle = new_rotation
        return True
    
    def register(self, sprite_list:arcade.SpriteList):
        return sprite_list.append(self.body)
    
    def remove(self):
        return self.body.remove_from_sprite_lists()
    
    # def _set_movement(self, direction:Vector, speed:float):
    #     self._set_velocity(direction.normalize() * speed)
    #     pass
    
    # def _set_velocity(self, velocity:Vector = Vector(0, 0)):
    #     self.body.velocity = velocity
    
    # # def on_update(self, delta_time: float = 1 / 60):
    # #     self.tick()
    # #     return super().on_update(delta_time)
    
    position = property(_get_position, _set_position)
    rotation = property(_get_rotation, _set_rotation)

class Pawn2D(Actor2D):
    
    def __init__(self, 
                 body: Sprite = None, 
                 hp:float = 100,
                 **kwargs) -> None:
        super().__init__(body, **kwargs)
        self.hp = hp
        self.rotation_speed = kwargs['rotation_speed'] or 90
        self.acceleration = kwargs['acceleration'] or 1
        
        
        '''rotation speed in degrees per second'''
    
    def turn_to(self, rotation:float):
        self.rotation = rotation
    
    def turn_left(self, rotation_speed:float = None, delta_time:float = None):
        '''if delta_time is 1, will turn immediately'''
        if delta_time is None: delta_time = CLOCK.delta_time
        if rotation_speed is None: rotation_speed = self.rotation_speed
        
        theta = rotation_speed * delta_time
        return self.body.turn_left(theta)
    
    def _get_velocity(self):
        return self.body.velocity
    
    def _set_velocity(self):
        self.body.velocity
    
    def on_dead(self):
        pass
    
