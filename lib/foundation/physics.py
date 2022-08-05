'''
very simple physics code injection by mash

'''
import sys

import arcade
from arcade import (Point, 
                    PointList, 
                    is_point_in_polygon, 
                    get_distance, 
                    Sprite, 
                    are_polygons_intersecting
                    )

def is_polygon_intersecting_with_circle(poly: PointList, p: Point, radius: float):
    # print(poly, position, radius)
    
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
                print('sides check [colliding]')
                return True
            # print('sides check [not colliding]')
            
        # if projection <= radius: 
        #     print(p, p1, p2, d12, projection)
        #     return True
        
    
    return False

def foo(sprite1: Sprite, sprite2: Sprite) -> bool:
    print('foooo')
    return False

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


arcade.sprite_list.spatial_hash._check_for_collision = _check_for_collision