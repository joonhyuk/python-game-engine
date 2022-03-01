"""
base feature codes
joonhyuk@me.com
"""
import sys, json
from enum import Enum
from typing import Iterable
from lib.foundation.vector import Vector
# from lib.foundation.clock import *

class EnumVector(Vector, Enum):
    __class__ = Vector
    
    def __repr__(self) -> Vector:
        return self.value

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

def clamp(value, in_min, in_max):
    return min(in_max, max(in_min, value))

def map_range(value, in_min, in_max, out_min, out_max, clamped = False):
    if clamped: value = clamp(value, in_min, in_max)
    return ((value - in_min) / (in_max - in_min)) * (out_max - out_min) + out_min

def load_json(filepath:str) -> dict:
    with open(get_path(filepath), 'r') as json_file:
        return json.load(json_file)

def save_json(filepath:str, json_data) -> None:
    with open(get_path(filepath), 'w') as json_file:
        json.dump(json_data, json_file, indent = 4)

if __name__ != "__main__":
    print("include", __name__, ":", __file__)