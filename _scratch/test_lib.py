from __future__ import annotations

import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


from lib.foundation import *
from config import *

class Foo:
    
    def __init__(self) -> None:
        self.sprite = SpriteCircle()
    
    position = PropertyFrom('sprite')

f = Foo()