from __future__ import annotations

from lib.foundation.base import *

from .object import *


class MovementHandler(Handler):
    
    def __init__(
        self,
        body : Body) -> None:
        
        super().__init__()
        self.body = body