"""
Base actors, aka game objects

"""
from __future__ import annotations

import math, functools
from config.engine import *

from .engine import *
from .component import *


class BodyObject(Actor):
    def __init__(self, 
                 body:BodyHandler,
                 **kwargs) -> None:
        super().__init__(**kwargs)
        self.body:BodyHandler = body
    
    def spawn(self, 
              spawn_to:ObjectLayer, 
              position:Vector = None,
              angle:float = None,
              lifetime: float = None) -> None:
        if position is not None:
            self.body.position = position
        if angle is not None:
            self.body.angle = angle
        return super().spawn()

    def register_components(self):
        self.body.owner = self
        self.tick_components.append(self.body.tick)
        self.body.on_register()
        # return super().register_components()
    
    position:Vector = PropertyFrom('body')
    angle:float = PropertyFrom('body')


class StaticObject(Actor):
    ''' Actor with simple sprite '''
    __slots__ = ('body', )
    
    def __init__(self, body:StaticBody, **kwargs) -> None:
        super().__init__(**kwargs)
        self.body:StaticBody = body
    
    def spawn(self, spawn_to:ObjectLayer, position:Vector = None, angle:float = None):
        self.body.set_spawn(spawn_to=spawn_to)
        ''' simple workaround for static objects '''
        if position is not None : self.position = position
        if angle is not None : self.angle = angle
        return super().spawn()

    def draw(self):
        self.body.draw()
    
    position:Vector = PropertyFrom('body')
    angle:float = PropertyFrom('body')
    friction:float = PropertyFrom('body')
    elasticity:float = PropertyFrom('body')
    

class DynamicObject(Actor):
    
    __slots__ = 'body', 
    
    def __init__(self, 
                 body:Union[DynamicBody, KinematicBody],
                 **kwargs) -> None:
        super().__init__(**kwargs)
        self.body:Union[DynamicBody, KinematicBody] = body
    
    def spawn(self, 
              spawn_to:ObjectLayer, 
              position:Vector = None,
              angle:float = None,
              initial_impulse:Vector = None,
              ) -> None:
        # if not position:
        #     position = self.body.position
        
        # self.body.spawn(spawn_to, position, angle)
        self.body.set_spawn(spawn_to=spawn_to, position=position, angle=angle)
        super().spawn()
        if initial_impulse:
            self.body.apply_impulse_world(initial_impulse)
        
        return self
    
    def draw(self):
        self.body.draw()
    
    mass:float = PropertyFrom('body')
    friction:float = PropertyFrom('body')
    elasticity:float = PropertyFrom('body')
    visibility:bool = PropertyFrom('body')
    position:Vector = PropertyFrom('body')
    angle:float = PropertyFrom('body')
    velocity:Vector = PropertyFrom('body')
    speed:float = PropertyFrom('body')
    
    @property
    def screen_position(self) -> Vector:
        ''' relative position in viewport '''
        return self.position - GAME.abs_screen_center + CONFIG.screen_size / 2
    
    @property
    def forward_vector(self) -> Vector:
        return self.body.forward_vector

    @property
    def speed(self) -> float:
        return self.body.speed
        

class KinematicObject(DynamicObject):
    def __init__(self, body: KinematicBody, **kwargs) -> None:
        super().__init__(body, **kwargs)


class Projectile(DynamicBody):
    
    def __init__(self, 
                 sprite: Sprite, 
                 position: Vector = None, 
                 angle: float = None, 
                 spawn_to: ObjectLayer = None, 
                 mass: float = 1,
                 collision_type: int = collision.projectile, 
                 elasticity: float = None, 
                 friction: float = 1, 
                 shape_edge_radius: float = 0, 
                 physics_shape: Union[physics_types.shape, type] = ..., 
                 offset_circle: Vector = ..., 
                 custom_gravity: Vector = vectors.zero, 
                 custom_damping: float = 0.0, 
                 **kwargs) -> None:
        super().__init__(sprite, 
                         position,
                         angle,
                         spawn_to,
                         mass,
                         None,
                         collision_type = collision_type, 
                         elasticity=elasticity, 
                         friction=friction, 
                         shape_edge_radius=shape_edge_radius,
                         physics_shape=physics_shape,
                         offset_circle=offset_circle,
                         max_speed = CONFIG.terminal_speed,
                         custom_gravity = custom_gravity,
                         custom_damping = custom_damping,
                         **kwargs)
    
    def spawn(self, spawn_to: ObjectLayer, position: Vector = None, angle: float = None):
        return super().spawn(spawn_to, position, angle)


class Pawn(DynamicObject):
    
    __slots__ = 'hp',  
    
    def __init__(self, 
                 body: DynamicBody, 
                 hp:float = 100,
                 **kwargs) -> None:
        super().__init__(body, **kwargs)
        self.hp = hp
        # self.movement = TopDownPhysicsMovement(body = self.body)
    
    def apply_damage(self, damage:float):
        self.hp -= damage
        if not self.alive: return self.die()
        
    def die(self):
        return self.destroy()
    
    @property
    def _is_alive(self) -> bool:
        if self.hp <=0: return False
        return super()._is_alive


class Character(Pawn):
    
    __slots__ = 'controller', 
    
    def __init__(self, body: DynamicBody, hp: float = 100, **kwargs) -> None:
        super().__init__(body, hp, **kwargs)
        
        self.controller:Controller = None
        
    # def tick(self, delta_time: float = None) -> bool:
    #     if not super().tick(delta_time): return False
    #     direction = ENV.direction_input
    #     if direction: self.movement.turn_toward(direction)
    #     self.movement.move(ENV.move_input)
    #     ENV.debug_text['player_speed'] = round(self.speed, 1)
    #     return True


