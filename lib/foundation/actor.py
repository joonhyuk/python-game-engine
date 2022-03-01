
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
            for k, v in kwargs:
                setattr(self, k, v)
        
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

    @property
    def remain_lifetime(self) -> float:
        if self._lifetime:
            return 1 - CLOCK.timer_get(self.id) / self._lifetime
        else: return 1
    
    @property
    def is_alive(self) -> bool:
        return self._alive
    
    

class Actor2D(MObject):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        # self._position:Vector = Vector()
        self.direction:float = 0.0
        self.rotation:float = 0.0
        self.body:Sprite = None
        """actual body to be rendered. (i.e. pygame.Surface, arcade.Sprite, ...)"""
    
    def tick(self) -> bool:
        if not super().tick(): return False
        return True
    
    def set_body(self, body:Sprite = None) -> None:
        self.body = body or SpriteCircle()
        # self.body.position = self._position
        self.body.angle = self.rotation
        
    def spawn(self, lifetime=0) -> None:
        return super().spawn(lifetime)
    
    def get_position(self) -> Vector:
        return Vector(self.body.position)
    
    def set_position(self, new_position:Vector) -> bool:
        self.body.position = new_position
        return True
    
    def get_speed(self):
        return Vector(self.body.velocity).norm()
    
    def _set_movement(self, direction:Vector, speed:float):
        self._set_velocity(direction.normalize() * speed)
        pass
    
    def _set_velocity(self, velocity:Vector = Vector(0, 0)):
        self.body.velocity = velocity
    
    position = property(get_position, set_position)