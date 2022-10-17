"""
base feature codes
joonhyuk@me.com
"""
import os, sys, json

from enum import Enum
from typing import Iterable, Union
from collections import deque
from tqdm import tqdm

from easing_functions import *

# from config import *
from .vector import Vector, vectors
from .dice import *
import math

cubic_easeinout = CubicEaseInOut()

class EnumVector(Vector, Enum):
    __class__ = Vector
    
    def __repr__(self) -> Vector:
        return self.value
    
    
class SingletonType(type):
    def __call__(cls, *args, **kwargs):
        try:
            return cls.__instance
        except AttributeError:
            cls.__instance = super().__call__(*args, **kwargs)
            return cls.__instance


class PropertyFrom:
    
    __slots__ = ['proxied', 'name']
    
    def __init__(self, proxied) -> None:
        self.proxied = proxied
    
    def __set_name__(self, owner, name):
        ### 디스크립터는 클래스 정의 과정에서 실행되기 때문에 
        ### __dict__, __slots__서 찾을 수 없는 시점에 체크하게 된다. 
        ### __slots__를 미리 정의해두면 문제가 없지만 늘 그럴 수는 없으므로 삭제
        ### get 과정에서 체크하면 성능에서 손해.
        
        # if not hasattr(owner, self.proxied):
        #     raise AttributeError(f"'{owner}' has no attribute '{self.proxied}'")
        # if not hasattr(getattr(owner, self.proxied), name):
        #     raise AttributeError(f"'{getattr(owner, self.proxied)}' has no attribute '{name}'")
        self.name = name
    
    def __get__(self, owner, objtype):
        return getattr(getattr(owner, self.proxied), self.name, None)
    
    def __set__(self, owner, value):
        setattr(getattr(owner, self.proxied), self.name, value)


class Version(metaclass=SingletonType):
    '''planned to convert into singleton class'''
    def __init__(self, major:int = None, minor:int = None, patch:int = None, is_production = False, file = 'data/version.json', run_count_up = True) -> None:
        import json
        self.path = get_path(file)
        
        try:
            with open(self.path) as self.version_file:
                self.data = json.load(self.version_file)
                if run_count_up and not is_production:
                    self.data['run_count'] += 1
                if major is not None: self.data['major'] = major
                if minor is not None: self.data['minor'] = minor
                if patch is not None: self.data['patch'] = patch
            self._write(self.data)

        except:
            print('Version file unavailable. Create new one')
            from collections import OrderedDict
            new_json = OrderedDict()
            new_json['major'] = 0
            new_json['minor'] = 1
            new_json['patch'] = 0
            new_json['tag'] = 'initial'
            new_json['run_count'] = 1
            self.data = new_json
            self._write(self.data)
        
        if not is_production:
            debug_str = '-dev'
            self.exec = ' build#' + str(self.data['run_count'])
        else:
            debug_str = self.exec = ''
        
        self.body = '.'.join((str(self.data['major']), 
                              str(self.data['minor']), 
                              str(self.data['patch'])))
        self.tail = self.data['tag'] + debug_str + '@' + sys.platform
        self.full = '.'.join((self.body, self.tail))
        if not is_production:
            self.full += self.exec
    
    def _write(self, data):
        import json
        with open(get_path(self.path), "w") as version_file:
            json.dump(data, version_file, indent = '\t')
     
    def __str__(self):
        return self.body
    def __repr__(self):
        return self.__str__()


def get_path(path):
    """return proper path for packaging platform"""
    if sys.platform == 'darwin': return path
    if getattr(sys, 'frozen', False):
        # running in bundle
        return os.path.join(sys._MEIPASS, path)
    else:
        return path

def get_iter(arg, return_type:type = tuple) -> Iterable:
    """return iterable(default : tuple)"""
    if isinstance(arg, str) or not isinstance(arg, Iterable):
        if return_type is tuple:
            return (arg, )
        if return_type is list:
            return [arg]
    if isinstance(arg, Iterable):
        return arg
    
def finterp_to(current:float, 
               target:float, 
               delta_time:float, 
               speed:float = 1.0, 
               precision:float = 0.001):
    if speed <= 0: return target
    delta = target - current
    if abs(delta) < precision: return target
    return current + delta * clamp(delta_time * speed, 0, 1)

def vinterp_to(current:Vector,
               target:Vector,
               delta_time:float, 
               speed:float = 1.0, 
               precision:float = 0.001):
    if speed <= 0: return target
    delta = target - current
    if delta.norm() < precision: return target
    return current + delta * clamp(delta_time * speed, 0, 1)

def rinterp_to(current:float, 
               target:float,
               delta_time:float, 
               speed:float = 1.0,
               precision:float = 0.001):
    '''rotation angle interp. in degrees'''
    delta = get_shortest_angle(current, target)
    speedo = map_range(abs(delta), 15, 90, 3, 1, clamped=True)
    # print(speedo)
    if abs(delta) < precision: return target
    a = delta * clamp(delta_time * speed * speedo, 0, 1)
    # if abs(a) > 180 * delta_time:
    #     if a < 0: a = -180 * delta_time
    #     else: a = 180 * delta_time
    # print(a // delta_time)
    return current + a

def get_shortest_angle(start:float,
                       end:float):
    return ((end - start) + 180) % 360 - 180

def get_positive_angle(degrees:float):
    '''convert angle in degrees to 0 <= x < 360'''
    degrees = get_shortest_angle(0, degrees)
    if degrees < 0: degrees += 360
    return degrees

def clamp(value, in_min = None, in_max = None):
    if in_min > in_max: raise ValueError('in_min > in_max')
    # if in_min is None: return min(value, in_max)
    # if in_max is None: return max(value, in_min)
    # return min(in_max, max(in_min, value))
    ''' optimized '''
    if in_min is not None and value < in_min: return in_min
    if in_max is not None and value > in_max: return in_max
    return value

def clamp_abs(value, in_min, in_max):
    result = min(abs(in_max), max(abs(in_min), abs(value)))
    if value < 0 : result *= -1
    return result

def map_range(value, in_min, in_max, out_min, out_max, clamped = False):
    if clamped: value = clamp(value, in_min, in_max)
    return ((value - in_min) / (in_max - in_min)) * (out_max - out_min) + out_min

def map_range_abs(value, in_min, in_max, out_min, out_max, clamped = False):
    if clamped: value = clamp_abs(value, in_min, in_max)
    result = map_range(abs(value), in_min, in_max, out_min, out_max)
    if value < 0: result *= -1
    return result

def map_range_attenuation(value, in_min, in_max, out_start, out_min, out_max):
    ''' need to be revised '''
    if value < in_min:
        return map_range(value, 0, in_min, out_start, out_min)
    return map_range(value, in_min, in_max, out_min, out_max)

def load_json(filepath:str) -> dict:
    with open(get_path(filepath), 'r') as json_file:
        return json.load(json_file)

def save_json(filepath:str, json_data) -> None:
    with open(get_path(filepath), 'w') as json_file:
        json.dump(json_data, json_file, indent = 4)

def get_from_dict(dict:dict, keyword:str, default:... = None):
    if keyword in dict:
        return dict[keyword]
    return default

def map_range_easing(value, in_min, in_max, out_min, out_max, clamped=False, easing_class = LinearInOut):
    return easing_class(out_min, out_max)(map_range(value, in_min, in_max, 0, 1, clamped))

def get_curve_value(x:float, curve:dict, easing_class = LinearInOut):
    '''
    Get unreal style curve value from dict data.
    Keys could be float, int, 'rclamp', 'lclamp'
    i.e. curve = {0:0, 1:1, 'rclamp':True, 'lclamp':True}
    rclamp / lclamp: clamping to right / left end value
        
    easing_class referes to easing-functions module
    '''
    
    keys = curve.keys()
    dots = []
    for key in keys:
        if isinstance(key, (float, int)):
            dots.append(key)
    rclamp = get_from_dict(curve, 'rclamp')
    lclamp = get_from_dict(curve, 'lclamp')
    
    if len(dots) == 1: return curve[dots[0]]
    if x in dots: return curve[x]
    
    dots.append(x)
    dots.sort()
    idx_x = dots.index(x)
    
    def gcv(dots_idx:int):
        ''' get curve value from the index of x '''
        return curve[dots[dots_idx]]
    
    if idx_x == 0:     ### if x is the first value
        if lclamp: return curve[dots[1]]    ### return clamped value
        id_start, id_end = 1, 2
    elif idx_x == len(dots) - 1:     ### if x is the last value
        if rclamp: return curve[dots[-2]]    ### return clamped value
        id_start, id_end = -3, -2
    else:
        id_start, id_end = idx_x - 1, idx_x + 1
    
    alpha = map_range(dots[idx_x], dots[id_start], dots[id_end], 0, 1)
    
    y_start = curve[dots[id_start]]
    y_end = curve[dots[id_end]]
    
    return easing_class(y_start, y_end)(alpha)

def avg_generator(value, num_limit:int = 10):
    '''
    generator for average value
    
    usage;
    
    foo = avg_generator(initial value, limitation)
    next(foo)
    
    bar = foo.send(value)
    '''
    # _values = [value]
    _values = deque(maxlen=num_limit)
    _values.append(value)
    while True:
        received = yield sum(_values) / len(_values)
        _values.append(received)
        # if len(_values) > num_limit:
        #     _values.pop(0)
        # print(value, _values)

def rearrange(arr:list, start:int, end:int):
    '''
    Rearrange iterable with first, end element index
    '''
    if start < end:
        return arr[start:end]
    return arr[start:] + arr[:end]

def get_slots(_obj : object) -> set:
    ''' Get all slots of obj including super classes '''
    slots = set()
    for cls in _obj.__class__.__mro__:
        slots.update(getattr(cls, '__slots__', []))
    return slots

def get_random_pos(
    position: Vector,
    angle: float = 0.0,
    area: Vector = Vector(1, 1),
    area_shape: str = 'rectangle',
):
    if area_shape == 'rectangle':
        rand_x = random.random() * area.x * flip_coin(0.5, 1, -1) + position.x
        rand_y = random.random() * area.y * flip_coin(0.5, 1, -1) + position.y
    elif area_shape == 'elipse':
        u = random.random() / 4.0
        theta = math.atan(area.y/area.x * math.tan(2*math.pi*u))

        v = random.random()
        if 0.25 <= v < 0.5:
            thata =  math.pi - theta
        elif v < 0.75:
            thate = math.pi + theta
        else:
            theta = -theta
        
        max_radius = area.x * area.y / math.sqrt((area.y*math.cos(theta))**2 + (area.x*math.sin(theta))**2)
        
        random_radius = max_radius * math.sqrt(random.random())

        rand_x = random_radius * math.cos(theta)* flip_coin(0.5, 1, -1) 
        rand_y = random_radius * math.sin(theta)* flip_coin(0.5, 1, -1) 
    
    return Vector(rand_x, rand_y).rotate(angle)

def get_class_loaded(name: str):
    return getattr(sys.modules[__name__], name)

def rotate_point(point: tuple, degree: float, center: tuple = (0, 0), precision = 2) -> Vector:
    tmp_x = point[0] - center[0]
    tmp_y = point[1] - center[1]
    
    angle = math.radians(degree)
    cos_angle = math.cos(angle)
    sin_angle = math.sin(angle)
    
    # return type(point)(
    return Vector(
        round(tmp_x * cos_angle - tmp_y * sin_angle + center[0], precision),
        round(tmp_x * sin_angle + tmp_y * cos_angle + center[1], precision)
        )
    
if __name__ != "__main__":
    print("include", __name__, ":", __file__)