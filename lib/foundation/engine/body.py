from __future__ import annotations

from ..physics import *
from .object import *
from .primitive import *


class Body(GameObject):
    
    """
    Base class of 'body'. Combined with transform component/
    """
    
    counter_created = 0 ### for debug. total created
    counter_removed = 0 ### for debug. total destroyed
    counter_gced = 0 ### for debug. total garbage collected

    __slots__ = 'sprite', '_hidden', '_last_spawn_layer'
    
    def __init__(self, 
                 sprite:Sprite,
                 position:Vector = None,
                 angle:float = None,
                 **kwargs) -> None:
        super().__init__(**kwargs)
        Body.counter_created += 1 ### for debug
        
        self.sprite:Sprite = sprite
        self._hidden:bool = False
        self._last_spawn_layer:Layer = None
        
        if position: self.position = position
        if angle: self.angle = angle
    
    def _get_ref(self):
        return self.sprite
    
    def __del__(self):
        Body.counter_gced += 1
    
    def set_spawn(self, spawn_to:Layer = None, position:Vector = None, angle:float = None) -> None:
        if spawn_to is not None:
            self._last_spawn_layer = spawn_to
        if position is not None: 
            self.position = position
        if angle is not None:
            self.angle = angle
        
        if self._last_spawn_layer is None :
            raise Exception(f'Spawn layer of {self} is None')
    
    def spawn(self, spawn_to:Layer = None, position:Vector = None, angle:float = None):
        # self.sprite.owner = self.owner  ### will be removed after Sprite converted to GameObject
        self.set_spawn(spawn_to=spawn_to, position=position, angle=angle)
        # spawn_to.add(self)
        return super().spawn()
    
    def on_spawn(self) -> None:
        self._last_spawn_layer.add(self)
    
    def draw(self, *args, **kwargs):
        self.sprite.draw(*args, **kwargs)
    
    def _hide(self, switch:bool = None) -> bool:
        ''' hide sprite and physics if exist and return switch '''
        if switch is None: switch = not self.hidden
        self.visibility = not switch
        return switch
    
    def _get_hidden(self) -> bool:
        return self._hidden
    
    def _set_hidden(self, switch:bool = None):
        ''' hide sprite and physics body '''
        self._hidden = self._hide(switch)
    
    hidden:bool = property(_get_hidden, _set_hidden)
    
    def destroy(self) -> bool:
        Body.counter_removed += 1
        self.sprite.remove_from_sprite_lists()
        return super().destroy()
    
    def _get_visibility(self) -> bool:
        return self.sprite.visible
    
    def _set_visibility(self, switch:bool = None):
        if switch is None: switch = not self.sprite.visible
        self.sprite.visible = switch
    
    visibility:bool = property(_get_visibility, _set_visibility)
    ''' set None to toggle visibility '''
    
    def _get_position(self):
        return self._get_ref().position
    
    def _set_position(self, position):
        self._get_ref().position = position
    
    position:Vector = property(_get_position, _set_position)
    
    def _get_angle(self) -> float:
        return self._get_ref().angle
    
    def _set_angle(self, angle:float = 0.0):
        self._get_ref().angle = angle
    
    angle:float = property(_get_angle, _set_angle)
    
    def _get_veloticy(self) -> Vector:
        return self._get_ref().velocity
    
    def _set_velocity(self, velocity):
        self._get_ref().velocity = velocity
    
    velocity:Vector = property(_get_veloticy, _set_velocity)
    
    def _get_scale(self) -> float:
        return self.sprite.relative_scale
    
    def _set_scale(self, scale:float):
        self.sprite.relative_scale = scale
    
    scale = property(_get_scale, _set_scale)
    
    @property
    def speed(self) -> float :
        ''' different according to physics or sprite 
        
        :physics = per sec
        :sprite = per tick
        '''
        return self.velocity.length
    
    @property
    def forward_vector(self) -> Vector:
        return Vector.directional(self.angle)
    
    @property
    def size(self) -> Vector:
        return Vector(self.sprite.width, self.sprite.height)
    
    @property
    def layers(self) -> list[Layer]:
        ''' Layers(ObjectLayer list) where this body is '''
        return self.sprite.sprite_lists


class SpriteBody(Body):
    
    __slots__ = ()

    def __init__(self, 
                 sprite:Sprite,
                 position:Vector = None,
                 angle:float = None,
                 spawn_to:Layer = None,
                 **kwargs) -> None:
        super().__init__(sprite, position, angle, **kwargs)
        
        if spawn_to is not None:
            ''' sprite_list는 iter 타입이므로 비어있으면 false를 반환. 따라서 is not none으로 체크 '''
            self.spawn(spawn_to, position, angle)


class PhysicsBody(Body):
    
    __slots__ = ('physics', )

    def __init__(self, 
                 sprite:Sprite,
                 position:Vector = None,
                 angle:float = None,
                 spawn_to:Layer = None,
                 mass = 0,
                 moment = None,
                 body_type = physics_types.static,
                 collision_type = collision.wall,
                 elasticity:float = None,
                 friction:float = 0.7,
                 shape_edge_radius:float = 0.0,
                 physics_shape:Union[physics_types.shape, type] = physics_types.poly,
                 offset_circle:Vector = vectors.zero,
                 max_speed:float = None,
                 custom_gravity:Vector = None,
                 custom_damping:float = None,
                 **kwargs) -> None:

        self.physics:PhysicsObject = None
        super().__init__(sprite, position, angle, **kwargs)
        
        self.physics = setup_physics_object(sprite=sprite,
                                            mass=mass,
                                            moment=moment,
                                            friction=friction,
                                            elasticity=elasticity,
                                            body_type=body_type,
                                            collision_type=collision_type,
                                            physics_shape=physics_shape,
                                            shape_edge_radius=shape_edge_radius,
                                            offset_circle=offset_circle,
                                            max_speed=max_speed,
                                            custom_gravity=custom_gravity,
                                            custom_damping=custom_damping,
                                            )
        
        self.physics._scale = self.sprite.scale
        ### not working...
        # if body_type == physics_types.static:
        #     self._set_position = self.cannot_move
        #     self._set_angle = self.cannot_move
        
        if spawn_to is not None:
            ''' sprite_list는 iter 타입이므로 비어있으면 false를 반환. 따라서 is not none으로 체크 '''
            self.spawn(spawn_to)
    
    def _get_ref(self):
        return self.physics or self.sprite
    
    def cannot_move(self, *args, **kwargs):
        raise PhysicsException('CAN NOT OVERRIDING POSITION, ANGLE')
    
    # def spawn(self, spawn_to: Layer, position: Vector = None, angle: float = None):
    #     ### need to sync sprite position when _ref_body is physics
    #     if position is not None:
    #         self.sprite.position = position
    #     if angle is not None:
    #         self.sprite.angle = angle
        
    #     return super().spawn(spawn_to, position, angle)

    # def draw(self, *args, **kwargs):
        # super().draw(*args, **kwargs)
        # if CONFIG.debug_draw:
            # self.physics.draw()
    
    def _hide(self, switch: bool = None) -> bool:
        #WIP : should revisit filter control
        switch = super()._hide(switch)
        # self.physics.filter = physics_types.filter_nomask if switch else physics_types.filter_allmask
        self.physics.hidden = switch
        print('hide me!',switch)
        return switch
    
    def _get_scale(self) -> float:
        return self.physics._scale
    
    def _set_scale(self, scale: float):
        self.physics.scale = scale
        return super()._set_scale(scale)
    
    scale = property(_get_scale, _set_scale)
    
    def _set_position(self, position) -> None:
        if not self.physics: self.sprite.position = position
        else: raise PhysicsException(f'Can\'t move static object by overriding position = {position}. Set position with StaticActor.')
        
    position:Vector = property(Body._get_position, _set_position)  
    
    def _set_velocity(self, velocity):
        if not self.physics: self.sprite.velocity = velocity
        else: raise PhysicsException(f'Can\'t move static object by overriding velocity = {velocity}. Set position with StaticActor.')

    velocity: Vector = property(Body._get_veloticy, _set_velocity)
    
    def _set_angle(self, angle: float):
        if not self.physics: self.sprite.angle = angle
        else: raise PhysicsException(f'Can\'t rotate static object by set angle = {angle}. Set angle with StaticActor.')

    angle:float = property(Body._get_angle, _set_angle)
    
    mass:float = PropertyFrom('physics')
    
    elasticity:float = PropertyFrom('physics')

    friction:float = PropertyFrom('physics')
    
    @property
    def is_movable_physics(self) -> bool:
        return isinstance(self, DynamicBody)


class DynamicBody(PhysicsBody):

    __slots__ = ()

    def __init__(self, 
                 sprite: Sprite, 
                 position: Vector = None, 
                 angle: float = None,
                 spawn_to: Layer = None,
                 mass:float = 1.0,
                 moment = None,
                 body_type:int = physics_types.dynamic,
                 collision_type:int = collision.default,
                 elasticity: float = None,
                 friction: float = 0.5,
                 shape_edge_radius: float = 0,
                 physics_shape: Union[physics_types.shape, type] = physics_types.circle,
                 offset_circle: Vector = vectors.zero,
                 max_speed:float = None,
                 custom_gravity:Vector = None,
                 custom_damping:float = None,
                 **kwargs) -> None:
        
        super().__init__(sprite=sprite,
                         position=position,
                         angle=angle,
                         spawn_to=spawn_to,
                         mass=mass,
                         moment=moment,
                         body_type=body_type,
                         collision_type=collision_type,
                         elasticity=elasticity,
                         friction=friction,
                         shape_edge_radius=shape_edge_radius,
                         physics_shape=physics_shape,
                         offset_circle=offset_circle,
                         max_speed=max_speed,
                         custom_gravity=custom_gravity,
                         custom_damping=custom_damping,
                         **kwargs)
    
    def apply_force_local(self, force:Vector = vectors.zero):
        return self.physics._body.apply_force_at_local_point(force)
    
    def apply_impulse_local(self, impulse:Vector = vectors.zero):
        return self.physics._body.apply_impulse_at_local_point(impulse)
    
    def apply_force_world(self, force:Vector = vectors.zero):
        return self.physics._body.apply_force_at_world_point(force, self.position)
    
    def apply_impulse_world(self, impulse:Vector = vectors.zero):
        return self.physics._body.apply_impulse_at_world_point(impulse, self.position)
    
    def apply_acceleration_world(self, acceleration:Vector):
        self.apply_force_world(acceleration * self.mass)
    
    def apply_force(self, force:Vector):
        self.apply_force_world(force)
    
    def apply_impulse(self, impulse:Vector):
        self.apply_impulse_world(impulse)
    
    def _set_position(self, position) -> None:
        if self.physics:
            self.physics._body.position = position
        self.sprite.position = position
    
    position:Vector = property(Body._get_position, _set_position)    
    
    def _set_angle(self, angle:float = 0.0):
        if self.physics:
            self.physics._body.angle = math.radians(angle)
        self.sprite.angle = angle

    angle:float = property(Body._get_angle, _set_angle)
    
    velocity: Vector = property(Body._get_veloticy, Body._set_velocity)
    
    def _get_gravity(self):
        return self.sprite.pymunk.gravity or self.physics._body.space.gravity
    
    def _set_gravity(self, gravity:Vector):
        self.sprite.pymunk.gravity = gravity
    
    gravity:float = property(_get_gravity, _set_gravity)
    
    def _get_damping(self):
        return self.sprite.pymunk.damping or self.physics._body.space.damping
    
    def _set_damping(self, damping:float = None):
        self.sprite.pymunk.damping = damping
    
    damping:float = property(_get_damping, _set_damping)
    
    def _get_max_speed(self):
        return self.sprite.pymunk.max_velocity
    
    def _set_max_speed(self, max_speed:int):
        self.sprite.pymunk.max_velocity = max_speed
    
    max_speed:int = property(_get_max_speed, _set_max_speed)


class KinematicBody(DynamicBody):
    
    __slots__ = ()
    
    def __init__(self, 
                 sprite: Sprite,
                 position: Vector = None,
                 angle: float = None, 
                 spawn_to: Layer = None,
                 mass=0, moment=None,
                 body_type=physics_types.kinematic, 
                 collision_type=collision.wall,
                 elasticity: float = None, 
                 friction: float = 0.7, 
                 shape_edge_radius: float = 0,
                 physics_shape: Union[physics_types.shape, type] = physics_types.poly,
                 offset_circle: Vector = vectors.zero, max_speed: float = None,
                 custom_gravity: Vector = None,
                 custom_damping: float = None,
                 **kwargs) -> None:
        super().__init__(sprite, position, angle, spawn_to, mass, moment, body_type, collision_type, elasticity, friction, shape_edge_radius, physics_shape, offset_circle, max_speed, custom_gravity, custom_damping, **kwargs)
    
    def apply_force_local(self, force:Vector = vectors.zero):
        pass
    
    def apply_impulse_local(self, impulse:Vector = vectors.zero):
        pass
    
    def apply_force_world(self, force:Vector = vectors.zero):
        pass
    
    def apply_impulse_world(self, impulse:Vector = vectors.zero):
        pass
    
    def apply_acceleration_world(self, acceleration:Vector):
        pass
    
    def apply_force(self, force:Vector):
        pass
    
    def apply_impulse(self, impulse:Vector):
        pass
    
    velocity: Vector = property(Body._get_veloticy, Body._set_velocity)
