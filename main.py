# from lib.foundation.engine import SoundBank
from config import *
from lib.foundation import *

from lib.PythonByte.main import *

# SB = SoundBank(RESOURCE_PATH + 'sfx/')
# game = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
game = GameManager()
game.setup()
arcade.run()