from config.engine import *
from lib.foundation.base import *
from lib.foundation.engine import *

class World:
    ''' could be a singleton class '''
    def __init__(self) -> None:
        
        self.level:arcade.TileMap = None
        self.physics:arcade.PhysicsEngineSimple = None
        self.static_layers:list[ObjectLayer] = []
    
    def load_tiled_level(self, filepath:str) -> arcade.TileMap:
        
        self.level = arcade.load_tilemap(get_path(filepath))
        self.physics = arcade.PhysicsEngineSimple()
        # self.physics.player_sprite
        # self.level.object_lists
        # self.level.properties

    def setup(self):
        
        if not self.level: return False

if __name__ != "__main__":
    print("include", __name__, ":", __file__)
