"""
Clock class for any purpose
by joonhyuk@me.com

maybe it's reinventing the wheel, the goal was reducing dependance on any frameworks
"""
import threading

from lib.foundation.base import avg_generator

class Clock:
    """SUPER PRECISE timer"""
    import time as pytime
    get_time = pytime.time
    get_perf = pytime.perf_counter
    
    def __init__(self, fps = 60, use_engine_tick = False) -> None:
        self.use_engine_tick = use_engine_tick
        '''switch for sleep in tick'''
        self.start_time = self.prev_time = self.__class__.get_time()
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
        
        self._fps_avg = avg_generator(0.0)
        next(self._fps_avg)
        
        self.timers:dict[str, list[bool,float,float]] = {}
        """{id:[pause, start time, paused time]}"""
        self.timer_game_paused_list:list = []
        self.timer_game_ispaused:bool = False
        self.magic_num = 0.5
        self.raw_time = self.cur_time - self.eof_time
        
        # self.pgclock = pygame.time.Clock()
        print('CLOCK initialized')
        
    def tick(self, fps_limit:float = None, magic_num = 1):    # replacement for pygame.Clock.tick
        """refresh frame and wait for actual framerate\n
        should be called once a loop"""
        if fps_limit != None : self.fps_limit = fps_limit
        frame_sec = 1 / self.fps_limit
        est_eof_time = self.eof_time + frame_sec
        """prev end of frame time plus frame delay(1/60)"""
        self.cur_time = self.__class__.get_time()
        self.raw_time = self.cur_time - self.eof_time
        self.delta_time = self.cur_time - self.prev_time or 0.016
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
        if not self.use_engine_tick: self.eof_time = self.sleep(wait_time * self.magic_num, est_eof_time)        
        
    def sleep(self, sleep_time = 0.0, wake_time = 0.0, precision = 0.0):
        if sleep_time > 0 : self.__class__.pytime.sleep(sleep_time)
        cur_time = self.__class__.get_time()
        while cur_time < wake_time:
            if precision : self.__class__.pytime.sleep(precision)
            cur_time = self.__class__.get_time()
        return cur_time

    def __repr__(self):
        """need to refine to use each timer class instance"""
        return self.timers
    
    def get_fps(self) -> float:
        
        return self.fps_current
    
    def timer_get(self, name:str) -> float:
        if name not in self.timers:
            self.timer_start(name)
            return 0.0
            
        if self.timers[name][0]:
            """while pause"""
            return self.timers[name][2] - self.timers[name][1]
        else:
            return self.get_perf() - self.timers[name][1]
    
    def timer_start(self, id:str, pause:bool = None):
        cur_time = self.get_perf()
        
        if id not in self.timers:
            if pause is None: pause = False
            self.timers[id] = [pause, cur_time, cur_time]
            return 0
        
        return self.timer_get(id)
    
    def timer_pause(self, id:str, switch:bool = None):
        if id not in self.timers:
            return self.timer_start(id, pause = switch)
        
        cur_time = self.get_perf()
        prev_pause = self.timers[id][0]
        if switch is None: switch = not prev_pause
        if switch ^ prev_pause:
            self.timers[id][0] = switch
            if switch:
                self.timers[id][2] = cur_time
            else:
                self.timers[id][1] = self.timers[id][1] - self.timers[id][2] + cur_time
        return self.timer_get(id)
    
    def timer_reset(self, id:str, restart = True):
        timer_value = self.timer_remove(id)
        self.timer_start(id, not restart)
        return timer_value
        
    def timer_remove(self, id:str) -> float:
        if id not in self.timers:
            return 0.0
        timer_value = self.timer_get(id)
        del self.timers[id]
        return timer_value
    
    def timer_pause_all(self, switch:bool = None):
        if switch is None: switch = not self.timer_game_ispaused
        if switch == self.timer_game_ispaused: return False
        if switch:
            self.timer_game_paused_list = []
            for id, timer in self.timers.items():
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
    
    def reserve_exec(self, interval:float, function, *args, **kwargs):
        ''' function reference not deleted after timer ends. so do not use it for destruction '''
        for tt in threading.enumerate():
            if isinstance(tt, threading.Timer):
                if all((tt.function == function, tt.args == args, tt.kwargs == kwargs)):
                    tt.cancel()
        if interval <= 0: return function(*args, **kwargs)
        # print('thread active count ',threading.active_count())
        return threading.Timer(interval, function, args, kwargs).start()
    
    def reserve_cancel(self, function = None):
        thread_list = threading.enumerate()
        for tt in thread_list:
            if isinstance(tt, threading.Timer):
                if function:
                    if tt.function == function: tt.cancel()
                else: tt.cancel()
    
    @property
    def fps_average(self):
        return round(self._fps_avg.send(self.fps_current), 2)
    
    @property
    def process_time_ms(self) -> int:
        return round(self.raw_time * 1000)
    
    @property
    def actual_time_elapsed(self) -> float:
        """return elapsed time(sec) after this instance made"""
        return self.__class__.get_time() - self.start_time

    @property
    def perf(self) -> float:
        return self.get_perf()
    
if __name__ != "__main__":
    print("include", __name__, ":", __file__)
    CLOCK = Clock()
