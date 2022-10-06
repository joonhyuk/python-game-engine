from __future__ import annotations

from abc import abstractmethod

from ..base import *

from .object import *
from .body import *


class MovementHandler(Handler):
    
    __slots__ = 'body', 'rotation_interp_speed', 'move_direction', 'desired_angle', '_move_modifier', '_turn_modifier'
    
    def __init__(
        self,
        body : BodyHandler,
        rotation_interp_speed:float = 3.0,
        **kwargs,
        ) -> None:
        super().__init__(**kwargs)
        
        self.body = body
        self.rotation_interp_speed = rotation_interp_speed
    
    def setup(self, **kwargs):
        self.move_direction:Vector = None
        ''' direction unit vector for movement '''
        self.desired_angle:float = None
        
        self._move_modifier:float = 1.0
        self._turn_modifier:float = 1.0
        return super().setup(**kwargs)
        
    @property
    def move_lock(self):
        return math.isclose(self._move_modifier, 0.0, abs_tol=0.001)
    
    @property
    def turn_lock(self):
        return math.isclose(self._turn_modifier, 0.0, abs_tol=0.001)
    
    def on_spawn(self):
        self.desired_angle = self.body.angle
        """
        이동에 필요한 것이 없으면 비활성화 시켜야 함.
        """
    
    def tick(self, delta_time:float) -> bool:
        if not self.spawnned : return False
        if not self.alive : return False
        self._set_heading(delta_time)
        self._set_movement(delta_time)
        return True
    
    def _set_movement(self, delta_time:float):
        if not self.move_direction: return False
        if self.move_direction.near_zero():
            ''' stop '''
            if self.body.velocity.is_zero: return False
            if self.body.velocity.near_zero():
                self.body.velocity = vectors.zero
                return False
        if self.move_lock: return False
        
        return self.set_movement(delta_time)
    
    def _set_heading(self, delta_time:float):
        if self.body.angle == self.desired_angle: return False
        if math.isclose(self.body.angle, self.desired_angle):
            self.body.angle = self.desired_angle
            return False
        if self.turn_lock: return False
        
        return self.set_heading(delta_time)
    
    @abstractmethod
    def set_movement(self, delta_time:float):
        ''' overridable method for movement setting '''
        return True
    
    @abstractmethod
    def set_heading(self, delta_time:float):
        ''' overridable or inheritable method for rotation setting '''
        return True
    
    def move_to_position(self, destination:Vector):
        #WIP
        ''' move to position '''
        cur_move_vec = destination - self.body.position
        self.move(cur_move_vec)
    
    def move_toward(self, direction:Vector, speed:float):
        force = direction 
        pass
    
    def move(self, force:Vector):
        self.owner.apply_force(force)
        pass
    
    def move_forward(self):
        # self.move_towa
        pass
    
    def turn(self, angle:float = 0.0):
        self.desired_angle = angle
    
    def turn_by(self, angle_diff:float = 0.0):
        self.desired_angle += angle_diff
    
    def turn_toward(self, direction:Vector = None):
        if not direction: return False
        self.desired_angle = direction.angle
    
    def turn_to_position(self, destination:Vector = None):
        if not destination: return False
        angle = (destination - self.body.position).angle
        self.turn(angle)
        
    def move_toward(self, destination:Vector):
        self.move_to_position(destination)
        self.turn_to_position(destination)
    
    def warp(self, position:Vector, angle:float):
        pass
    