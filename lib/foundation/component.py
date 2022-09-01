from config.engine import *
from lib.foundation.engine import *


class ActionComponent(ActorComponent):
    '''
    Action : custom functions for owner
    '''
    pass


class SpriteBody(BodyComponent):
    
    __slots__ = ()
    def __init__(self, 
                 sprite:Sprite,
                 position:Vector = None,
                 angle:float = None,
                 spawn_to:ObjectLayer = None,
                 **kwargs) -> None:
        super().__init__(sprite, position, angle, **kwargs)
        
        if spawn_to is not None:
            ''' sprite_list는 iter 타입이므로 비어있으면 false를 반환. 따라서 is not none으로 체크 '''
            self.spawn(spawn_to, position, angle)


class StaticBody(BodyComponent):
    
    __slots__ = ('physics', )
    def __init__(self, 
                 sprite:Sprite,
                 position:Vector = None,
                 angle:float = None,
                 spawn_to:ObjectLayer = None,
                 mass = 0,
                 moment = None,
                 body_type = physics_types.static,
                 collision_type = collision.wall,
                 elasticity:float = None,
                 friction:float = 1.0,
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
    
    def get_ref(self):
        return self.physics or self.sprite
    
    def cannot_move(self, *args, **kwargs):
        raise PhysicsException('CAN NOT OVERRIDING POSITION, ANGLE')
    
    def spawn(self, spawn_to: ObjectLayer, position: Vector = None, angle: float = None):
        ### need to sync sprite position when _ref_body is physics
        if position is not None:
            self.sprite.position = position
        if angle is not None:
            self.sprite.angle = angle
        
        return super().spawn(spawn_to, position, angle)

    def draw(self, *args, **kwargs):
        super().draw(*args, **kwargs)
        if CONFIG.debug_draw:
            self.physics.draw()
    
    def _hide(self, switch: bool = None) -> bool:
        #WIP : should revisit filter control
        switch = super()._hide(switch)
        self.physics.shape.filter = physics_types.filter_nomask if switch else physics_types.filter_allmask
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
        
    position:Vector = property(BodyComponent._get_position, _set_position)  
    
    def _set_velocity(self, velocity):
        if not self.physics: self.sprite.velocity = velocity
        else: raise PhysicsException(f'Can\'t move static object by overriding velocity = {velocity}. Set position with StaticActor.')

    velocity: Vector = property(BodyComponent._get_veloticy, _set_velocity)
    
    def _set_angle(self, angle: float):
        if not self.physics: self.sprite.angle = angle
        else: raise PhysicsException(f'Can\'t rotate static object by set angle = {angle}. Set angle with StaticActor.')

    angle:float = property(BodyComponent._get_angle, _set_angle)
    
    # def _get_mass(self):
    #     return self.physics.mass
    
    # def _set_mass(self, mass:float):
    #     self.physics.mass = mass
    
    # mass:float = property(_get_mass, _set_mass)
    mass:float = PropertyFrom('physics')
    
    # def _get_elasticity(self):
    #     return self.physics.elasticity
    
    # def _set_elasticity(self, elasticity:float):
    #     self.physics.elasticity = elasticity
    
    # elasticity:float = property(_get_elasticity, _set_elasticity)
    elasticity:float = PropertyFrom('physics')

    # def _get_friction(self):
    #     return self.physics.friction
    
    # def _set_friction(self, friction:float):
    #     self.physics.friction = friction
    
    # friction:float = property(_get_friction, _set_friction)
    friction:float = PropertyFrom('physics')
    
    def _get_scale(self) -> float:
        return super()._get_scale()
    
    def _set_scale(self, scale: float):
        # self.physics.shape.
        return super()._set_scale(scale)


class DynamicBody(StaticBody):

    __slots__ = ()
    def __init__(self, 
                 sprite: Sprite, 
                 position: Vector = None, 
                 angle: float = None,
                 spawn_to: ObjectLayer = None,
                 mass:float = 1.0,
                 moment = None,
                 body_type:int = physics_types.dynamic,
                 collision_type:int = collision.default,
                 elasticity: float = None,
                 friction: float = 1,
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
        self.movable = True

    def on_register(self):
        self.owner.movable = True
        return super().on_register()
    
    def apply_force_local(self, force:Vector = vectors.zero):
        return self.physics.body.apply_force_at_local_point(force)
    
    def apply_impulse_local(self, impulse:Vector = vectors.zero):
        return self.physics.body.apply_impulse_at_local_point(impulse)
    
    def apply_force_world(self, force:Vector = vectors.zero):
        return self.physics.body.apply_force_at_world_point(force, self.position)
    
    def apply_impulse_world(self, impulse:Vector = vectors.zero):
        return self.physics.body.apply_impulse_at_world_point(impulse, self.position)
    
    def apply_acceleration_world(self, acceleration:Vector):
        self.apply_force_world(acceleration * self.mass)
    
    def apply_force(self, force:Vector):
        self.apply_force_world(force)
    
    def apply_impulse(self, impulse:Vector):
        self.apply_impulse_world(impulse)
    
    def _set_position(self, position) -> None:
        if self.physics:
            self.physics.body.position = position
        self.sprite.position = position
    
    position:Vector = property(BodyComponent._get_position, _set_position)    
    
    def _set_angle(self, angle:float = 0.0):
        if self.physics:
            self.physics.body.angle = math.radians(angle)
        self.sprite.angle = angle

    angle:float = property(BodyComponent._get_angle, _set_angle)
    
    velocity: Vector = property(BodyComponent._get_veloticy, BodyComponent._set_velocity)
    
    def _get_gravity(self):
        return self.sprite.pymunk.gravity
    
    def _set_gravity(self, gravity:Vector):
        self.sprite.pymunk.gravity = gravity
    
    gravity:float = property(_get_gravity, _set_gravity)
    
    def _get_damping(self):
        return self.sprite.pymunk.damping
    
    def _set_damping(self, damping:float):
        self.sprite.pymunk.damping = damping
    
    damping:float = property(_get_damping, _set_damping)
    
    def _get_max_speed(self):
        return self.sprite.pymunk.max_velocity
    
    def _set_max_speed(self, max_speed:int):
        self.sprite.pymunk.max_velocity = max_speed
    
    max_speed:int = property(_get_max_speed, _set_max_speed)


class SpriteMovement(ActorComponent):
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
        return self.speed_tick / ENV.delta_time   # need to be removed
    
    @property
    def speed_tick(self) -> float:
        ''' speed per tick '''
        return self.owner.velocity.length
    
    @property
    def braking(self) -> float:
        if hasattr(self.owner, 'braking_friction'):
            return self._braking * self.owner.braking_friction
        else: return self._braking
    

class MovementHandler(ActorComponent):
    #WIP
    ''' need body component to move '''
    def __init__(self, 
                 max_speed_run:float = 250,
                 max_speed_walk:float = 100,
                 rotation_interp_speed:float = 3.0,
                 acceleration:float = 4,
                 **kwargs) -> None:
        super().__init__(**kwargs)
        
        self.move_direction:Vector = None
        self.desired_angle:float = 0.0
    
    def update(self, delta_time: float) -> bool:
        
        return True
    
    def move(self):
        pass
    
    def rotate(self, angle):
        pass
    
    def warp(self, position):
        pass
    

class PhysicsMovement(ActorComponent):
    ''' movement handler for actor based on pymunk physics engine '''
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.move_direction:Vector = None
        self.desired_angle:float = 0.0
        self.rotation_interp_speed = 3.0
        self.stopped = True
    
    def tick(self, delta_time: float) -> bool:
        if not super().tick(delta_time): return False
        self._set_movement(delta_time)
        self._set_heading(delta_time)
    
    def _set_movement(self, delta_time:float):
        if not self.move_direction: return False
        if self.move_direction.near_zero():
            ''' stop '''
            if self.owner.velocity.is_zero: return False
            if self.owner.velocity.near_zero():
                self.stopped = True
                self.owner.velocity = vectors.zero
        else:
            # self.owner.velocity = self.move_direction * 250
            angle = abs(get_shortest_angle(self.owner.angle, self.owner.velocity.argument()))
            # speed = 1000 * get_curve_value(angle, CONFIG.directional_speed)
            speed = 60 ### damping 0, force 10000 => max_spd 166.6 (1/60)
            '''
            위의 속도는 초당 픽셀. 프레임당 픽셀은 speed / fps
            1초간 감소하는 속도의 양은 1 - damping
            물리 계산하기 귀찮은데 선형 회귀를 써야하나;;;
            speed / (1 - damping)
            '''
            # desired_force = speed / (1- ENV.physics_engine.damping)
            # print(desired_force)
            
            if self.stopped:
                ''' 정지 상태에서 가속 '''
                schedule_once(self._foo_print, 1)
            
            self.owner.body.apply_force_world(self.move_direction * 1000)
            self.stopped = False
    
    def _foo_print(self, t):
        print(self.owner.speed)
    
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
    

class PlayerController(Controller):
    #WIP
    '''  '''
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
    
    def tick(self, delta_time: float) -> bool:
        if not super().tick(delta_time): return False
        direction = ENV.direction_input
        if direction: self.owner.movement.turn_toward(direction)
        self.movement.move(ENV.move_input)
        ENV.debug_text['player_speed'] = round(self.speed, 1)
    
    def on_key_press(self, key: int, modifiers: int):
        pass
    
    def on_key_release(self, key: int, modifiers: int):
        pass
    
    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int):
        pass
    
    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        pass
    
    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int):
        pass
    
    def on_mouse_drag(self, x: int, y: int, dx: int, dy: int, buttons: int, modifiers: int):
        pass
    
    def on_mouse_scroll(self, x: int, y: int, scroll_x: int, scroll_y: int):
        pass
    