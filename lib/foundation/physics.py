'''
physics engine based on pymunk, 
very simple physics code injection by mash

may be coupled with pymunk
'''
import sys
from typing import Callable, Optional, Union
from enum import Enum

### for in-house physics engine
import pymunk, math
from .vector import Vector
from config.engine import *

from .utils import debug_draw_poly
### for in-house physics engine

### for code injection of simple physics engine
# will be deprecated after moved to pymunk
import arcade
from arcade import (Point, 
                    PointList, 
                    is_point_in_polygon, 
                    get_distance, 
                    Sprite, 
                    are_polygons_intersecting
                    )
### for code injection of simple physics engine

def is_polygon_intersecting_with_circle(poly: PointList, p: Point, radius: float):  ### function added to arcade simple physics engine
    ''' for legacy simple physics engine '''
    if is_point_in_polygon(*p, poly): return True   # 중심이 안에 있으면 충돌
    
    for i in range(-len(poly), 0):
        if get_distance(*poly[i], *p) <= radius: return True    # 모서리 충돌
        
        p1 = poly[i]
        p2 = poly[i + 1]

        # v12 = (p2[0] - p1[0], p2[1] - p1[1])
        # v21 = (p1[0] - p2[0], p1[1] - p2[1])
        # v1 = (p[0] - p1[0], p[1] - p1[1])
        # v2 = (p[0] - p2[0], p[1] - p2[1])

        # def dot(a:tuple, b:tuple):
        #     return sum(i * j for i, j in zip(a, b))
        
        dot1 = (p2[0] - p1[0]) * (p[0] - p1[0]) + (p2[1] - p1[1]) * (p[1] - p1[1]) >= 0
        dot2 = (p2[0] - p1[0]) * (p[0] - p2[0]) + (p2[1] - p1[1]) * (p[1] - p2[1]) < 0
        
        # if dot(v12, v1) >=0 and dot(v21, v2) >=0:
        if dot1 and dot2:
            projection = ((p2[0] - p1[0]) * (p1[1] - p[1]) - (p1[0] - p[0]) * (p2[1] - p1[1])) / get_distance(*p1, *p2)
        
        # if 0 < projection <= d12:
            if abs(projection) <= radius:
                # print('sides check [colliding]')
                return True
            # print('sides check [not colliding]')
            
        # if projection <= radius: 
        #     print(p, p1, p2, d12, projection)
        #     return True
        
    
    return False

def is_sprite_intersecting_with_line(start:tuple, end:tuple, sprite:arcade.Sprite):
    
    pass

def _check_for_collision(sprite1: Sprite, sprite2: Sprite) -> bool:
    """
    Check for collision between two sprites.

    :param Sprite sprite1: Sprite 1
    :param Sprite sprite2: Sprite 2

    :returns: True if sprites overlap.
    :rtype: bool
    """
    collision_radius_sum = sprite1.collision_radius + sprite2.collision_radius

    diff_x = sprite1.position[0] - sprite2.position[0]
    diff_x2 = diff_x * diff_x

    if diff_x2 > collision_radius_sum * collision_radius_sum:
        return False

    diff_y = sprite1.position[1] - sprite2.position[1]
    diff_y2 = diff_y * diff_y
    if diff_y2 > collision_radius_sum * collision_radius_sum:
        return False

    distance = diff_x2 + diff_y2
    if distance > collision_radius_sum * collision_radius_sum:
        return False

    ### mash custom starts
    if getattr(sprite1, 'collides_with_radius', False):
        if getattr(sprite2, 'collides_with_radius', False):
            # print('collision case 0')
            return True
        else:
            # print('collision case 1')
            return is_polygon_intersecting_with_circle(sprite2.get_adjusted_hit_box(), sprite1.position, sprite1.collision_radius)
    else:
        if getattr(sprite2, 'collides_with_radius', False):
            # print('collision case 2')
            return is_polygon_intersecting_with_circle(sprite1.get_adjusted_hit_box(), sprite2.position, sprite2.collision_radius)
    ### mash custom ends
    
    return are_polygons_intersecting(
        sprite1.get_adjusted_hit_box(), sprite2.get_adjusted_hit_box()
    )

### code injection
arcade.sprite_list.spatial_hash._check_for_collision = _check_for_collision


@dataclass
class physics_types:
    __slots__ = ()
    ''' 그닥 필요는 없지만 '''
    
    fps_base = 60
    delta_time = 1 / fps_base
    
    space = pymunk.Space
    
    body = pymunk.Body
    shape = pymunk.Shape
    
    segment = pymunk.Segment
    box = pymunk.Poly
    circle = pymunk.Circle
    poly = pymunk.Poly
    
    static = pymunk.Body.STATIC
    dynamic = pymunk.Body.DYNAMIC
    kinematic = pymunk.Body.KINEMATIC
    
    infinite:float = float('inf')
    allmask:int = pymunk.ShapeFilter.ALL_MASKS()
    allcategories:int = pymunk.ShapeFilter.ALL_CATEGORIES()
    filter_nomask = pymunk.ShapeFilter(mask = 0)
    filter_allmask = pymunk.ShapeFilter(mask = allmask)
    filter_allcategories = pymunk.ShapeFilter(mask = allcategories)


def setup_physics_object(sprite:Sprite, 
                         mass:float = 0,
                         moment = None,
                         friction:float = 1.0,
                         elasticity:float = None,
                         body_type:int = physics_types.static,
                         collision_type = collision.default,
                         physics_shape = physics_types.poly,
                         shape_edge_radius:float = 0.0,
                         offset_circle:Vector = vectors.zero,
                         max_speed:float = None,
                         custom_gravity:Vector = None,
                         custom_damping:float = None,
                         ):
    
    size = Vector(sprite.width, sprite.height)
    
    if body_type == physics_types.static:
        _moment = physics_types.infinite
    else:
        if physics_shape == physics_types.circle or isinstance(physics_shape, physics_types.circle):
            _moment = pymunk.moment_for_circle(mass, 0, 
                                                min(size.x, size.y) / 2 + shape_edge_radius, 
                                                offset_circle)
        elif physics_shape == physics_types.box or isinstance(physics_shape, physics_types.box):
            _moment = pymunk.moment_for_box(mass, size)
        else:
            scaled_poly = [[x * sprite.scale for x in z] for z in sprite.get_hit_box()]
            _moment = pymunk.moment_for_poly(mass, scaled_poly, offset_circle, radius=shape_edge_radius)
    
    if moment is None: moment = _moment
    
    body = physics_types.body(mass, moment, body_type)
    body.position = sprite.position
    body.angle = math.radians(sprite.angle)
    
    if isinstance(physics_shape, physics_types.shape):
        shape = physics_shape
        shape.body = body
    else:
        if physics_shape == physics_types.circle:
            shape = physics_types.circle(body, 
                                            min(size.x, size.y) / 2 + shape_edge_radius, 
                                            offset_circle)
        else:
            scaled_poly = [[x * sprite.scale for x in z] for z in sprite.get_hit_box()]
            shape = physics_types.poly(body, scaled_poly, radius=shape_edge_radius)
    
    shape.collision_type = collision_type
    shape.friction = friction

    if elasticity is not None:
        shape.elasticity = elasticity

    def velocity_callback(my_body, my_gravity, my_damping, dt):
        """ Used for custom damping, gravity, and max_velocity. """
        # Custom damping
        if sprite.pymunk.damping is not None:
            adj_damping = ((sprite.pymunk.damping * 100.0) / 100.0) ** dt
            # print(f"Custom damping {sprite.pymunk.damping} {my_damping} default to {adj_damping}")
            my_damping = adj_damping

        # Custom gravity
        if sprite.pymunk.gravity is not None:
            my_gravity = sprite.pymunk.gravity

        # Go ahead and update velocity
        pymunk.Body.update_velocity(my_body, my_gravity, my_damping, dt)

        # Now see if we are going too fast...

        # Support max velocity
        if sprite.pymunk.max_velocity:
            velocity = my_body.velocity.length
            if velocity > sprite.pymunk.max_velocity:
                scale = sprite.pymunk.max_velocity / velocity
                my_body.velocity = my_body.velocity * scale

        ### Not needed for now. if making platformer game, we'll need it
        # # Support max horizontal velocity
        # if sprite.pymunk.max_horizontal_velocity:
        #     velocity = my_body.velocity.x
        #     if abs(velocity) > sprite.pymunk.max_horizontal_velocity:
        #         velocity = sprite.pymunk.max_horizontal_velocity * math.copysign(1, velocity)
        #         my_body.velocity = pymunk.Vec2d(velocity, my_body.velocity.y)

        # # Support max vertical velocity
        # if max_vertical_velocity:
        #     velocity = my_body.velocity[1]
        #     if abs(velocity) > max_vertical_velocity:
        #         velocity = max_horizontal_velocity * math.copysign(1, velocity)
        #         my_body.velocity = pymunk.Vec2d(my_body.velocity.x, velocity)

    if max_speed is not None:
        sprite.pymunk.max_velocity = max_speed
    
    if custom_gravity is not None:
        sprite.pymunk.gravity = custom_gravity
    
    if custom_damping is not None:
        sprite.pymunk.damping = custom_damping

    if body_type == physics_types.dynamic:
        body.velocity_func = velocity_callback
    
    return PhysicsObject(body, shape)


class PhysicsObject:
    '''
    physics object that holds pymunk body and shape for a sprite
    think usecase only!
    '''
    __slots__ = ('body',
                 'shape',
                 'hitbox')
    def __init__(self,
                 body: pymunk.Body = None,
                 shape: pymunk.Shape = None, 
                 hitbox: pymunk.Shape = None):
        
        self.body: Optional[pymunk.Body] = body
        ''' actual body which has mass, position, velocity, rotation '''
        self.shape: Optional[pymunk.Shape] = shape
        ''' main collision '''
        self.hitbox: Optional[pymunk.Shape] = hitbox or shape
        ''' custom hitbox collision if needed '''
        
    def draw(self):
        if not CONFIG.debug_draw: return False
        if isinstance(self.shape, physics_types.circle):
            arcade.draw_circle_outline(*self.body.position, self.shape.radius, (255,255,255,255))
        else:
            if isinstance(self.shape, physics_types.poly):
                shape = []
                angle = self.body.angle
                points = self.shape.get_vertices()
                for point in points:
                    shape.append(point.rotated(angle))
                debug_draw_poly(self.body.position, shape, (255,255,255,255))
    
    def __del__(self):
        # print(self.__name__, 'deleted just now')
        pass
    
    def _get_mass(self):
        return self.body.mass
    
    def _set_mass(self, mass:float):
        self.body.mass = mass
    
    mass:float = property(_get_mass, _set_mass)
    
    def _get_elasticity(self):
        return self.shape.elasticity
    
    def _set_elasticity(self, elasticity:float):
        self.shape.elasticity = elasticity
    
    elasticity:float = property(_get_elasticity, _set_elasticity)
    
    def _get_friction(self):
        return self.shape.friction
    
    def _set_friction(self, friction:float):
        self.shape.friction = friction
    
    friction:float = property(_get_friction, _set_friction)

    def _get_position(self):
        return Vector(self.body.position)
    
    def _set_position(self, position:tuple[float, float]):
        self.body.position = position
    
    position:Vector = property(_get_position, _set_position)
    
    def _get_velocity(self):
        return Vector(self.body.velocity)
    
    def _set_velocity(self, velocity:tuple[float, float]):
        self.body.velocity = velocity
    
    velocity:Vector = property(_get_position, _set_position)
    
    def _get_angle(self):
        return math.degrees(self.body.angle)
    
    def _set_angle(self, angle:float):
        self.body.angle = math.radians(angle)
    
    angle:float = property(_get_angle, _set_angle)
    
    def _get_collision_type(self):
        ''' movement or hitbox? '''
        return self.shape.collision_type
    
    def _set_collision_type(self, collision_type:int):
        self.shape.collision_type = collision_type
    
    collision_type = property(_get_collision_type, _set_collision_type)
    
    @property
    def speed(self):
        return self.velocity.length
    
    @property
    def space(self):
        return self.body.space


class PhysicsException(Exception):
    pass


class PhysicsEngine:
    '''
    pymunk physics handler for 2D game by mash
    
    there will be no gravity until set manually
    '''
    
    DYNAMIC = pymunk.Body.DYNAMIC
    STATIC = pymunk.Body.STATIC
    KINEMATIC = pymunk.Body.KINEMATIC
    MOMENT_INF = float('inf')
    
    def __init__(self, gravity = vectors.zero, damping = 0.1) -> None:
        self.space = pymunk.Space(threaded=True)
        self.space.threads = os.cpu_count() // 2
        self.space.gravity = gravity
        self.space.damping = damping    # ratio of speed(scalar) which is kept to next tick
        
        self.space.sleep_time_threshold = 5.0
        self.space.idle_speed_threshold = 100
        # self.space.collision_slop = 0.0
        
        # self.collision_types: list[str] = list(t.name for t in collision.__dict__())
        self.objects: dict[Sprite, PhysicsObject] = {}
        self.non_static_objects: list[Sprite] = []
        self.maximum_incline_on_ground = 0.708  # no need for now
        
        # self.space.add_post_step_callback()
        
    def _set_gravity(self, gravity:tuple):
        self.space.gravity = gravity
    
    def _get_gravity(self):
        return self.space.gravity
    
    gravity = property(_get_gravity, _set_gravity)
    
    def _set_damping(self, damping:float):
        self.space.damping = damping
    
    def _get_damping(self):
        return self.space.damping
    
    damping = property(_get_damping, _set_damping)
    """ The default damping for every object controls the percent of velocity the object will keep each SECOND.
    
    1.0 is no speed loss, 0.1 is 90% loss.
    
    For top-down, this is basically the friction for moving objects.
    
    For platformers with gravity, it's probably recommended to be 1.0"""
    
    def add_sprite(self, 
                   sprite:Sprite, 
                   mass:float = 1, 
                   friction:float = 0.2,
                   elasticity: Optional[float] = None,
                   moment_of_inertia: Optional[float] = None, 
                   body_type: int = DYNAMIC,
                   shape: Union[pymunk.Shape, type] = None, 
                   damping: Optional[float] = None,
                   gravity: Union[Vector, tuple[float, float]] = None,
                   max_velocity: int = None,
                   max_horizontal_velocity: int = None,
                   max_vertical_velocity: int = None,
                   radius: float = 0,
                   collision_type: Optional[int] = collision.default,
                   offset_body: Vector = None,
                   offset_shape: Vector = None,
                   spawn:bool = True,
                   ):
        
        if sprite in self.objects: return True
        
        if damping is not None:
            sprite.pymunk.damping = damping

        if gravity is not None:
            sprite.pymunk.gravity = gravity

        if max_velocity is not None:
            sprite.pymunk.max_velocity = max_velocity

        if max_vertical_velocity is not None:
            sprite.pymunk.max_vertical_velocity = max_vertical_velocity

        if max_horizontal_velocity is not None:
            sprite.pymunk.max_horizontal_velocity = max_horizontal_velocity

        ## Keep track of collision types
        # if collision_type not in self.collision_types:
        #     self.collision_types.append(collision_type)
        
        # # Get a number associated with the string of collision_type
        # collision_type_id = self.collision_types.index(collision_type)
        
        # Default to a box moment_of_inertia
        if moment_of_inertia is None:
            moment_of_inertia = pymunk.moment_for_box(mass, (sprite.width, sprite.height))
        
        # Create the physics body
        body = pymunk.Body(mass, moment_of_inertia, body_type=body_type)

        # Set the body's position
        body.position = pymunk.Vec2d(sprite.center_x, sprite.center_y)
        body.angle = math.radians(sprite.angle)
        
        # Callback used if we need custom gravity, damping, velocity, etc.
        def velocity_callback(my_body, my_gravity, my_damping, dt):
            """ Used for custom damping, gravity, and max_velocity. """
            # Custom damping
            if sprite.pymunk.damping is not None:
                adj_damping = ((sprite.pymunk.damping * 100.0) / 100.0) ** dt
                # print(f"Custom damping {sprite.pymunk.damping} {my_damping} default to {adj_damping}")
                my_damping = adj_damping

            # Custom gravity
            if sprite.pymunk.gravity is not None:
                my_gravity = sprite.pymunk.gravity

            # Go ahead and update velocity
            pymunk.Body.update_velocity(my_body, my_gravity, my_damping, dt)

            # Now see if we are going too fast...

            # Support max velocity
            if sprite.pymunk.max_velocity:
                velocity = my_body.velocity.length
                if velocity > sprite.pymunk.max_velocity:
                    scale = sprite.pymunk.max_velocity / velocity
                    my_body.velocity = my_body.velocity * scale

            # Support max horizontal velocity
            if sprite.pymunk.max_horizontal_velocity:
                velocity = my_body.velocity.x
                if abs(velocity) > sprite.pymunk.max_horizontal_velocity:
                    velocity = sprite.pymunk.max_horizontal_velocity * math.copysign(1, velocity)
                    my_body.velocity = pymunk.Vec2d(velocity, my_body.velocity.y)

            # Support max vertical velocity
            if max_vertical_velocity:
                velocity = my_body.velocity[1]
                if abs(velocity) > max_vertical_velocity:
                    velocity = max_horizontal_velocity * math.copysign(1, velocity)
                    my_body.velocity = pymunk.Vec2d(my_body.velocity.x, velocity)

        # Add callback if we need to do anything custom on this body
        # if damping or gravity or max_velocity or max_horizontal_velocity or max_vertical_velocity:
        if body_type == self.DYNAMIC:
            body.velocity_func = velocity_callback

        ### shape 세팅. 모든 물리 액션은 shape로 판단한다.
        # Set the physics shape to the sprite's hitbox
        if shape is None:
            # poly = sprite.get_adjusted_hit_box()
            poly = sprite.get_hit_box()
            scaled_poly = [[x * sprite.scale for x in z] for z in poly]
            
            shape = pymunk.Poly(body, scaled_poly, radius=radius)
        else:
            shape.body = body
        
        # Set collision type, used in collision callbacks
        if collision_type:
            # shape.collision_type = collision_type_id
            shape.collision_type = collision_type

        # How bouncy is the shape?
        if elasticity is not None:
            shape.elasticity = elasticity

        # Set shapes friction
        shape.friction = friction
        """ Friction only applied to collision """
        
        # Create physics object and add to list
        physics_object = self.add_object(sprite, body, shape)
        
        if spawn:
            # Add body and shape to pymunk engine, register physics engine to sprite
            self.add_to_space(sprite)
        
        return physics_object
    
    def add_object(self, sprite:Sprite, body:pymunk.Body, shape:pymunk.Shape):
        physics_object = PhysicsObject(body, shape)
        self.objects[sprite] = physics_object
        if body.body_type != self.STATIC:
            self.non_static_objects.append(sprite)
        return physics_object
    
    def add_to_space(self, sprite:Sprite) -> None:
        physics_object = self.objects[sprite]
        self.space.add(physics_object.body, physics_object.shape)
        
        # Register physics engine with sprite, so we can remove from physics engine
        # if we tell the sprite to go away.
        sprite.register_physics_engine(self)
    
    def add_sprite_list(self, 
                        sprite_list, 
                        mass: float = 1,
                        friction: float = 0.2,
                        elasticity: Optional[float] = None,
                        moment_of_intertia: Optional[float] = None,
                        shape: pymunk.Shape = None, 
                        body_type: int = DYNAMIC,
                        damping: Optional[float] = None,
                        collision_type: Optional[str] = None
                        ):
        
        for sprite in sprite_list:
            self.add_sprite(sprite=sprite,
                            mass=mass,
                            friction=friction,
                            elasticity=elasticity,
                            moment_of_inertia=moment_of_intertia,
                            shape=shape, 
                            body_type=body_type,
                            damping=damping,
                            collision_type=collision_type)
    
    def remove_sprite(self, sprite:Sprite):
        ''' name coupled with aracde framework. so do not change it'''
        physics_object = self.objects[sprite]
        self.space.remove(physics_object.body)  # type: ignore
        self.space.remove(physics_object.shape)  # type: ignore
        self.objects.pop(sprite)
        if sprite in self.non_static_objects:
            self.non_static_objects.remove(sprite)
            return True
        return False
    
    def get_object_from_shape(self, shape: Optional[pymunk.Shape]) -> Optional[Sprite]:
        """ Given a shape, what sprite is associated with it? """
        for sprite in self.objects:
            if self.objects[sprite].shape is shape:
                return sprite
        return None
    
    def get_objects_from_arbiter(self, arbiter: pymunk.Arbiter) -> tuple[Optional[Sprite], Optional[Sprite]]:
        """ Given a collision arbiter, return the sprites associated with the collision. """
        shape1, shape2 = arbiter.shapes
        sprite1 = self.get_object_from_shape(shape1)
        sprite2 = self.get_object_from_shape(shape2)
        return sprite1, sprite2
    
    def is_on_ground(self, sprite: Sprite) -> bool:
        """ Return true of sprite is on top of something. """
        grounding = self.check_grounding(sprite)
        return grounding['body'] is not None
    
    def check_grounding(self, sprite: Sprite):
        """ See if the player is on the ground. Used to see if we can jump. """
        grounding = {
            'normal': pymunk.Vec2d.zero(),
            'penetration': pymunk.Vec2d.zero(),
            'impulse': pymunk.Vec2d.zero(),
            'position': pymunk.Vec2d.zero(),
            'body': None
        }

        # creates a unit vector (Vector of length 1) in the same direction as the gravity
        gravity_unit_vector = pymunk.Vec2d(1, 0).rotated(self.space.gravity.angle)

        def f(arbiter: pymunk.Arbiter):
            """
            Checks if the the point of collision is in a way, that the sprite is on top of the other
            """
            # Gets the normal vector of the collision. This is the point of collision.
            n = arbiter.contact_point_set.normal

            # Checks if the x component of the gravity is in range of the maximum incline, same for the y component.
            # This will work, as the normal AND gravity are both points on a circle with a radius of 1.
            # (both are unit vectors)
            if gravity_unit_vector.x + self.maximum_incline_on_ground > \
               n.x > \
               gravity_unit_vector.x - self.maximum_incline_on_ground\
               and \
               gravity_unit_vector.y + self.maximum_incline_on_ground > \
               n.y > gravity_unit_vector.y - self.maximum_incline_on_ground:
                grounding['normal'] = n
                grounding['penetration'] = -arbiter.contact_point_set.points[0].distance
                grounding['body'] = arbiter.shapes[1].body
                grounding['impulse'] = arbiter.total_impulse
                grounding['position'] = arbiter.contact_point_set.points[0].point_b

        physics_object = self.objects[sprite]
        if not physics_object.body:
            raise ValueError("No physics body set.")
        physics_object.body.each_arbiter(f)

        return grounding
    
    def apply_impulse(self, sprite: Sprite, impulse: Vector):
        """ Apply an impulse force on a sprite """
        physics_object = self.get_physics_object(sprite)
        if physics_object is None:
            raise PhysicsException("Tried to apply an impulse, but this physics object has no 'body' set.")
        physics_object.body.apply_impulse_at_local_point(impulse)
    
    def apply_impulse_world(self, sprite: Sprite, impulse: Vector, point: Vector):
        """ Apply an impulse force on a sprite from a world point """
        physics_object = self.get_physics_object(sprite)
        if physics_object is None:
            raise PhysicsException("Tried to apply an impulse, but this physics object has no 'body' set.")
        physics_object.body.apply_impulse_at_world_point(impulse, point)
    
    def apply_force(self, sprite: Sprite, force: Vector):
        """ Apply an impulse force on a sprite """
        physics_object = self.get_physics_object(sprite)
        if physics_object is None:
            raise PhysicsException("Tried to apply a force, but this physics object has no 'body' set.")
        physics_object.body.apply_force_at_local_point(force)
    
    def apply_force_world(self, sprite: Sprite, force: Vector, point: Vector):
        """ Apply an impulse force on a sprite from a world point """
        physics_object = self.get_physics_object(sprite)
        if physics_object is None:
            raise PhysicsException("Tried to apply a force, but this physics object has no 'body' set.")
        physics_object.body.apply_force_at_world_point(force, point)
    
    def get_physics_object(self, sprite: Sprite) -> PhysicsObject:
        """ Get the shape/body for a sprite. """
        return self.objects[sprite]
    
    def set_position(self, sprite: Sprite, position: Vector):
        ''' might be deprecated '''
        physics_object = self.get_physics_object(sprite)
        if physics_object.body is None:
            raise PhysicsException("Tried to set a position, but this physics object has no 'body' set.")
        physics_object.body.position = position
    
    def set_velocity(self, sprite: Sprite, velocity: Vector):
        ''' might be deprecated '''
        physics_object = self.get_physics_object(sprite)
        if physics_object.body is None:
            raise PhysicsException("Tried to set a velocity, but this physics object has no 'body' set.")
        physics_object.body.velocity = velocity
    
    def apply_opposite_running_force(self, sprite: Sprite):
        """
        If a sprite goes left while on top of a dynamic sprite, that sprite
        should get pushed to the right.
        """
        grounding = self.check_grounding(sprite)
        body = self.get_physics_object(sprite).body
        if not body:
            raise ValueError("Physics body not set.")

        if body.force[0] and grounding and grounding['body']:
            grounding['body'].apply_force_at_world_point((-body.force[0], 0), grounding['position'])
    
    def query_segment(self, origin:Vector, end:Vector, radius = 1.0, shape_filter = None):
        ''' returns {PhysicsObject}'''
        query = self.space.segment_query(origin, end, radius, shape_filter)
        if not query: return None
        return query
            
    def hide(self, sprite: Sprite):
        physics_object = self.get_physics_object(sprite)
        self.space.add_default_collision_handler()
        physics_object.body.sleep()
    
    def add_collision_handler(self, 
                              first_type:str,
                              second_type:str, 
                              begin_handler:Callable = None,
                              pre_handler:Callable = None, 
                              post_handler:Callable = None,
                              separate_handler:Callable = None):
        """ Add code to handle collisions between objects. """
        # if first_type not in self.collision_types:
        #     self.collision_types.append(first_type)
        # first_type_id = self.collision_types.index(first_type)
        
        # if second_type not in self.collision_types:
        #     self.collision_types.append(second_type)
        # second_type_id = self.collision_types.index(second_type)
        
        """A collision handler is a set of 4 function callbacks for the different
        collision events that Pymunk recognizes.

        Collision callbacks are closely associated with Arbiter objects. You
        should familiarize yourself with those as well.

        Note #1: Shapes tagged as sensors (Shape.sensor == true) never generate
        collisions that get processed, so collisions between sensors shapes and
        other shapes will never call the post_solve() callback. They still
        generate begin(), and separate() callbacks, and the pre_solve() callback
        is also called every frame even though there is no collision response.
        Note #2: pre_solve() callbacks are called before the sleeping algorithm
        runs. If an object falls asleep, its post_solve() callback won't be
        called until it's re-awoken.
        """
        
        def handler_begin(arbiter, space, data):
            sprite_a, sprite_b = self.get_objects_from_arbiter(arbiter)
            should_process_collision = begin_handler(sprite_a, sprite_b, arbiter, space, data)
            return should_process_collision

        def handler_post(arbiter, space, data):
            sprite_a, sprite_b = self.get_objects_from_arbiter(arbiter)
            if sprite_a is not None and sprite_b is not None:
                post_handler(sprite_a, sprite_b, arbiter, space, data)

        def handler_pre(arbiter, space, data):
            sprite_a, sprite_b = self.get_objects_from_arbiter(arbiter)
            return pre_handler(sprite_a, sprite_b, arbiter, space, data)

        def handler_separate(arbiter, space, data):
            sprite_a, sprite_b = self.get_objects_from_arbiter(arbiter)
            separate_handler(sprite_a, sprite_b, arbiter, space, data)
        
        # h = self.space.add_collision_handler(first_type_id, second_type_id)
        h = self.space.add_collision_handler(first_type, second_type)
        if begin_handler:
            h.begin = handler_begin
        if post_handler:
            h.post_solve = handler_post
        if pre_handler:
            h.pre_solve = handler_pre
        if separate_handler:
            h.separate = handler_separate
    
    def activate_objects(self):
        for sprite in self.non_static_objects:
            self.objects[sprite].body.activate()
    
    def resync_objects(self):
        """
        Set visual sprites to be the same location as physics engine sprites.
        Call this after stepping the pymunk physics engine
        """
        # Create copy in case a sprite wants to remove itself from the list as
        # we iterate through the list.
        sprites = self.non_static_objects.copy()

        for sprite in sprites:
            # Get physics object for this sprite
            physics_object = self.objects[sprite]

            # Item is sleeping, skip
            if physics_object.body.is_sleeping:
                continue

            original_position = sprite.position
            new_position = physics_object.body.position
            new_angle = math.degrees(physics_object.body.angle)

            # Calculate change in location, used in call-back
            dx = new_position[0] - original_position[0]
            dy = new_position[1] - original_position[1]
            d_angle = new_angle - sprite.angle

            # Update sprite to new location
            sprite.position = new_position
            sprite.angle = new_angle

            # Notify sprite we moved, in case animation needs to be updated
            sprite.pymunk_moved(self, dx, dy, d_angle)
    
    def step(self,
             delta_time: float = 1 / 60.0,
             resync_objects: bool = True):
        """
        Tell the physics engine to perform calculations.

        :param float delta_time: Time to move the simulation forward. Keep this
                                 value constant, do not use varying values for
                                 each step.
        :param bool resync_sprites: Resynchronize Arcade graphical sprites to be
                                    at the same location as their Pymunk counterparts.
                                    If running multiple steps per frame, set this to
                                    false for the first steps, and true for the last
                                    step that's part of the update.
        """
        # Update physics
        # Use a constant time step, don't use delta_time
        # See "Game loop / moving time forward"
        # http://www.pymunk.org/en/latest/overview.html#game-loop-moving-time-forward
        self.space.step(delta_time)
        if resync_objects:
            self.resync_objects()