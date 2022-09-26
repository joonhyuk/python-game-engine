'''
physics engine based on pymunk, 
very simple physics code injection by mash

may be coupled with pymunk
'''
import sys, math
from typing import Callable, Optional, Union
from enum import Enum
from weakref import WeakSet

### for in-house physics engine
import arcade, pymunk, pymunk.util
from .vector import Vector
from config.engine import *
from .utils import *

from arcade import Sprite

def is_sprite_not_in_zone(sprite:Sprite):
    
    if GAMEZONE_POS_MIN < sprite.position[0] < GAMEZONE_POS_MAX:
        if GAMEZONE_POS_MIN < sprite.position[1] < GAMEZONE_POS_MAX:
            return False

    return True

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
    ''' collides with nothing '''
    filter_allmask = pymunk.ShapeFilter(mask = allmask)
    ''' collides with everything '''
    filter_allcategories = pymunk.ShapeFilter(mask = allcategories)


def setup_shape(body:physics_types.body,
                collision_type = collision.default,
                
                ):
    pass


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
                         additional_hitbox:bool = False,
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
            scaled_poly = [[x * sprite.scale for x in z] for z in sprite.get_hit_box()].reverse()
            _moment = pymunk.moment_for_poly(mass, scaled_poly, offset_circle, radius=shape_edge_radius)
    
    if moment is None: moment = _moment
    
    body = physics_types.body(mass, moment, body_type)
    body.position = sprite.position
    body.angle = math.radians(sprite.angle)
    
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
    
    if additional_hitbox:
        hitbox = physics_types.poly(body, sprite.get_hit_box(), pymunk.Transform.scaling(sprite.scale))
    else:
        hitbox = None
    
    shape:Union[physics_types.shape, list[physics_types.shape]]
    
    if isinstance(physics_shape, (physics_types.shape, list)):
        shape = physics_shape
        if isinstance(physics_shape, list):
            for sh in shape:
                sh.body = body
        else:
           shape.body = body
    else:
        if physics_shape == physics_types.circle:
            shape = physics_types.circle(body, 
                                            min(size.x, size.y) / 2 + shape_edge_radius, 
                                            offset_circle)
        else:
            poly = sprite.get_hit_box()
            scaled_poly = [[x * sprite.scale for x in z] for z in poly]
            scaled_poly.reverse()
            if not pymunk.util.is_convex(scaled_poly):
            # if hasattr(sprite, 'is_concave') and sprite.is_concave:
                # shape:list[physics_types.poly] = []
                # # triangles = pymunk.util.triangulate(scaled_poly)
                # convexes = pymunk.util.convexise(pymunk.util.triangulate(scaled_poly))
                
                # for convex in convexes:
                #     shape.append(physics_types.poly(body, convex, radius=shape_edge_radius))
                shape = convexise_complex(scaled_poly, body, radius = shape_edge_radius)
            else:    
                shape = physics_types.poly(body, scaled_poly, radius=shape_edge_radius)

    obj = PhysicsObject(body, shape, hitbox)
    
    obj.collision_type = collision_type
    obj.friction = friction

    if elasticity is not None:
        obj.elasticity = elasticity
    
    return obj


def convexise_complex(points:list[tuple[float, float]], body, **kwargs) -> list[physics_types.poly]:
    shape:list[physics_types.poly] = []
    convexes = pymunk.util.convexise(pymunk.util.triangulate(points))
    for convex in convexes:
        shape.append(physics_types.poly(body, convex, **kwargs))
    
    return shape

def convexise_shape(body:physics_types.body):
    ''' 결론적으로는 쓸모 없어졌지만... '''
    #deprecated
    shapes = body.shapes
    triangles = []
    for shape in shapes:
        if not isinstance(shape, physics_types.poly):
            raise PhysicsException('not poly')
        triangles.extend(pymunk.util.triangulate(shape.get_vertices()))
    convexes = pymunk.util.convexise(triangles)
    
    new_shapes = WeakSet()
    for convex in convexes:
        new_shapes.add(physics_types.poly(body, convex))
    body._shapes = new_shapes
    body.space.add(*new_shapes)
    body.space.remove(*shapes)

def build_convex_shape(body:physics_types.body, points_list:set[list]) -> list[physics_types.poly]:
    #deprecated
    triangles = []
    for points in points_list:
        # if not isinstance(shape, physics_types.poly):
            # raise PhysicsException('not poly')
        # points.reverse()
        triangles.extend(pymunk.util.triangulate(points))
    convexes = pymunk.util.convexise(triangles)
    
    new_shapes = set()
    for convex in convexes:
        new_shapes.add(physics_types.poly(body, convex))
    # body._shapes = new_shapes
    
    body._shapes.union(new_shapes)
    body.space.add(*new_shapes)
    # body.space.remove(*shapes)
    return new_shapes

def build_convex_shape2(body:physics_types.body, points_list:set[list]) -> list[physics_types.poly]:
    #deprecated
    tmp_hull = pymunk.util.convex_hull([y for x in points_list for y in x])
    bad_boys = check_point_on_segment(tmp_hull)
    if bad_boys:
        for bad in bad_boys:
            points_list.remove(bad)
    return build_convex_shape(body, points_list)

def check_point_on_segment(points:list[Vector]) -> list[Vector]:
    
    print('input__', points)
    # points = list(set(points))
    pnts = [Vector(x) for x in points]
    points = list(dict.fromkeys(pnts))
    print('phase_1', points)
    num = len(points)
    if num < 3:
        raise AttributeError('need more than 3 points')
    # points = tuple(points)
    bad_boys = []
    
    for i, point in enumerate(points):
        ab = point - points[i - 1]
        bc = points[i + 1 if i < num - 1 else 0] - point
        if ab.unit == bc.unit:
            bad_boys.append(point)
    
    return bad_boys

    if not bad_boys: return points
    
    for bad in bad_boys:
        points.remove(bad)
    print('phase_2', points)
    
    return points

def _attempt_reduction(hulla:list, hullb:list):
    inter = [vec for vec in hulla if vec in hullb]
    if len(inter) == 2:
        starta = hulla.index(inter[1])
        tempa = hulla[starta:] + hulla[:starta]
        tempa = tempa[1:-1]
        startb = hullb.index(inter[0])
        tempb = hullb[startb:] + hullb[:startb]
        tempb = tempb[1:-1]
        reduced = tempa + tempb
        if pymunk.util.is_convex(reduced):
            return reduced
    # reduction failed, return None
    return None

def _remove_last_point_and_union(hulla:list, hullb:list):
    inter = [vec for vec in hulla if vec in hullb]
    if len(inter) == 1:
        starta = hulla.index(inter[0])
        tempa = hulla[starta:] + hulla[:starta]
        tempa = tempa[1:]
        startb = hullb.index(inter[0])
        tempb = hullb[startb:] + hullb[:startb]
        tempb = tempb[1:]
        reduced = tempa + tempb
        return reduced
    return None

def _reduce_shapes(shapes:list, reduction_func:Callable):
    count = len(shapes)
    if count < 2:
        return shapes, False
    
    for ia in range(count - 1):
        for ib in range(ia + 1, count):
            reduction = reduction_func(shapes[ia], shapes[ib])
            if reduction != None:
                # they can so return a new list of hulls and a True
                newhulls = [reduction]
                for j in range(count):
                    if not (j in (ia, ib)):
                        newhulls.append(shapes[j])
                return newhulls, True

    # nothing was reduced, send the original hull list back with a False
    return shapes, False

def triangulate_all(shapes:list):
    triangles = []
    for shape in shapes:
        triangles.extend(pymunk.util.triangulate(shape))
    return triangles

def get_convexes(shapes) -> list:
    """Reduces a list of shapes to a
    non-optimum list of convex polygons

    :Parameters:
        shapes
            list of anticlockwise shapes (a list of more than three points) to reduce
    """
    hulls = shapes[:]
    reduced = True
    n = 0
    # keep trying to reduce until it won't reduce any more
    while reduced:
        print('step',n,':',hulls)
        hulls, reduced = _reduce_shapes(hulls, _attempt_reduction)
        n += 1
    reduced = True
    while reduced:
        print('step',n,':',hulls)
        hulls, reduced = _reduce_shapes(hulls, _remove_last_point_and_union)
        n += 1
    # return reduced hull list
    
    return pymunk.util.convexise(triangulate_all(hulls))

def build_shapes_with_convexes(body:physics_types.body, convex_list:list, 
                               friction = 1.0,
                               elasticity:float = None,
                               collision_type = collision.default,
                               shape_edge_raduis = 0.0,
                               ):
    shapes:list[physics_types.poly] = []
    for convex in convex_list:
        shape = physics_types.poly(body, convex, radius=shape_edge_raduis)
        shape.collision_type = collision_type
        shape.friction = friction
        if elasticity is not None:
            shape.elasticity = elasticity
        shapes.append(shape)
    return shapes

def add_convex_to_world(convex_list:list, world_physics:"PhysicsEngine",
                        friction = 1.0,
                        elasticity:float = None,
                        collision_type = collision.default,
                        shape_edge_raduis = 0.0,
                        ):
    body = world_physics.space.static_body
    shapes = build_shapes_with_convexes(body, convex_list, 
                                        friction=friction,
                                        elasticity=elasticity,
                                        collision_type=collision_type,
                                        shape_edge_raduis=shape_edge_raduis)
    body._shapes.union(shapes)
    body.space.add(*shapes)
    return shapes


class PhysicsObject:
    '''
    physics object that holds pymunk body and shape for a sprite
    think usecase only!
    
    completely decoupled with private codes
    '''
    __slots__ = ('_body', '_shape', 'hitbox', '_scale', '_initial_size', '_initial_mass', '_mass_scaling', '_original_poly', '_hidden', '_last_filter', 'joints', 'multi_shape')
    def __init__(self,
                 body: pymunk.Body = None,
                 shape: Union[list[pymunk.Shape], pymunk.Shape] = None, 
                 hitbox: physics_types.poly = None,
                 mass_scaling:bool = True,
                 ):
        
        self._body: Optional[pymunk.Body] = body
        ''' actual body which has mass, position, velocity, rotation '''
        if isinstance(shape, list):
            self.multi_shape = True
            self._shape:list[pymunk.Shape] = shape
        else:
            self.multi_shape = False
            self._shape:pymunk.Shape = shape
        # if isinstance(shape, pymunk.Shape):
        #     self.shape: Optional[pymunk.Shape] = shape
        # else:
        #     self.shape:list[pymunk.Shape] = shape
        # self._shape: Union[list[pymunk.Shape], pymunk.Shape] = shape
        ''' main collision '''
        self.hitbox: physics_types.poly = hitbox
        ''' custom hitbox collision if needed '''
        self._scale = 1.0
        self._initial_size:Union[float, Vector] = self._get_size()
        ''' no need to be set when poly '''
        self._initial_mass = body.mass
        # if hitbox: self._original_poly = self.hitbox.get_vertices()
        if isinstance(self.shape, physics_types.poly):
            self._original_poly = self.shape.get_vertices()
        self._mass_scaling = mass_scaling
        
        self._last_filter:pymunk.ShapeFilter = self.shape.filter    ### should revisit later
        self._hidden = False
        
        self.joints:list[pymunk.constraints.Constraint] = []

    def _get_size(self):
        if not self.shape: return 0
        if isinstance(self.shape, physics_types.circle):
            return self.shape.radius
        if isinstance(self.shape, physics_types.segment):
            return (self.shape.a - self.shape.b).length
        return None

    def _hide(self, switch:bool = None):
        if switch is None: switch = not self._hidden
        if switch: self._last_filter = self.filter
        self.filter = physics_types.filter_nomask if switch else self._last_filter
        return switch
    
    def segment_query(self, end:Vector, start:Vector = None, radius:float = 1, shape_filter = None):
        if start is None: start = self.position
        if shape_filter is None: shape_filter = pymunk.ShapeFilter(mask=physics_types.allmask^collision.character)  ### need to revisit
        
        return self._body.space.segment_query(start, end, radius, shape_filter)
    
    def debug_draw(self, color = (255, 255, 0, 128), line_thickness = 1):
        if not CONFIG.debug_f_keys[2]: return False
        if isinstance(self.shape, physics_types.circle):
            debug_draw_circle(self._body.position, self.shape.radius, color, line_thickness)
        else:
            ''' costs a lot. optimize later if needed '''
            if self.multi_shape:
                debug_draw_multi_shape(self._shape, self._body, color, line_thickness)
            else : debug_draw_shape(self._shape, self._body, color, line_thickness)
    
    @classmethod
    def debug_draw_body(body:physics_types.body, color = (255, 255, 0, 128), line_thickness = 1):
        shapes = body.shapes
        for shape in shapes:
            debug_draw_shape(shape, body, color, line_thickness)
        
    def add_pivot(self, target:physics_types.body, *positions):
        if target is None: PhysicsException('target body is None. check spawnned')
        joint = pymunk.constraints.PivotJoint(self._body, target, *positions)
        self.joints.append(joint)
        self.space.add(joint)
    
    def add_world_pivot(self, position:Vector):
        joint = pymunk.constraints.PivotJoint(self._body, self.space.static_body, position)
        self.joints.append(joint)
        self.space.add(joint)
    
    def remove_pivot(self, target:physics_types.body = None):
        if target is None: target = self.space.static_body
        if target is None: PhysicsException('target body is None. check spawnned')
        for joint in self.joints:
            if joint.b == target:
                self.joints.remove(joint)
                self.space.remove(joint)
    
    def destroy(self):
        if self.multi_shape: self.space.remove(*self._shape)
        else: self.space.remove(self._shape)
        self.space.remove(self._body, *self.joints)      ### self.space is from self.body, so it should come last
        self.joints.clear()
    
    def __del__(self):
        if self.joints:
            map(self.space.remove, self.joints)
    
    angular_velocity = PropertyFrom('_body')
    
    def _get_body(self):
        return self._body
    
    def _set_body(self, body):
        if self.multi_shape:
            for shape in self._shape:
                shape.body = body
        else: self._shape.body = body
    
    body = property(_get_body, _set_body)
    
    def _get_shape(self):
        return self._shape if not self.multi_shape else self._shape[0]
    
    def _set_shape(self, shape):
        self._shape = shape
    
    shape = property(_get_shape, _set_shape)
    
    def _get_scale(self):
        return self._scale
    
    def _set_scale(self, scale:float):
        ''' unsafe for real physics '''
        # if scale <= 0: raise PhysicsException     ## need something
        self._scale = scale
        
        if isinstance(self.shape, physics_types.circle):
            self.shape.unsafe_set_radius(self._initial_size * scale)
        else:
            ### totally unsafe...
            # self.shape.update(pymunk.Transform.scaling(scale))
            # if not self.hitbox: return False
            st = pymunk.Transform.scaling(scale)
            self.shape.unsafe_set_vertices(self._original_poly, st)
            if self._mass_scaling: self.mass = self._initial_mass * scale
    
    scale:float = property(_get_scale, _set_scale)
    ''' scaling is not yet supported for multi-shape object '''
    
    def _get_mass(self):
        return self._body.mass
    
    def _set_mass(self, mass:float):
        self._body.mass = mass
    
    mass:float = property(_get_mass, _set_mass)
    
    def _get_elasticity(self):
        return self._shape.elasticity if not self.multi_shape else self._shape[0].elasicity
    
    def _set_elasticity(self, elasticity:float):
        if self.multi_shape:
            for shape in self._shape:
                shape.elasticity = elasticity
        else: self._shape.elasticity = elasticity
    
    elasticity:float = property(_get_elasticity, _set_elasticity)
    
    def _get_friction(self):
        return self._shape.friction if not self.multi_shape else self._shape[0].friction
    
    def _set_friction(self, friction:float):
        if self.multi_shape:
            for shape in self._shape:
                shape.friction = friction
        else: self._shape.friction = friction
    
    friction:float = property(_get_friction, _set_friction)

    def _get_position(self):
        return Vector(self._body.position)
    
    def _set_position(self, position:tuple[float, float]):
        self._body.position = position
    
    position:Vector = property(_get_position, _set_position)
    
    def _get_velocity(self):
        return Vector(self._body.velocity)
    
    def _set_velocity(self, velocity:tuple[float, float]):
        self._body.velocity = velocity
    
    velocity:Vector = property(_get_velocity, _set_velocity)
    
    def _get_angle(self):
        return math.degrees(self._body.angle)
    
    def _set_angle(self, angle:float):
        self._body.angle = math.radians(angle)
    
    angle:float = property(_get_angle, _set_angle)
    
    def _get_collision_type(self):
        ''' movement or hitbox? '''
        return self._shape.collision_type if not self.multi_shape else self._shape[0].collision_type
        return self.shape.collision_type
    
    def _set_collision_type(self, collision_type:int):
        if self.multi_shape:
            for shape in self._shape:
                shape.collision_type = collision_type
        else: self._shape.collision_type = collision_type
    
    collision_type = property(_get_collision_type, _set_collision_type)
    
    def _get_hidden(self):
        return self._hidden
    
    def _set_hidden(self, switch:bool = None):
        self._hidden = self._hide(switch)
        
    hidden:bool = property(_get_hidden, _set_hidden)
    
    def _get_filter(self):
        return self._shape.filter if not self.multi_shape else self._shape[0].filter
    
    def _set_filter(self, filter):
        if self.multi_shape:
            for shape in self._shape:
                shape.filter = filter
        else: self._shape.filter = filter
    
    filter = property(_get_filter, _set_filter)
        
    
    @property
    def speed(self):
        return self.velocity.length
    
    @property
    def space(self):
        return self._body.space


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
        self.space.idle_speed_threshold = 10
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
            scaled_poly.reverse()
            if not pymunk.util.is_convex(scaled_poly):
            # if hasattr(sprite, 'is_concave') and sprite.is_concave:
                shape:list[pymunk.Poly] = []
                # triangles = pymunk.util.triangulate(scaled_poly)
                triangles = pymunk.util.convexise(pymunk.util.triangulate(scaled_poly))
                for triangle in triangles:
                    shape.append(pymunk.Poly(body, triangle, radius=radius))
            else:    
                shape = pymunk.Poly(body, scaled_poly, radius=radius)
        else:
            shape.body = body
        
        # Create physics object and add to list
        physics_object = self.add_object(sprite, body, shape)
        
        # Set collision type, used in collision callbacks
        if collision_type:
            # shape.collision_type = collision_type_id
            physics_object.collision_type = collision_type

        # How bouncy is the shape?
        if elasticity is not None:
            physics_object.elasticity = elasticity

        # Set shapes friction
        physics_object.friction = friction
        """ Friction only applied to collision """
        
        if spawn:
            # Add body and shape to pymunk engine, register physics engine to sprite
            self.add_to_space(sprite)
        
        return physics_object
    
    def add_object(self, sprite:Sprite, body:pymunk.Body, shape:pymunk.Shape):
        physics_object = PhysicsObject(body, shape)
        self.add_physics_object(sprite, physics_object)
        return physics_object
    
    def add_physics_object(self, sprite:Sprite, physics_object:PhysicsObject):
        self.objects[sprite] = physics_object
        if physics_object._body.body_type != self.STATIC:
            self.non_static_objects.append(sprite)
        return physics_object
    
    def add_to_space(self, sprite:Sprite) -> None:
        physics_object = self.objects[sprite]
        if isinstance(physics_object._shape, list):
        # if hasattr(sprite, 'is_concave') and sprite.is_concave:
            self.space.add(physics_object._body, *physics_object._shape)
        else:
            self.space.add(physics_object._body, physics_object.shape)
        
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
    
    def add_static_collison(self, sprite_list,
                            friction = 1.0,
                            elasticity:float = None,
                            collision_type = collision.default,
                            shape_edge_raduis = 0.0,
                            ):
        walls_points:list = []
        for sprite in sprite_list:
            sprite:Sprite
            hit_box = sprite.get_hit_box()
            pos = sprite.position
            scaled_poly = [[int(x * sprite.scale + p) for x, p in zip(z, pos)] for z in hit_box]
            walls_points.append(scaled_poly)

        wall_convexes = get_convexes(walls_points)
        return add_convex_to_world(wall_convexes, self, elasticity=elasticity, collision_type=collision_type, friction=friction, shape_edge_raduis=shape_edge_raduis) 
    
    def remove_sprite(self, sprite:Sprite):
        ''' name coupled with aracde framework. so do not change it'''
        # physics_object = self.objects[sprite]
        # self.space.remove(physics_object.body)  # type: ignore
        # self.space.remove(physics_object.shape)  # type: ignore
        self.objects.pop(sprite).destroy()
        if sprite in self.non_static_objects:
            self.non_static_objects.remove(sprite)
    
    def get_object_from_shape(self, shape: Optional[pymunk.Shape]) -> Optional[Sprite]:
        """ Given a shape, what sprite is associated with it? """
        for sprite, physics in self.objects.items():
            if physics.shape is shape:
                return sprite
        return None
    
    def get_objects_from_arbiter(self, arbiter: pymunk.Arbiter) -> tuple[Optional[Sprite], Optional[Sprite]]:
        """ Given a collision arbiter, return the sprites associated with the collision. """
        shape1, shape2 = arbiter.shapes
        sprite1 = self.get_object_from_shape(shape1)
        sprite2 = self.get_object_from_shape(shape2)
        return sprite1, sprite2
    
    def get_owner(self, shape:Optional[pymunk.Shape]):
        print('HIT SPRITE ', self.get_object_from_shape(shape))
        return self.get_object_from_shape(shape).owner
    
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
        if not physics_object._body:
            raise ValueError("No physics body set.")
        physics_object._body.each_arbiter(f)

        return grounding
    
    def apply_impulse(self, sprite: Sprite, impulse: Vector):
        """ Apply an impulse force on a sprite """
        physics_object = self.get_physics_object(sprite)
        if physics_object is None:
            raise PhysicsException("Tried to apply an impulse, but this physics object has no 'body' set.")
        physics_object._body.apply_impulse_at_local_point(impulse)
    
    def apply_impulse_world(self, sprite: Sprite, impulse: Vector, point: Vector):
        """ Apply an impulse force on a sprite from a world point """
        physics_object = self.get_physics_object(sprite)
        if physics_object is None:
            raise PhysicsException("Tried to apply an impulse, but this physics object has no 'body' set.")
        physics_object._body.apply_impulse_at_world_point(impulse, point)
    
    def apply_force(self, sprite: Sprite, force: Vector):
        """ Apply an impulse force on a sprite """
        physics_object = self.get_physics_object(sprite)
        if physics_object is None:
            raise PhysicsException("Tried to apply a force, but this physics object has no 'body' set.")
        physics_object._body.apply_force_at_local_point(force)
    
    def apply_force_world(self, sprite: Sprite, force: Vector, point: Vector):
        """ Apply an impulse force on a sprite from a world point """
        physics_object = self.get_physics_object(sprite)
        if physics_object is None:
            raise PhysicsException("Tried to apply a force, but this physics object has no 'body' set.")
        physics_object._body.apply_force_at_world_point(force, point)
    
    def get_physics_object(self, sprite: Sprite) -> PhysicsObject:
        """ Get the shape/body for a sprite. """
        return self.objects[sprite]
    
    def set_position(self, sprite: Sprite, position: Vector):
        ''' might be deprecated '''
        physics_object = self.get_physics_object(sprite)
        if physics_object._body is None:
            raise PhysicsException("Tried to set a position, but this physics object has no 'body' set.")
        physics_object._body.position = position
    
    def set_velocity(self, sprite: Sprite, velocity: Vector):
        ''' might be deprecated '''
        physics_object = self.get_physics_object(sprite)
        if physics_object._body is None:
            raise PhysicsException("Tried to set a velocity, but this physics object has no 'body' set.")
        physics_object._body.velocity = velocity
    
    def apply_opposite_running_force(self, sprite: Sprite):
        """
        If a sprite goes left while on top of a dynamic sprite, that sprite
        should get pushed to the right.
        """
        grounding = self.check_grounding(sprite)
        body = self.get_physics_object(sprite)._body
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
        physics_object._body.sleep()
    
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
            self.objects[sprite]._body.activate()
    
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
            if physics_object._body.is_sleeping:
                continue

            if is_sprite_not_in_zone(sprite):
                if hasattr(sprite, 'owner'): sprite.owner.destroy()
                else: sprite.remove_from_sprite_lists()
                continue

            original_position = sprite.position
            new_position = physics_object._body.position
            new_angle = math.degrees(physics_object._body.angle)

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