"""
Base actors, aka game objects

"""
from __future__ import annotations

import math, functools
from config.engine import *

from lib.foundation.engine import *
from lib.foundation.component import *


class BodyObject(Actor):
    def __init__(self, 
                 body:Body,
                 **kwargs) -> None:
        super().__init__(**kwargs)
        self.body:Body = body
    
    def spawn(self, 
              spawn_to:ObjectLayer, 
              position:Vector = None,
              angle:float = None,
              lifetime: float = None) -> None:
        
        self.body.spawn(spawn_to, position, angle)
        return super().spawn(lifetime)

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
        self.body.owner = self
        if position is not None: self.position = position
        if angle is not None: self.angle = angle
        self.body.spawn(spawn_to)
        return super().spawn()

    def draw(self):
        self.body.draw()
    
    def _get_position(self) -> Vector:
        return self.body.position
    
    def _set_position(self, position) -> None:
        self.body.sprite.position = position
        self.body.physics.position = position
        if self._spawned: self.body.physics.space.reindex_static()    #BUG : when spawn, not yet added to space
        
    position:Vector = property(_get_position, _set_position)
    
    def _get_angle(self) -> float:
        return self.body.angle
    
    def _set_angle(self, angle:float = 0.0):
        self.body.sprite.angle = angle
        self.body.physics.angle = angle
        if self._spawned: self.body.physics.space.reindex_static()    #BUG : when spawn, not yet added to space
    
    angle:float = property(_get_angle, _set_angle)


class DynamicObject(Actor):
    
    # __slots__ = ('body', 'apply_force', 'apply_impulse')
    def __init__(self, 
                 body:DynamicBody,
                 **kwargs) -> None:
        super().__init__(**kwargs)
        self.body:DynamicBody = body
        self.movable = True
        self.apply_force = self.body.apply_force_world
        self.apply_impulse = self.body.apply_impulse_world
    
    def spawn(self, 
              spawn_to:ObjectLayer, 
              position:Vector = None,
              angle:float = None,
              initial_impulse:Vector = None,
              lifetime: float = None) -> None:
        if not position:
            position = self.body.position
        
        self.body.spawn(spawn_to, position, angle)
        if initial_impulse:
            self.body.apply_impulse_world(initial_impulse)
        return super().spawn(lifetime)
    
    # def draw(self):
    #     # self.body.draw()
    #     pass    ### delegate draw to body. 
    
    mass:float = PropertyFrom('body')
    friction:float = PropertyFrom('body')
    elasticity:float = PropertyFrom('body')
    
    # def _get_visibility(self) -> bool:
    #     return self.body.visibility
    
    # def _set_visibility(self, switch:bool):
    #     self.body.visibility = switch
    
    # visibility:bool = property(_get_visibility, _set_visibility)
    visibility:bool = PropertyFrom('body')
    
    # def _get_position(self) -> Vector:
    #     return self.body.position
    
    # def _set_position(self, position) -> None:
    #     self.body.position = position
    
    # position:Vector = property(_get_position, _set_position)
    position:Vector = PropertyFrom('body')
    
    # def _get_angle(self) -> float:
    #     return self.body.angle
    
    # def _set_angle(self, angle:float):
    #     self.body.angle = angle
    
    # angle:float = property(_get_angle, _set_angle)
    angle:float = PropertyFrom('body')
    
    # def _get_velocity(self) -> Vector:
    #     return self.body.velocity
    
    # def _set_velocity(self, velocity):
    #     self.body.velocity = velocity
    
    # velocity:Vector = property(_get_velocity, _set_velocity)
    velocity:Vector = PropertyFrom('body')
    
    @property
    def screen_position(self) -> Vector:
        ''' relative position in viewport '''
        return self.position - ENV.abs_screen_center + CONFIG.screen_size / 2
    
    @property
    def forward_vector(self) -> Vector:
        return self.body.forward_vector

    @property
    def speed(self) -> float:
        return self.body.speed
        

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
                 owner: ... = None,
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
        self.owner = None
    
    def spawn(self, spawn_to: ObjectLayer, position: Vector = None, angle: float = None):
        return super().spawn(spawn_to, position, angle)


class AIController(ActorComponent):
    
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
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
        self.others:list[Actor] = []
        
    def begin_overlap(self, other:Actor):
        self.others.append(other)
    
    def end_overlap(self, other:Actor):
        self.others.remove(other)
    

class CameraHandler(ActorComponent):
    '''handling actor camera
    should be possesed by engine camera system'''
    
    def __init__(self,
                 offset:Vector = vectors.zero,
                 interp_speed:float = 0.05,
                 boom_length:float = 200,
                 dynamic_boom:bool = True,
                 max_lag_distance:float = 300,
                 ) -> None:
        super().__init__()
        self._spawned = False
        self.offset:Vector = offset
        self.camera = Camera(*CONFIG.screen_size, max_lag_distance=max_lag_distance)
        self.camera_interp_speed = interp_speed
        self.boom_length = boom_length
        self.dynamic_boom = dynamic_boom
        self.max_lag_distance = max_lag_distance
        self.owner_has_position = True
    
    def on_spawn(self):
        if not hasattr(self.owner, 'position'):
            self.owner_has_position = True
            self.set_update(False)  # failsafe, will be removed
    
    def tick(self, delta_time: float) -> bool:
        if not super().tick(delta_time): return False
        # ENV.debug_text.perf_check('update_camera')
        self.center = self.owner.position
        
        ENV.abs_screen_center = self.center # not cool...
        self._spawned = False
        # print('camera_tick')
        # ENV.debug_text.perf_check('update_camera')
        

    def use(self):
        self._spawned = True
        self.camera.use()
    
    def _get_center(self) -> Vector:
        return self.camera.position + CONFIG.screen_size / 2
    
    def _set_center(self, new_center:Vector = Vector()):
        # cam_accel = map_range(self.owner.speed, 500, 1000, 1, 3, True)
        self.camera.move_to(new_center - CONFIG.screen_size / 2 + self.offset + self._get_boom_vector(), self.camera_interp_speed)
    
    center:Vector = property(_get_center, _set_center)
    
    def _get_boom_vector(self) -> Vector:
        if not self.owner_has_position: return vectors.zero
        if not self.dynamic_boom: return self.owner.forward_vector.unit * self.boom_length
        # distv = ENV.cursor_position - ENV.scren_center
        distv = self.owner.position - ENV.abs_cursor_position
        # print(self.owner.rel_position, ENV.cursor_position)
        # return Vector()
        alpha = map_range(self.owner.speed, 500, 1000, 1, 0, clamped = True)
        
        in_min = ENV.window_shortside // 5
        in_max = ENV.window_shortside // 1.2
        ''' 최적화 필요 need optimization '''
        return self.owner.forward_vector.unit * self.boom_length * map_range(distv.length, in_min, in_max, 0, 1, clamped=True) * alpha


class Pawn(DynamicObject):
    
    # __slots__ = ('hp', 'movement', )
    
    def __init__(self, 
                 body: DynamicBody, 
                 hp:float = 100,
                 **kwargs) -> None:
        super().__init__(body, **kwargs)
        self.hp = hp
        self.movement = PhysicsMovement()
    
    def apply_damage(self, damage:float):
        self.hp -= damage
        if not self.is_alive: self.die()
        
    def die(self):
        self.destroy()
    
    @property
    def is_alive(self) -> bool:
        if self.hp <=0: return False
        return super().is_alive


class Character(Pawn):
    
    # __slots__ = ('camera', )
    
    def __init__(self, body: DynamicBody, hp: float = 100, **kwargs) -> None:
        super().__init__(body, hp, **kwargs)
        
        self.camera = CameraHandler()
        self.controller:PawnController = None
        
    # def tick(self, delta_time: float = None) -> bool:
    #     if not super().tick(delta_time): return False
    #     direction = ENV.direction_input
    #     if direction: self.movement.turn_toward(direction)
    #     self.movement.move(ENV.move_input)
    #     ENV.debug_text['player_speed'] = round(self.speed, 1)
    #     return True


