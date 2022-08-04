"""
Functions for calculating geometry.
"""

from typing import cast

from arcade import PointList, Point, get_distance


_PRECISION = 2

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
            if abs(projection) <= radius: return True
            
        # if projection <= radius: 
        #     print(p, p1, p2, d12, projection)
        #     return True
        
    
    return False

def are_polygons_intersecting(poly_a: PointList,
                              poly_b: PointList) -> bool:
    """
    Return True if two polygons intersect.

    :param PointList poly_a: List of points that define the first polygon.
    :param PointList poly_b: List of points that define the second polygon.
    :Returns: True or false depending if polygons intersect

    :rtype bool:
    """

    for polygon in (poly_a, poly_b):

        for i1 in range(len(polygon)):
            i2 = (i1 + 1) % len(polygon)
            projection_1 = polygon[i1]
            projection_2 = polygon[i2]

            normal = (projection_2[1] - projection_1[1],
                      projection_1[0] - projection_2[0])

            min_a, max_a, min_b, max_b = (None,) * 4

            for poly in poly_a:
                projected = normal[0] * poly[0] + normal[1] * poly[1]

                if min_a is None or projected < min_a:
                    min_a = projected
                if max_a is None or projected > max_a:
                    max_a = projected

            for poly in poly_b:
                projected = normal[0] * poly[0] + normal[1] * poly[1]

                if min_b is None or projected < min_b:
                    min_b = projected
                if max_b is None or projected > max_b:
                    max_b = projected

            if cast(float, max_a) <= cast(float, min_b) or cast(float, max_b) <= cast(float, min_a):
                return False

    return True


def is_point_in_polygon(x, y, polygon_point_list):
    """
    Use ray-tracing to see if point is inside a polygon

    Args:
        x:
        y:
        polygon_point_list:

    Returns: bool

    """
    n = len(polygon_point_list)
    inside = False
    if n == 0:
        return False

    p1x, p1y = polygon_point_list[0]
    for i in range(n + 1):
        p2x, p2y = polygon_point_list[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xints = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    # noinspection PyUnboundLocalVariable
                    if p1x == p2x or x <= xints:
                        inside = not inside
        p1x, p1y = p2x, p2y

    return inside
