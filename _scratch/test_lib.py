import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from lib.foundation import *
from config import *

class fooo:
    
    def __init__(self, ll:list) -> None:
        ll.append(self)
    
    def __del__(self):
        print('I\'m dying~')
    
    @classmethod
    def init(cls, ll:list):
        cls(ll)

fl = []
print('start')
fooo.init(fl)
# del(f)
print('added')
fl.pop(0)
print('popped')
