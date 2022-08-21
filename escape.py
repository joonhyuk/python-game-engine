from lib.escape import *
from config import *

VERSION = Version()


def main():
    CLOCK.use_engine_tick = True
    app = Window(*CONFIG.screen_size, PROJECT_NAME + ' ' + str(VERSION.full))
    title = TitleScreen()
    
    app.show_view(title)
    app.run()


if __name__ == '__main__':
    main()