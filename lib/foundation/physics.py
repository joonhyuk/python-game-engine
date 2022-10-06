'''
(only coupled with pymunk in this file)
'''

import math
from typing import Callable, Optional, Union

import pymunk, pymunk.util
from pymunk._chipmunk_cffi import ffi, lib

from pymunk import _chipmunk_cffi, _version

cp = _chipmunk_cffi.lib
ffi = _chipmunk_cffi.ffi
lib = _chipmunk_cffi.lib


from .base import *
from .vector import *
from .utils import *
# from .engine.primitive import Sprite
from .engine.object import *

from config.engine import *


def get_all_points_from_shapes(shapes):
    return [point for shape in shapes for point in shape]

def _reduce_points(points:list[Vector]) -> list[Vector]:
    
    # print('input__', points)
    # points = list(set(points))
    points = [Vector(x) for x in points]
    # points = list(dict.fromkeys(points))      ### 중복 포인트는 제거하지 않는다. 혹시라도 concave에서 겹치는게 있을 수 있음.

    # print('phase_1', points)
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
    
    # return bad_boys

    if not bad_boys: return points
    
    for bad in bad_boys:
        points.remove(bad)
    # print('phase_2', points)
    
    return points

def _combine_n_reduce(shape_a:list, shape_b:list):
    assert all((len(shape_a) > 2, len(shape_b) > 2)), 'Hulls need to be more than triangles'
    
    intersec = [p for p in shape_a if p in shape_b]
    inter_num = len(intersec)
    len_shape_a = len(shape_a)
    
    if inter_num < 2: return None
    
    for p in intersec:      ### 접점이 연속되지 않으면 병합 취소
        idx = shape_a.index(p)
        if shape_a[idx - 1] in intersec or shape_a[(idx + 1) % len_shape_a] in intersec:
            continue
        return None
    
    a_nob_in_intersec = shape_a[0] in intersec and shape_a[-1] in intersec
    '''
    첫 점과 끝 점이 포함되어 있으면 순서가 꼬이기 때문에 미리 알아둔다.
    '''
    for_debug = _reduce_points(shape_b)

    if inter_num > 2:       ### reduce intersec to each edge
        if intersec[0] == shape_a[0]:
            temp_inter = intersec[:]
            n = 1
            l_e, r_e = True, True
            idx = 0
            while intersec and (l_e or r_e):       ### I AM GENIUS
                if l_e and shape_a[n] not in temp_inter:
                    l_e = False
                if r_e and shape_a[-n] not in temp_inter:
                    r_e = False
                if l_e and shape_a[n - 1] in intersec:
                    intersec.remove(shape_a[n - 1])
                if r_e and shape_a[1 - n] in intersec:
                    intersec.remove(shape_a[1 - n])
                n += 1
    
            if not intersec:
                # intersec = [temp_inter[0], temp_inter[-1]]
                return None
                
                
            # n = 0
            # while shape_a[(n + 1) % len_shape_a] in temp_inter:
            #     intersec.remove(shape_a[n])
            #     n += 1
            # n = -1
            # while shape_a[n - 1] in temp_inter:
            #     intersec.remove(shape_a[n])
            #     n -= 1
    
    if a_nob_in_intersec:
        a_start = shape_a.index(intersec[0])
        a_end = shape_a.index(intersec[-1])
    else:
        a_start = shape_a.index(intersec[-1])
        a_end = shape_a.index(intersec[0])
    
    b_start = shape_b.index(shape_a[a_end])
    b_end = shape_b.index(shape_a[a_start])
    
    rest_a = rearrange(shape_a, a_start, a_end)
    rest_b = rearrange(shape_b, b_start, b_end)
    
    return rest_a + rest_b

def _reduce_shapes(shapes:list):
    count = len(shapes)
    if count < 2:
        return shapes, False
    
    for ia in range(count - 1):
        for ib in range(ia + 1, count):
            reduction = _combine_n_reduce(shapes[ia], shapes[ib])
            if reduction != None:
                # they can so return a new list of hulls and a True
                new_hulls = [reduction]
                for j in range(count):
                    if not (j in (ia, ib)):
                        new_hulls.append(shapes[j])
                return new_hulls, True

    # nothing was reduced, send the original hull list back with a False
    return shapes, False

def triangulate_all(shapes:list) -> list:
    triangles = []
    if len(shapes[0]) < 3:
        return pymunk.util.triangulate(shapes)
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
    # hulls = shapes[:]
    hulls = triangulate_all(shapes)
    reducing = True
    n = 0
    # keep trying to reduce until it won't reduce any more
    while reducing:
        hulls, reducing = _reduce_shapes(hulls)
        n += 1
    new_hulls = []
    for hull in hulls:
        new_hulls.append(_reduce_points(hull))
        
    return pymunk.util.convexise(triangulate_all(new_hulls))

def setup_shapes(
    body: pymunk.Body,
    collision_type = collision.default,
    shape_data: Union[float, list[Vector]] = None,
    shape_edge_radius: float = 0.0,
    shape_offset:Vector = vectors.zero,
    friction: float = None,
    elasticity: float = None,
    ) -> list[pymunk.Shape]:
    '''
    Note that shape_offset is working only on Circle type so far.
    '''
    def set_shapes_attr(shapes:list[pymunk.Shape]) -> list[pymunk.Shape]:
        for s in shapes:
            s.collision_type = collision_type
            if friction: s.friction = friction
            if elasticity: s.elasticity = elasticity
        return shapes
    
    if isinstance(shape_data, list):
        point_count = len(shape_data)
        if point_count < 2:
            raise PhysicsException(f'Shape constructor error : {shape_data}')
        if point_count == 2:
            shapes = [pymunk.Segment(body, *shape_data, shape_edge_radius),]
            return set_shapes_attr([
                pymunk.Segment(
                    body,
                    *shape_data, 
                    shape_edge_radius
                )
            ])
        ### For convex poly
        # if pymunk.util.is_convex(shape_data):
        #     return set_shapes_attr([
        #         pymunk.Poly(
        #             body,
        #             shape_data,
        #             radius = shape_edge_radius,
        #         )
        #     ])
        ### For concave / super complex poly
        convexes = get_convexes(shape_data)
        return set_shapes_attr([
            pymunk.Poly(body, c, radius=shape_edge_radius) 
            for c in convexes
        ])
    
    if isinstance(shape_data, (int, float)):
        return set_shapes_attr([
            pymunk.Circle(
                body, 
                shape_data + shape_edge_radius, 
                shape_offset
                )
        ])
    raise PhysicsException('Shape setup error')
    return None


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
    void_body = pymunk.Body()


class PhysicsException(Exception):
    pass


class __PhysicsObject(GameObject):
    '''
    Base physics object class coupled with pymunk body.
    
    Should be tested in case of removed : shapes, constraints should be removed also.
    
    :Parameter:
        `shape_data -> Union[float, list[Vector]]`
            raw data for shape. if it's float, shape will be circle with radius of it, else if list, will be poly
    '''
    
    __slots__ = '_body', '_initial_size', '_initial_mass', '_shape', '_scale', '_hidden', '_last_filter', '_original_poly', 
    
    def __init__(
        self,
        mass: float = 0,
        moment: float = None,
        body_type: pymunk.body._BodyType = pymunk.Body.DYNAMIC,
        collision_type = collision.default,
        shape_data: Union[float, list[Vector]] = None,
        shape_edge_radius: float = 0.0,
        shape_offset:Vector = vectors.zero,
        friction: float = 1.0,
        elasticity: float = None,
        position:Vector = None,
        angle:float = None,
        mass_scaling:bool = True,
        ) -> None:
        
        if body_type == pymunk.Body.STATIC:
            moment = physics_types.infinite
        else:
            # if shape_constructor == pymunk.Circle
            pass
        
        self._body = pymunk.Body(mass, moment, body_type)
        
        super().__init__()
        
        if position:
            self.position = position
        if angle:
            self.angle = angle
        
        ts = setup_shapes(
            body = self._body,
            collision_type = collision_type,
            shape_data = shape_data,
            shape_edge_radius = shape_edge_radius,
            shape_offset = shape_offset,
            friction = friction,
            elasticity = elasticity,
        )
        ''' Just making shapes will be added to `self.shapes` '''
        self._shape = ts[0]
        self._original_poly = shape_data if isinstance(shape_data, list) else None
        self._scale = 1.0
        self._hidden = False
        self._initial_size = self.size
        self._initial_mass = self.mass
        self._last_filter:pymunk.ShapeFilter = None
        self._mass_scaling = mass_scaling
    
    def spawn(self) -> GameObject:
        
        return super().spawn()
    
    def spawn_in_space(self, space: pymunk.Space) -> None:
        space.add(self._body, *self._body.shapes)
    
    def add_world_pivot(self, position : Vector) -> None:
        '''
        Example feature for dealing with constraints.
        '''
        if not self._body.space: 
            raise PhysicsException('Not yet added to space')
        self._body.space.add(
            pymunk.constraints.PivotJoint(self._body, self._body.space.static_body, position)
        )
    
    def draw(self, line_color = None, line_thickness = 1, fill_color = None):
        debug_draw_physics(self._body, line_color=line_color, line_thickness=line_thickness, fill_color=fill_color)
    
    def get_grounding(self):
        grounding = {
            'normal' : vectors.zero,
            'penetration' : vectors.zero,
            'impulse' : vectors.zero,
            'position' : vectors.zero,
            'body' : None
        }
        if self._body.space.gravity == (0,0): return grounding    ### no gravity, no grounding
        
        gravity_direction = Vector(self._body.space.gravity).unit
        
        def f(arbiter: pymunk.Arbiter):
            
            norm = Vector(arbiter.contact_point_set.normal)
            
            if gravity_direction + vectors.walkable_limit > norm > gravity_direction - vectors.walkable_limit:
                grounding['normal'] = norm
                grounding['penetration'] = -arbiter.contact_point_set.points[0].distance
                grounding['impulse'] = arbiter.total_impulse
                grounding['position'] = arbiter.contact_point_set.points[0].point_b
                grounding['body'] = arbiter.shapes[1].body
        
        self._body.each_arbiter(f)
        
        return grounding
    
    @property
    def is_on_ground(self) -> bool:
        return self.get_grounding()['body'] is not None

    @property
    def size(self) -> Union[float, Vector]:
        if not self._body.shapes: return 0
        if len(self._body.shapes) == 1:
            if isinstance(self._shape, pymunk.Circle):
                return self._shape.radius
            if isinstance(self._shape, pymunk.Segment):
                return (self._shape.a - self._shape.b).length
            return None
        cv = []
        for shape in self._body.shapes:
            if isinstance(shape, pymunk.Poly):
                cv.append(shape.get_vertices())
        bb = pymunk.Poly(body = physics_types.void_body, vertices = pymunk.util.convex_hull(get_all_points_from_shapes(cv))).bb
        return Vector(bb.left + bb.right, bb.top + bb.bottom)
    
    def _hide(self, switch:bool = None):
        if switch is None: switch = not self._hidden
        if switch: self._last_filter = self.filter
        self.filter = physics_types.filter_nomask if switch else self._last_filter
        return switch
    
    def _get_mass(self):
        return self._body.mass
    
    def _set_mass(self, mass:float):
        self._body.mass = mass
    
    mass:float = property(_get_mass, _set_mass)
    
    def _set_position(self, pos: Vector) -> None:
        self._body.position = pos

    def _get_position(self) -> Vector:
        return Vector(self._body.position)

    position = property(
        _get_position,
        _set_position,
        doc="""Position of the body.

        When changing the position you may also want to call
        :py:func:`Space.reindex_shapes_for_body` to update the collision 
        detection information for the attached shapes if plan to make any 
        queries against the space.""",
    )
    
    def _get_angle(self):
        return math.degrees(self._body.angle)
    
    def _set_angle(self, angle:float):
        self._body.angle = math.radians(angle)
    
    angle:float = property(_get_angle, _set_angle)
    
    def _get_velocity(self):
        return Vector(self._body.velocity)
    
    def _set_velocity(self, velocity:tuple[float, float]):
        self._body.velocity = velocity
    
    velocity:Vector = property(_get_velocity, _set_velocity)
    
    def _get_hidden(self):
        return self._hidden
    
    def _set_hidden(self, switch:bool = None):
        self._hidden = self._hide(switch)
        
    hidden:bool = property(_get_hidden, _set_hidden)
    
    def _get_filter(self):
        return self._shape.filter
    
    def _set_filter(self, filter):
        for shape in self._body.shapes:
            shape.filter = filter
    
    filter = property(_get_filter, _set_filter)
    
    def _get_scale(self):
        return self._scale
    
    def _set_scale(self, scale:float):
        ''' unsafe for real physics '''
        # if scale <= 0: raise PhysicsException     ## need something
        self._scale = scale
        
        if isinstance(self._shape, physics_types.circle):
            self._shape.unsafe_set_radius(self._initial_size * scale)
        else:
            ### totally unsafe...
            # self.shape.update(pymunk.Transform.scaling(scale))
            # if not self.hitbox: return False
            st = pymunk.Transform.scaling(scale)
            self._shape.unsafe_set_vertices(self._original_poly, st)
            if self._mass_scaling: self.mass = self._initial_mass * scale
    
    scale:float = property(_get_scale, _set_scale)
    ''' EXPERIMENTAL
    
    Scaling is not yet supported for multi-shape object.
    '''
    
    def _get_elasticity(self):
        return self._shape.elasticity
    
    def _set_elasticity(self, elasticity:float):
        for shape in self.shapes:
            shape.elasticity = elasticity
    
    elasticity:float = property(_get_elasticity, _set_elasticity)
    
    def _get_friction(self):
        return self._shape.friction
    
    def _set_friction(self, friction:float):
        for shape in self.shapes:
            shape.friction = friction
    
    friction:float = property(_get_friction, _set_friction)

    def _get_collision_type(self):
        ''' movement or hitbox? '''
        return self._shape.collision_type
    
    def _set_collision_type(self, collision_type:int):
        for shape in self._shape:
            shape.collision_type = collision_type
    
    collision_type = property(_get_collision_type, _set_collision_type)
    
    @property
    def speed(self):
        return self.velocity.length
    
    @property
    def space(self):
        return self._body.space
    

class PhysicsObject(pymunk.Body, GameObject):
    '''
    Base physics object class coupled with pymunk body.
    
    Should be tested in case of removed : shapes, constraints should be removed also.
    
    :Parameter:
        `shape_data -> Union[float, list[Vector]]`
            raw data for shape. if it's float, shape will be circle with radius of it, else if list, will be poly
    '''
    
    # __slots__ = '_initial_size', '_initial_mass', '_shape', '_scale', '_hidden', '_last_filter', '_original_poly', 
    
    def __init__(
        self,
        mass: float = 0,
        moment: float = None,
        body_type: pymunk.body._BodyType = pymunk.Body.DYNAMIC,
        collision_type = collision.default,
        shape_data: Union[float, list[Vector]] = None,
        shape_edge_radius: float = 0.0,
        shape_offset:Vector = vectors.zero,
        friction: float = 1.0,
        elasticity: float = None,
        position:Vector = None,
        angle:float = None,
        mass_scaling:bool = True,
        ) -> None:
        
        if body_type == pymunk.Body.STATIC:
            moment = physics_types.infinite
        else:
            # if shape_constructor == pymunk.Circle
            pass
        
        pymunk.Body.__init__(self, mass, moment, body_type)
        GameObject.__init__(self)
        
        if position:
            self.position = position
        if angle:
            self.angle = angle
        
        ts = setup_shapes(
            body = self,
            collision_type = collision_type,
            shape_data = shape_data,
            shape_edge_radius = shape_edge_radius,
            shape_offset = shape_offset,
            friction = friction,
            elasticity = elasticity,
        )
        ''' Just making shapes will be added to `self.shapes` '''
        self._shape = ts[0]
        self._original_poly = shape_data if isinstance(shape_data, list) else None
        self._scale = 1.0
        self._hidden = False
        self._initial_size = self.size
        self._initial_mass = self.mass
        self._last_filter:pymunk.ShapeFilter = None
        self._mass_scaling = mass_scaling
    
    def spawn(self) -> GameObject:
        
        return super().spawn()
    
    def spawn_in_space(self, space: pymunk.Space) -> None:
        space.add(self, *self.shapes)
    
    def add_world_pivot(self, position : Vector) -> None:
        '''
        Example feature for dealing with constraints.
        '''
        if not self.space: 
            raise PhysicsException('Not yet added to space')
        self.space.add(
            pymunk.constraints.PivotJoint(self, self.space.static_body, position)
        )
    
    def draw(self, line_color = None, line_thickness = 1, fill_color = None):
        debug_draw_physics(self, line_color=line_color, line_thickness=line_thickness, fill_color=fill_color)
    
    def get_grounding(self):
        grounding = {
            'normal' : vectors.zero,
            'penetration' : vectors.zero,
            'impulse' : vectors.zero,
            'position' : vectors.zero,
            'body' : None
        }
        if self.space.gravity == (0,0): return grounding    ### no gravity, no grounding
        
        gravity_direction = Vector(self.space.gravity).unit
        
        def f(arbiter: pymunk.Arbiter):
            
            norm = Vector(arbiter.contact_point_set.normal)
            
            if gravity_direction + vectors.walkable_limit > norm > gravity_direction - vectors.walkable_limit:
                grounding['normal'] = norm
                grounding['penetration'] = -arbiter.contact_point_set.points[0].distance
                grounding['impulse'] = arbiter.total_impulse
                grounding['position'] = arbiter.contact_point_set.points[0].point_b
                grounding['body'] = arbiter.shapes[1].body
        
        self.each_arbiter(f)
        
        return grounding
    
    @property
    def is_on_ground(self) -> bool:
        return self.get_grounding()['body'] is not None

    @property
    def size(self) -> Union[float, Vector]:
        if not self.shapes: return 0
        if len(self.shapes) == 1:
            if isinstance(self._shape, pymunk.Circle):
                return self._shape.radius
            if isinstance(self._shape, pymunk.Segment):
                return (self._shape.a - self._shape.b).length
            return None
        cv = []
        for shape in self.shapes:
            if isinstance(shape, pymunk.Poly):
                cv.append(shape.get_vertices())
        bb = pymunk.Poly(body = physics_types.void_body, vertices = pymunk.util.convex_hull(get_all_points_from_shapes(cv))).bb
        return Vector(bb.left + bb.right, bb.top + bb.bottom)
    
    def _hide(self, switch:bool = None):
        if switch is None: switch = not self._hidden
        if switch: self._last_filter = self.filter
        self.filter = physics_types.filter_nomask if switch else self._last_filter
        return switch
    
    def _set_position(self, pos: Vector) -> None:
        assert len(pos) == 2
        lib.cpBodySetPosition(self._body, pos)

    def _get_position(self) -> Vector:
        v = lib.cpBodyGetPosition(self._body)
        return Vector(v.x, v.y)

    position = property(
        _get_position,
        _set_position,
        doc="""Position of the body.

        When changing the position you may also want to call
        :py:func:`Space.reindex_shapes_for_body` to update the collision 
        detection information for the attached shapes if plan to make any 
        queries against the space.""",
    )
    
    def _get_hidden(self):
        return self._hidden
    
    def _set_hidden(self, switch:bool = None):
        self._hidden = self._hide(switch)
        
    hidden:bool = property(_get_hidden, _set_hidden)
    
    def _get_filter(self):
        return self._shape.filter
    
    def _set_filter(self, filter):
        for shape in self.shapes:
            shape.filter = filter
    
    filter = property(_get_filter, _set_filter)
    
    def _get_scale(self):
        return self._scale
    
    def _set_scale(self, scale:float):
        ''' unsafe for real physics '''
        # if scale <= 0: raise PhysicsException     ## need something
        self._scale = scale
        
        if isinstance(self._shape, physics_types.circle):
            self._shape.unsafe_set_radius(self._initial_size * scale)
        else:
            ### totally unsafe...
            # self.shape.update(pymunk.Transform.scaling(scale))
            # if not self.hitbox: return False
            st = pymunk.Transform.scaling(scale)
            self._shape.unsafe_set_vertices(self._original_poly, st)
            if self._mass_scaling: self.mass = self._initial_mass * scale
    
    scale:float = property(_get_scale, _set_scale)
    ''' EXPERIMENTAL
    
    Scaling is not yet supported for multi-shape object.
    '''
    
    def _get_elasticity(self):
        return self._shape.elasticity
    
    def _set_elasticity(self, elasticity:float):
        for shape in self.shapes:
            shape.elasticity = elasticity
    
    elasticity:float = property(_get_elasticity, _set_elasticity)
    
    def _get_friction(self):
        return self._shape.friction
    
    def _set_friction(self, friction:float):
        for shape in self.shapes:
            shape.friction = friction
    
    friction:float = property(_get_friction, _set_friction)

    def _get_collision_type(self):
        ''' movement or hitbox? '''
        return self._shape.collision_type
    
    def _set_collision_type(self, collision_type:int):
        for shape in self._shape:
            shape.collision_type = collision_type
    
    collision_type = property(_get_collision_type, _set_collision_type)


class PhysicsSpace(pymunk.Space):
    
    def __init__(
        self, 
        gravity: Vector = vectors.zero,
        damping: float = 0.01,
        threaded: bool = True,
        sleep_time_threshold: float = 5.0,
        idle_speed_threshold: float = 10.0,
        ) -> None:
        super().__init__(threaded)
        
        if threaded : self.threads = os.cpu_count() // 2  ### will not work above 2
        self.sleep_time_threshold = sleep_time_threshold
        self.idle_speed_threshold = idle_speed_threshold
    
    def add_static_collison(
        self, sprite_list,
        friction = 1.0,
        elasticity:float = None,
        collision_type = collision.default,
        shape_edge_raduis = 0.0,
        ) -> None:
        print('world static collision building')
        walls_points:list = []
        for sprite in tqdm(sprite_list):
            sprite:Sprite
            walls_points.append(sprite.get_adjusted_hit_box())
        
        shapes = setup_shapes(
            self.static_body, 
            collision_type = collision_type,
            shape_data = walls_points,
            friction = friction,
            elasticity = elasticity,
            )
        
        self.add(*shapes)
        return shapes
    
    def get_owners_from_arbiter(self, arbiter: pymunk.Arbiter) -> tuple[Optional[GameObject], Optional[GameObject]]:
        """ Given a collision arbiter, return the sprites associated with the collision. """
        shape1, shape2 = arbiter.shapes
        actor1 = shape1.body.owner
        actor2 = shape2.body.owner
        return actor1, actor2
    
    def add_collision_handler(
        self, 
        first_type:str,
        second_type:str, 
        begin_handler:Callable = None,
        pre_handler:Callable = None, 
        post_handler:Callable = None,
        separate_handler:Callable = None
        ) -> None:
        """ Add code to handle collisions between objects.
        
        A collision handler is a set of 4 function callbacks for the different
        collision events that Pymunk recognizes.

        Collision callbacks are closely associated with Arbiter objects. You
        should familiarize yourself with those as well.

        Note #1: Shapes tagged as sensors (`Shape.sensor == true`) never generate
        collisions that get processed, so collisions between sensors shapes and
        other shapes will never call the `post_solve()` callback. They still
        generate `begin()`, and `separate()` callbacks, and the `pre_solve()` callback
        is also called every frame even though there is no collision response.
        
        Note #2: `pre_solve()` callbacks are called before the sleeping algorithm
        runs. If an object falls asleep, its `post_solve()` callback won't be
        called until it's re-awoken.
        """
        
        def handler_begin(arbiter, space, data):
            actor1, actor2 = self.get_owners_from_arbiter(arbiter)
            should_process_collision = begin_handler(actor1, actor2, arbiter, space, data)
            return should_process_collision

        def handler_post(arbiter, space, data):
            actor1, actor2 = self.get_owners_from_arbiter(arbiter)
            if actor1 is not None and actor2 is not None:
                post_handler(actor1, actor2, arbiter, space, data)

        def handler_pre(arbiter, space, data):
            actor1, actor2 = self.get_owners_from_arbiter(arbiter)
            return pre_handler(actor1, actor2, arbiter, space, data)

        def handler_separate(arbiter, space, data):
            actor1, actor2 = self.get_owners_from_arbiter(arbiter)
            separate_handler(actor1, actor2, arbiter, space, data)
        
        h = self.add_collision_handler(first_type, second_type)
        
        if begin_handler:
            h.begin = handler_begin
        if post_handler:
            h.post_solve = handler_post
        if pre_handler:
            h.pre_solve = handler_pre
        if separate_handler:
            h.separate = handler_separate
    
    def sync(self):
        pass
    
    def step(self, dt: float) -> None:
        """Update the space for the given time step.

        Using a fixed time step is highly recommended. Doing so will increase
        the efficiency of the contact persistence, requiring an order of
        magnitude fewer iterations to resolve the collisions in the usual case.

        It is not the same to call step 10 times with a dt of 0.1 and
        calling it 100 times with a dt of 0.01 even if the end result is
        that the simulation moved forward 100 units. Performing  multiple
        calls with a smaller dt creates a more stable and accurate
        simulation. Therefor it sometimes make sense to have a little for loop
        around the step call, like in this example:

        >>> import pymunk
        >>> s = pymunk.Space()
        >>> steps = 10
        >>> for x in range(steps): # move simulation forward 0.1 seconds:
        ...     s.step(0.1 / steps)

        :param dt: Time step length
        """
        def dp():
            db = self.dynamics
            for d in db:
                print(d, d.body.position)
        try:
            self._locked = True
            dp()
            if self.threaded:
                cp.cpHastySpaceStep(self._space, dt)
            else:
                cp.cpSpaceStep(self._space, dt)
            dp()
            self._removed_shapes = {}
        finally:
            self._locked = False

        self.add(*self._add_later)
        self._add_later.clear()
        for obj in self._remove_later:
            self.remove(obj)
        self._remove_later.clear()

        for key in self._post_step_callbacks:
            self._post_step_callbacks[key](self)

        self._post_step_callbacks = {}
    
    @property
    def dynamics(self) -> list[GameObject]:
        ''' Returns GameObjects which have DYNAMIC body. 
        
        Not recommended to use frequently
        '''
        return [b.owner for b in self.bodies if b.body_type == pymunk.Body.DYNAMIC and hasattr(b, 'owner')]
    
    @property
    def statics(self) -> list[GameObject]:
        ''' Returns GameObjects which have STATIC body. 
        
        Not recommended to use frequently
        '''
        return [b.owner for b in self.bodies if b.body_type == pymunk.Body.STATIC and hasattr(b, 'owner')]
    
    @property
    def kinematics(self) -> list[GameObject]:
        ''' Returns GameObjects which have KINEMATIC body. 
        
        Not recommended to use frequently
        '''
        return [b.owner for b in self.bodies if b.body_type == pymunk.Body.KINEMATIC and hasattr(b, 'owner')]
