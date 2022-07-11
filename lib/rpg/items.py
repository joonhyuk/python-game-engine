from lib.foundation import *

class Item(MObject):
    def __init__(self, name = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.clsid = None