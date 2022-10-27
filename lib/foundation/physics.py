from __future__ import annotations
'''
(only coupled with pymunk in this file)
'''

import pickle
import math
from typing import Callable, Optional, Union

import pymunk, pymunk.util

from .base import *
from .vector import *
from .utils import *
# from .engine.primitive import Sprite
from .engine.object import *

from config.engine import *


def get_all_points_from_shapes(shapes):
    return [point for shape in shapes for point in shape]

def build_convex_shape(body:physics_types.body, points_list:set[list]) -> list[physics_types.poly]:
    #DEPRECATED
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

def _reduce_points(points:list[Vector]) -> list[Vector]:
    
    points = [Vector(x) for x in points]
    # points = list(dict.fromkeys(points))      ### 중복 포인트는 제거하지 않는다. 혹시라도 concave에서 겹치는게 있을 수 있음.

    num = len(points)
    if num < 3:
        raise AttributeError('need more than 3 points')
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
    if len(shapes[0]) == 2 and all(isinstance(x, (float, int)) for x in shapes[0]):     ### not cool...
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

def count_first_shape_points(shape, elements:int = 2) -> int:
    '''
    useless for now
    '''
    if not shape: return 0
    l1 = len(shape)
    s0 = shape[0]
    if l1 == elements and isinstance(s0, (int, float)):
        ''' get to the point '''
        return None
    if count_first_shape_points(s0) is None:
        return l1
    return count_first_shape_points(s0)

def get_owner(
    obj: Union[PhysicsObject, pymunk.Body, pymunk.Shape, Sprite]
    ) -> Union[GameObject, PhysicsSpace, None]:
    
    if isinstance(obj, pymunk.Shape):
        obj = obj.body
    
    if isinstance(obj, GameObject):
        return obj.owner
    
    if hasattr(obj, 'owner'):
        return getattr(obj, 'owner')
    
    if isinstance(obj, pymunk.Body) and obj.body_type == physics_types.static:
        return obj.space
    
    return None

def get_merged_convexes(sprite_list):
    ''' Returns merged convexes from sprite list '''
    walls_points:list = []
    for sprite in tqdm(sprite_list):
        sprite:Sprite
        walls_points.append(sprite.get_adjusted_hit_box())
    
    return get_convexes(walls_points)

def setup_shapes(
    body: PhysicsObject,
    collision_type = collision.default,
    shape_data: Union[float, list] = None,
    shape_edge_radius: float = 0.0,
    shape_offset:Vector = vectors.zero,
    friction: float = None,
    elasticity: float = None,
    ) -> list[pymunk.Shape]:
    '''
    Note that shape_offset is working only on Circle type so far.
    '''
    assert shape_data is not None, f'{body} can\'t make shape with empty data'
    
    def set_shapes_attr(shapes:list[pymunk.Shape]) -> list[pymunk.Shape]:
        for s in shapes:
            s.collision_type = collision_type
            s.filter = pymunk.ShapeFilter(categories=collision_type)    ### set collision type to filter
            if friction: s.friction = friction
            if elasticity: s.elasticity = elasticity
            PhysicsSpace._temp_shapes.add(s)
        return shapes
    
    if isinstance(shape_data, list):
        first = shape_data[0]
        if len(first) == 2 and all(isinstance(x, (float, int)) for x in first): ### for single shape
            point_count = len(shape_data)
            ### shape should have more than 2 points
            if point_count < 2:
                raise PhysicsException(f'Shape constructor error : {shape_data}')
            ### if segment
            if point_count == 2:
                # shapes = [pymunk.Segment(body, *shape_data, shape_edge_radius),]
                return set_shapes_attr([
                    pymunk.Segment(
                        body,
                        *shape_data, 
                        shape_edge_radius
                    )
                ])
            ### For concave poly
            if not pymunk.util.is_convex(shape_data):
                return set_shapes_attr([
                    pymunk.Poly(body, c, radius=shape_edge_radius)
                    for c in pymunk.util.convexise(pymunk.util.triangulate(shape_data))
                ])
            ### For convex poly
            return set_shapes_attr([
                pymunk.Poly(
                    body,
                    shape_data,
                    radius = shape_edge_radius,
                )
            ])
        ### For multiple shapes
        
        # convexes = get_convexes(shape_data)
        
        return set_shapes_attr([
            pymunk.Poly(body, c, radius=shape_edge_radius) 
            for c in shape_data
        ])
    ### for circle shape
    if isinstance(shape_data, (int, float)):
        return set_shapes_attr([
            pymunk.Circle(
                body, 
                shape_data + shape_edge_radius, 
                shape_offset
                )
        ])
    # raise PhysicsException('Shape setup error')
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
    

class PhysicsObject(pymunk.Body, GameObject):
    '''
    Base physics object class coupled with pymunk body.
    
    Should be tested in case of removed : shapes, constraints should be removed also.
    
    :Parameter:
        `shape_data -> Union[float, list[Vector]]`
            raw data for shape. if it's float, shape will be circle with radius of it, else if list, will be poly
    '''
    
    __slots__ = '_initial_size', '_initial_mass', '_shape', '_scale', '_hidden', '_last_filter', '_original_poly', 
    
    def __init__(
        self,
        mass: float = 1,
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
        
        assert mass != 0, 'mass error'
        if moment is None: moment = 1
        
        pymunk.Body.__init__(self, mass, moment, body_type)
        GameObject.__init__(self)
        
        if position:
            self.position = position
        if angle:
            self.angle = angle
        
        setup_shapes(
            body = self,
            collision_type = collision_type,
            shape_data = shape_data,
            shape_edge_radius = shape_edge_radius,
            shape_offset = shape_offset,
            friction = friction,
            elasticity = elasticity,
        )
        ''' Just making shapes will be added to `self.shapes` '''
        self._shape = list(self.shapes)[0]
        self._original_poly = shape_data if isinstance(shape_data, list) else None
        self._scale = 1.0
        self._hidden = False
        self._initial_mass = self.mass
        self._last_filter:pymunk.ShapeFilter = None
        self._initial_size = self.size
        self._mass_scaling = mass_scaling
    
    def __repr__(self) -> str:
        return f'PhysicsObject({self._id})'
    
    def spawn_in_space(self, space: pymunk.Space) -> None:
        space.add(self, *self.shapes)
        return self
    
    def add_world_pivot(self, position: Vector = None) -> None:
        '''
        Example feature for dealing with constraints.
        '''
        if not self.space: 
            raise PhysicsException('Not yet added to space')
        
        if position is None:
            position = self.position
        
        self.space.add(
            pymunk.constraints.PivotJoint(self, self.space.static_body, position)
        )
    
    def draw(self, line_color = (255,0,255,128), line_thickness = 1, fill_color = None):
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
    
    def destroy(self) -> None:
        self.space.remove(*self.shapes, self)
        return GameObject.destroy(self)
    
    @property
    def is_on_ground(self) -> bool:
        return self.get_grounding()['body'] is not None

    @property
    def size(self) -> Union[float, Vector]:
        if not self.shapes: return 0
        # return Vector(abs(self.bb.right - self.bb.left), abs(self.bb.top - self.bb.bottom))
        if len(self.shapes) == 1:
            if isinstance(self._shape, pymunk.Circle):
                return self._shape.radius
            if isinstance(self._shape, pymunk.Segment):
                return (self._shape.a - self._shape.b).length
            return None
        cv = []
        for shape in self.shapes:
            if isinstance(shape, pymunk.Poly):
                cv.extend(shape.get_vertices())
        cp = pymunk.util.calc_center(pymunk.util.convex_hull(cv))
        mxl = 0
        for p in cv:
            mxl = max(mxl, get_distance(*cp, *p))
        mnl = mxl
        for p in cv:
            mnl = min(mnl, get_distance(*cp, *p))
        return Vector().diagonal((mnl + mxl) / 2)
        
        # bb = pymunk.Poly(body = physics_types.void_body, vertices = pymunk.util.convex_hull(cv)).bb
        # return Vector(bb.left + bb.right, bb.top + bb.bottom)
    
    def _hide(self, switch:bool = None):
        if switch is None: switch = not self._hidden
        if switch: self._last_filter = self.filter
        self.filter = physics_types.filter_nomask if switch else self._last_filter
        return switch
    
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
        ''' UNSAFE for real physics, NOT working with multi-shape body '''
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
    ''' EXPERIMENTAL, UNSAFE
    
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
    '''
    Extended space object.
    
    Be careful with `threaded` option. 
    Will not use for release build because not so effective for its own risk.
    '''
    
    _temp_shapes: set[pymunk.Shape] = set()
    '''
    Maybe since the weakref of body and shape, 
    `body.shapes` can't retain its shapes unless add to space
    right after they're made.
    
    So add them to temp set and remove(discard) while adding to space.
    '''
    def __init__(
        self, 
        gravity: Vector = None,
        damping: float = 0.01,
        threaded: bool = False,
        sleep_time_threshold: float = 5.0,
        idle_speed_threshold: float = 10.0,
        ) -> None:
        super().__init__(threaded)
        
        if threaded : self.threads = os.cpu_count() // 2  ### will not work above 2
        self.sleep_time_threshold = sleep_time_threshold
        self.idle_speed_threshold = idle_speed_threshold
        
        if gravity is not None: self.gravity = gravity
        if damping is not None: self.damping = damping
        
        self._movable_objs: set[PhysicsObject] = set()
        self._static_objs: set[PhysicsObject] = set()
    
    def add(self, *objs: pymunk.space._AddableObjects) -> None:

        if not objs: return
        '''
        For better performance (not quite much though)
        If adding problem raised, remove a line above
        '''
        
        if self._locked:
            self._add_later.update(objs)
            return
        
        for o in objs:
            if isinstance(o, PhysicsObject) and o.body_type in (pymunk.Body.DYNAMIC, pymunk.Body.KINEMATIC):
                self._movable_objs.add(o)
            if isinstance(o, PhysicsObject) and o.body_type == pymunk.Body.STATIC:
                self._static_objs.add(o)
            if isinstance(o, pymunk.Shape):
                PhysicsSpace._temp_shapes.discard(o)
        
        return super().add(*objs)
    
    def remove(self, *objs: pymunk.space._AddableObjects) -> None:
        # print("PHY RMV JOB")
        
        if self._locked:
            self._remove_later.update(objs)
            return
        
        for o in objs:
            if isinstance(o, PhysicsObject):
                self._movable_objs.discard(o)
                self._static_objs.discard(o)
        
        return super().remove(*objs)
    
    def add_static_collison(
        self, 
        shape_data,
        friction = 1.0,
        elasticity:float = None,
        collision_type = collision.default,
        shape_edge_raduis = 0.0,
        ) -> None:
        print('world static collision building')
        
        # with open('data/static_collision.data', 'rb') as f:
        #     a = pickle.load(f, )
        #     self.add(*a)
        #     return a
        
        # walls_points:list = []
        # for sprite in tqdm(sprite_list):
        #     sprite:Sprite
        #     walls_points.append(sprite.get_adjusted_hit_box())
        
        # print(hash(frozenset(walls_points)))
        
        shapes = setup_shapes(
            self.static_body, 
            collision_type = collision_type,
            shape_data = shape_data,
            friction = friction,
            elasticity = elasticity,
            )
        
        # with open('data/static_collision.data', 'wb') as f:
            # pickle.dump(shapes, f)
                
        self.add(*shapes)
        return shapes
    
    def set_world_static(
        self,
        
    ):
        pass
    
    def get_owners_from_arbiter(self, arbiter: pymunk.Arbiter) -> tuple[Optional[GameObject], Optional[GameObject]]:
        """ Given a collision arbiter, return the shapes associated with the collision. """
        return arbiter.shapes
        # shape1, shape2 = arbiter.shapes
        # actor1 = shape1.body.owner if hasattr(shape1.body, 'owner') else self.static_body
        # actor2 = shape2.body.owner if hasattr(shape1.body, 'owner') else self.static_body
        # return actor1, actor2
    
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
            shape1, shape2 = self.get_owners_from_arbiter(arbiter)
            should_process_collision = begin_handler(shape1, shape2, arbiter, space, data)
            return should_process_collision

        def handler_post(arbiter, space, data):
            shape1, shape2 = self.get_owners_from_arbiter(arbiter)
            if shape1 is not None and shape2 is not None:
                return post_handler(shape1, shape2, arbiter, space, data)

        def handler_pre(arbiter, space, data):
            shape1, shape2 = self.get_owners_from_arbiter(arbiter)
            return pre_handler(shape1, shape2, arbiter, space, data)

        def handler_separate(arbiter, space, data):
            shape1, shape2 = self.get_owners_from_arbiter(arbiter)
            return separate_handler(shape1, shape2, arbiter, space, data)
        
        h = super().add_collision_handler(first_type, second_type)
        
        if begin_handler:
            h.begin = handler_begin
        if post_handler:
            h.post_solve = handler_post
        if pre_handler:
            h.pre_solve = handler_pre
        if separate_handler:
            h.separate = handler_separate
    
    def activate_objects(self):
        for o in self._movable_objs:
            o.activate()
    
    def debug_draw_movable_collision(
        self,
        line_color = (255, 255, 0, 255),
        line_thickness = 1,
        fill_color = None,
        ):
        for o in self._movable_objs:
            o.draw(
                line_color=line_color,
                line_thickness=line_thickness,
                fill_color=fill_color
            )
    
    def debug_draw_static_collision(
        self,
        line_color = (255, 0, 255, 255),
        line_thickness = 1,
        fill_color = None,
        ):
        
        debug_draw_physics(
            self.static_body, 
            line_color=line_color,
            line_thickness=line_thickness,
            fill_color=fill_color)
        for o in self._static_objs:
            o.draw(
                line_color=line_color,
                line_thickness=line_thickness,
                fill_color=fill_color
            )
    
    def sync(self):
        
        for o in self._movable_objs:
            if o.spawnned: o._owner._sync()        ### Not so robust method
            
    def tick(self, delta_time: float, sync: bool = True):
        # for _ in range(5):
        #     self.step(1/300)
        
        self.step(delta_time)
        if sync: self.sync()
    
    @property
    def movables(self) -> list[GameObject]:
        ''' Returns GameObjects which have DYNAMIC body. Fast, recommended for use. '''
        return [o.owner for o in self._movable_objs]
    
    @property
    def dynamics(self) -> list[GameObject]:
        ''' Returns GameObjects which have DYNAMIC body. '''
        return [o.owner for o in self._movable_objs if o.body_type == pymunk.Body.DYNAMIC]
    
    @property
    def statics(self) -> list[GameObject]:
        ''' Returns GameObjects which have STATIC body. 
        
        Not recommended to use frequently
        '''
        return [o.owner for o in self.bodies if o.body_type == pymunk.Body.STATIC and hasattr(o, 'owner')]
    
    @property
    def kinematics(self) -> list[GameObject]:
        ''' Returns GameObjects which have KINEMATIC body. '''
        return [o.owner for o in self._movable_objs if o.body_type == pymunk.Body.KINEMATIC]
