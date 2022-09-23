from __future__ import annotations

import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from pymunk.util import is_convex
from lib.foundation.vector import Vector as v
from typing import Callable

def _attempt_reduction(hulla, hullb):
    inter = [vec for vec in hulla if vec in hullb]
    if len(inter) == 2:
        starta = hulla.index(inter[1])
        tempa = hulla[starta:] + hulla[:starta]
        tempa = tempa[1:-1]
        startb = hullb.index(inter[0])
        tempb = hullb[startb:] + hullb[:startb]
        tempb = tempb[1:-1]
        reduced = tempa + tempb
        if is_convex(reduced):
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
            
def get_convexes(shapes):
    """Reduces a list of shapes to a
    non-optimum list of convex polygons

    :Parameters:
        triangles
            list of anticlockwise triangles (a list of three points) to reduce
    """
    # fun fact: convexise probably isn't a real word
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
    return hulls

a = [v(0,0), v(10,0), v(10,10), v(0,10)]
b = [v(10,0), v(20,0), v(20,10), v(10,10)]
c = [v(10,10), v(20,10), v(20,20), v(10,20)]
d = [v(0,0), v(0,10), v(-10,10), v(-10,0)]
e = [v(10,20), v(20,20), v(20,30), v(10,30)]
f = [v(10,20), v(10,30), v(0,30), v(0,20)]

boxes = [a, b, c]

get_convexes(boxes)