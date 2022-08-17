import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from lib.foundation import *
from config import *

print(collision.projectile in collision.test)