from lib.escape import *
from config import *

VERSION = Version()


def main():
    CLOCK.use_engine_tick = True
    # app = Client(*CONFIG.screen_size, PROJECT_NAME + ' ' + str(VERSION.full))
    
    GAME.set_window(title = 'ESCAPE GAME DEV')
    GAME.set_scene(TitleScreen)
    GAME.run()

if __name__ == '__main__':
    main()