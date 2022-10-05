import math
from typing import Callable, Optional, Union

import pymunk, pymunk.util

from .base import *
from .vector import *
from .utils import *
from .engine.primitive import Sprite
from .engine.object import *

from config.engine import *


def setup_shapes(
    body: pymunk.Body,
    collision_type = collision.default,
    elasticity: float = None,
    friction: float = 1.0,
    shape_type = pymunk.Poly,
    shape_edge_radius: float = 0.0,
    shape_offset:Vector = vectors.zero,
    ) -> list[pymunk.Shape]:
    
    pass


@dataclass
class ptypes:

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


class PhysicsException(Exception):
    pass


class PhysicsObject(pymunk.Body, GameObject):
    '''
    Base physics object class coupled with pymunk body.
    
    Should be tested in case of removed : shapes, constraints should be removed also.
    
    '''
    
    __slots__ = '_initial_mass', '_scale', '_hidden', '_last_filter'
    
    def __init__(
        self,
        mass: float = 0,
        moment: float = 0,
        body_type: pymunk.body._BodyType = pymunk.Body.DYNAMIC,
        collision_type = collision.default,
        elasticity: float = None,
        friction: float = 1.0,
        shape_type = pymunk.Poly,
        shape_edge_radius: float = 0.0,
        shape_offset:Vector = vectors.zero,
        ) -> None:
        pymunk.Body.__init__(self, mass, moment, body_type)
        GameObject.__init__(self)

        
        
        self._scale = 1.0
        self._hidden = False
        self._initial_mass = self.mass
        self._last_filter:pymunk.ShapeFilter = self.filter
    
    def spawn_in_space(self):
        self.space.add(self, *self.shapes)
    
    def add_world_pivot(self, position : Vector):
        '''
        Example feature for dealing with constraints.
        '''
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

    def _hide(self, switch:bool = None):
        if switch is None: switch = not self._hidden
        if switch: self._last_filter = self.filter
        self.filter = ptypes.filter_nomask if switch else self._last_filter
        return switch
    
    def _get_hidden(self):
        return self._hidden
    
    def _set_hidden(self, switch:bool = None):
        self._hidden = self._hide(switch)
        
    hidden:bool = property(_get_hidden, _set_hidden)
    
    def _get_filter(self):
        return self.shapes[0].filter
    
    def _set_filter(self, filter):
        for shape in self.shapes:
            shape.filter = filter
    
    filter = property(_get_filter, _set_filter)
    
    def _get_elasticity(self):
        return self.shapes[0].elasicity
    
    def _set_elasticity(self, elasticity:float):
        for shape in self.shapes:
            shape.elasticity = elasticity
    
    elasticity:float = property(_get_elasticity, _set_elasticity)
    
    def _get_friction(self):
        return self.shapes[0].friction
    
    def _set_friction(self, friction:float):
        for shape in self._shape:
            shape.friction = friction
    
    friction:float = property(_get_friction, _set_friction)

    def _get_collision_type(self):
        ''' movement or hitbox? '''
        return self.shapes[0].collision_type
    
    def _set_collision_type(self, collision_type:int):
        for shape in self._shape:
            shape.collision_type = collision_type
    
    collision_type = property(_get_collision_type, _set_collision_type)
    