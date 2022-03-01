"""
Clock class for any purpose
by joonhyuk@me.com

maybe it's reinventing the wheel, the goal was reducing dependance on pygame
"""

class Clock:
    """SUPER PRECISE timer"""
    import time as pytime
    get_time = pytime.time
    get_perf = pytime.perf_counter
    
    def __init__(self, fps = 60) -> None:
        self.start_time = self.prev_time = Clock.get_time()
        # self.prev_time = self.start_time - 1 / 60 # force delay for start
        """previous frame start time"""
        self.cur_time = 0.0
        """time of 'previous' frame'"""
        self.delta_time = 0.0
        """actual frame time(sec) of current frame"""
        self.eof_time = self.start_time
        """actual end of frame time(sec) (after waiting)"""
        self.fps_limit = fps
        """initial fps limit"""
        self.fps_current = 0.0
        
        self.timerdic:dict[str, list[bool,float,float]] = {}
        """{id:[pause, start time, paused time]}"""
        self.timer_game_paused_list:list = []
        self.timer_game_ispaused:bool = False
        self.magic_num = 0.5
        self.raw_time = self.cur_time - self.eof_time
        
        # self.pgclock = pygame.time.Clock()
    def tick(self, fps_limit:float = None, magic_num = 1):    # replacement for pygame.Clock.tick
        """refresh frame and wait for actual framerate\n
        should be called once a loop"""
        if fps_limit != None : self.fps_limit = fps_limit
        frame_sec = 1 / self.fps_limit
        est_eof_time = self.eof_time + frame_sec
        """prev end of frame time plus frame delay(1/60)"""
        self.cur_time = self.__class__.get_time()
        self.raw_time = self.cur_time - self.eof_time
        self.delta_time = self.cur_time - self.prev_time
        self.prev_time = self.cur_time
        
        self.fps_current = 1 / self.delta_time
        """actual framerate of this frame"""
        if fps_limit and fps_limit < 0:
            """for debug"""
            self.eof_time = self.cur_time
            return False
        
        """hyper precise but super high cost"""
        # est_eof_time = self.eof_time + frame_sec
        # while self.eof_time < est_eof_time:
        #     # time.sleep(0.001)
        #     self.eof_time = self.__class__.get_time()
            
        """low cost but less precise. almost same with pygame clock"""
        # wait_time = frame_sec - self.raw_time
        # if wait_time > 0 : time.sleep(wait_time * self.magic_num)
        # # magic_num : 0.9 for 60f, 0.922 for 45f, 0.945 for 30f, 0.9735 for 15f, 0.98 for 10f
        # self.eof_time = MTime.get_time()
        # # self.eof_time = self.cur_time + wait_time
        # # print(eof_time - self.eof_time)
        
        """hybrid method"""
        wait_time = frame_sec - self.raw_time
        self.eof_time = self.sleep(wait_time * self.magic_num, est_eof_time)        
        
    def sleep(self, sleep_time = 0.0, wake_time = 0.0, precision = 0.0):
        if sleep_time > 0 : self.__class__.pytime.sleep(sleep_time)
        cur_time = self.__class__.get_time()
        while cur_time < wake_time:
            if precision : self.__class__.pytime.sleep(precision)
            cur_time = self.__class__.get_time()
        return cur_time

    def __repr__(self):
        """need to refine to use each timer class instance"""
        return self.timerdic
    
    def get_fps(self) -> float:
        
        return self.fps_current
    
    def timer_get(self, name:str):
        if name not in self.timerdic:
            self.timer_start(name)
            
        if self.timerdic[name][0]:
            """while pause"""
            return self.timerdic[name][2] - self.timerdic[name][1]
        else:
            return self.get_perf() - self.timerdic[name][1]
    
    def timer_start(self, id:str, pause:bool = None):
        cur_time = self.get_perf()
        
        if id not in self.timerdic:
            if pause is None: pause = False
            self.timerdic[id] = [pause, cur_time, cur_time]
            return 0
        
        return self.timer_get(id)
    
    def timer_pause(self, id:str, switch:bool = None):
        if id not in self.timerdic:
            return self.timer_start(id, pause = switch)
        
        cur_time = self.get_perf()
        prev_pause = self.timerdic[id][0]
        if switch is None: switch = not prev_pause
        if switch ^ prev_pause:
            self.timerdic[id][0] = switch
            if switch:
                self.timerdic[id][2] = cur_time
            else:
                self.timerdic[id][1] = self.timerdic[id][1] - self.timerdic[id][2] + cur_time
        return self.timer_get(id)
    
    def timer_reset(self, id:str, restart = True):
        # if self.timer_remove(name):
        #     self.timer_start(name, not restart)
        self.timer_remove(id)
        return self.timer_start(id, not restart)
        
    def timer_remove(self, id:str):
        if id not in self.timerdic:
            # OPT.print_raw('timer['+name+'] not exists')
            return False
        del self.timerdic[id]
        return True
    
    def timer_pause_all(self, switch:bool = None):
        if switch is None: switch = not self.timer_game_ispaused
        if switch == self.timer_game_ispaused: return False
        if switch:
            self.timer_game_paused_list = []
            for id, timer in self.timerdic.items():
                if not timer[0]:
                    """not paused timers"""
                    self.timer_game_paused_list.append(id)
                    self.timer_pause(id, True)
        else:
            if self.timer_game_paused_list:
                for paused_id in self.timer_game_paused_list:
                    self.timer_pause(paused_id, False)
                self.timer_game_paused_list = []
        self.timer_game_ispaused = switch

    @property
    def process_time_ms(self) -> int:
        return round(self.raw_time * 1000)
    
    @property
    def actual_time_elapsed(self) -> float:
        """return elapsed time(sec) after this instance made"""
        return self.__class__.get_time() - self.game_start_time

if __name__ != "__main__":
    CLOCK = Clock()
    print("include", __name__, ":", __file__)
