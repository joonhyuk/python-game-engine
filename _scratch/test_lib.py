import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from lib.foundation import *
from config import *

a = Environment()

print(get_curve_value(3.5, {1:2, 2:4, 3:4, 4:2}, map_range_easeinout))