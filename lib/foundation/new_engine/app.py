from __future__ import annotations

from dataclasses import dataclass

from lib.foundation import *
from .controller import *


try:
    from config.game import *
except:
    pass

import psutil
PROCESS = psutil.Process(os.getpid())


class DebugTextLayer(dict, metaclass=SingletonType):
    '''
    use text_obj property to access text attributes
    
    bgcolor not working now
    
    '''
    def __init__(self, 
                 font_name = 'Kenney Mini Square', 
                 font_size = 10, 
                 color = (255,255,255,192),
                 bgcolor = None, 
                 topleft_position:Vector = Vector.diagonal(10) 
                 ):
        self.content = ''
        self._position = topleft_position
    
        self.font_name = font_name
        self.font_size = font_size
        self.color = color
        self.bgcolor = bgcolor
        self.text:arcade.Text = None
        self.width = CONFIG.screen_size.x
        
        self.setup()
    
    def setup(self):
        self.width = CONFIG.screen_size.x
        position = Vector(self._position.x, CONFIG.screen_size.y - self._position.y)
        # position.y = CONFIG.screen_size.y - position.y
        self.text = arcade.Text('', *position, self.color, self.font_size, 
                                font_name=self.font_name, 
                                width = self.width, 
                                anchor_y = 'top', 
                                multiline=True)
    
    def draw(self):
        text = ''
        for k, v in self.items():
            text += ' : '.join((k, str(v)))
            text += '\n'
        self.text.value = text
        self.text.draw()
    
    def _set_topleft_position(self, position:Vector):
        self._position = position
        self.setup()
    
    def _get_topleft_position(self):
        return self._position
    
    def perf_start(self, name:str = 'foo'):
        self[name] = CLOCK.perf
    
    def perf_end(self, name:str = 'foo'):
        self[name] = f'{round((CLOCK.perf - self[name]) * 1000,2)} ms'
    
    def perf_check(self, name:str = 'foo'):
        ''' kinda toggle function '''
        if name in self:
            if isinstance(self[name], float): return self.perf_end(name)
        return self.perf_start(name)
    
    def timer_start(self, name:str = 'foo'):
        self[name] = round(CLOCK.timer_start(name),2)
    
    def timer_end(self, name:str = 'foo', remain_time:float = 1.0):
        self[name] = round(CLOCK.timer_remove(name),2)
        self.remove_item(name, remain_time)
    
    def show_timer(self, name:str = 'foo'):
        if name not in CLOCK.timers: return None
        self[name] = round(CLOCK.timer_get(name),2)
    
    def remove_item(self, name:str = 'foo', delay:float = 0.0):
        def _remove(name:str):
            if name in self: self.pop(name)
        
        if not delay: _remove(name)
        else:
            CLOCK.reserve_exec(delay, self.remove_item, name, 0.0)
    
    position = property(_get_topleft_position, _set_topleft_position)
    ''' topleft position of text box '''


class Window(arcade.Window):
    
    def on_show(self):
        if GAME.gamepad: self.set_mouse_visible(False)
        GAME.debug_text['FPS'] = 0
        GAME.debug_text['MEMORY_USAGE'] = ""
        GAME.debug_text['UPTIME'] = ""
        
    def on_update(self, delta_time: float):
        
        GAME.delta_time = delta_time
        
        scheduler_count = pyglet_clock._schedule_interval_items.__len__()
        
        CLOCK.fps_current = 1 / delta_time
        GAME.debug_text['FPS'] = CLOCK.fps_average
        GAME.debug_text['MEMORY_USAGE'] = str(round(PROCESS.memory_info()[0]/(1024*1024),2))+" MB"
        GAME.debug_text['UPTIME'] = CLOCK.uptime
        GAME.debug_text['SCHEDULER'] = scheduler_count
        
    def on_draw(self):
        
        GAME.debug_text.draw()
    
    def on_resize(self, width: float, height: float):
        ### broken now. maybe arcade bug
        super().on_resize(width, height)
        resizing = Vector(width, height)
        tmp_scale = width / 1024
        print(self._ctx.projection_2d)
        GAME.set_screen()


class View(arcade.View):
    
    def __init__(self, window: Window = None):
        super().__init__(window)
        self.fade_out = 0.0
        self.fade_in = 0.0
        self.fade_alpha = 1

    def setup(self):
        pass
        
    def draw_tint(self, alpha = 0.0, color = (0, 0, 0)):
        arcade.draw_rectangle_filled(self.window.width / 2, self.window.height / 2,
                                     self.window.width, self.window.height,
                                     (*color, alpha * 255))
    
    def draw_contents(self):
        pass
    
    def on_draw(self):
        self.clear()
        self.draw_contents()
        if self.fade_in > 0 or self.fade_out > 0:
            # self.fade_alpha = finterp_to(self.fade_alpha, )
            self.draw_tint()
    
    def go_next(self, next_screen:arcade.View):
        if self.fade_out:
            pass
        
    def go_after_fade_out(self, next_screen:arcade.View):
        pass
    
    def on_update(self, delta_time: float):
        GAME.delta_time = delta_time


@dataclass
class Client(metaclass = SingletonType):
    ''' I/O for game
    
    - 디스플레이 정보
        - 렌더링 배율
    - 현재 뷰포트 중앙의 절대 좌표
    - 이동 조작, 카메라 조작
    - 게임패드 입력 raw
    - 마우스 입력 raw
        - 뷰포트 내 상대좌표
        - 월드상의 절대 좌표
    
    (나중에 Window 클래스에 통합시켜버릴 수도 있음)
    '''
    
    delta_time:float = 0.0
    physics_engine:PhysicsEngine = None
    window:Window = None
    
    abs_screen_center:Vector = Vector()
    render_scale:float = 1.0
    screen_shortside = None
    screen_longside = None

    debug_text:DebugTextLayer = None
    viewport:Camera = None
    _player_controller:PawnController = None
    local_players = []
    
    gamepads : list[pyglet.input.Joystick] = None
    keyboard : pyglet.window.key.KeyStateHandler = None            ### for later implementation
    mouse : pyglet.window.mouse.MouseStateHandler = None     ### for later implementation
    
    mouse_screen_position:Vector = Vector()
    gamepad:arcade.joysticks.Joystick = None
    input_move:Vector = Vector()
    
    key = arcade.key
    key_inputs = []
    
    last_abs_pos_mouse_lb_pressed:Vector = vectors.zero
    last_abs_pos_mouse_lb_released:Vector = vectors.zero
    last_mouse_lb_hold_time = 0.0
    
    walk_key_engaged = False
    
    ai_controllers = []
    
    controllers = []
    
    def __init__(
        self,
        max_local_players : int = 1,
        ) -> None:
        super().__init__()
        self.max_local_players = max_local_players
        self.local_players:list[PawnController] = []
        self.gamepads = self.get_gamepads()
        self.gamepad = self.get_gamepads(0)
        self.physics_engine = PhysicsEngine()
    
    def add_player(self, player_controller : PawnController):
        
        if len(self.local_players) >= self.max_local_players:
            return self.show_alert('Local player max error')
        
        self.local_players.append(player_controller)
        idx = self.local_players.index(player_controller)
        player_controller.local_player_id = idx
        
        self.window.push_handlers(player_controller)
        
        if self.gamepads:       ### need to revise logic for kb + gamepad pair.
            if len(self.local_players) >= len(self.gamepads):
                return self.show_alert('No more gamepads')
            self.gamepads[idx].push_handlers(player_controller)

    def remove_player(self, player_controller : PawnController):
        
        idx = player_controller.local_player_id
        self.local_players.remove(player_controller)
        self.gamepads[idx].remove_handlers(player_controller)
        self.window.remove_handlers(player_controller)
        
    def show_alert(self, message : str = 'ALERT'):
        #TODO
        ''' will be implemented later '''
        print(message)
    
    def _get_player_controller(self):
        return self.local_players[0]
    
    # def _set_player_controller(self, player_controller : PawnController):
    #     self._player_controller = player_controller
    #     if self.gamepad:
    #         self.gamepad.push_handlers(self._player_controller)
    #     self.window.push_handlers(self._player_controller)
        
    player_controller = property(_get_player_controller)
    
    def get_gamepads(self, id : int = None):
        if not self.gamepads:
            gamepads : list[pyglet.input.Joystick] = pyglet.input.get_joysticks()
            if not gamepads:
                return None
            for i, gamepad in enumerate(gamepads):
                gamepad.open()
                # gamepad.push_handlers(self)
                print(f'Gamepad[{i}] attached')
            # self.gamepads = gamepads
            return gamepads
        if id is None:
            return self.gamepads
        return self.gamepads[id]
        
    def set_window(
        self,
        size: Vector = CONFIG.screen_size,
        title: Optional[str] = 'mash arcade framework',
        fullscreen: bool = False,
        resizable: bool = False,
        update_rate: Optional[float] = 1 / 60,
        antialiasing: bool = True, 
        gl_version: Tuple[int, int] = (3, 3), 
        screen: pyglet.canvas.Screen = None,
        style: Optional[str] = pyglet.window.Window.WINDOW_STYLE_DEFAULT,
        visible: bool = True,
        vsync: bool = False,
        gc_mode: str = "context_gc",
        center_window: bool = False,
        samples: int = 4,
        enable_polling: bool = False,
        ):
        
        self.window = Window(
            *size, 
            title = title,
            fullscreen = fullscreen,
            resizable = resizable,
            update_rate = update_rate,
            antialiasing = antialiasing,
            gl_version = gl_version,
            screen = screen,
            style = style,
            visible = visible,
            vsync = vsync,
            gc_mode = gc_mode,
            center_window = center_window,
            samples = samples,
            enable_polling = enable_polling,
            )
        
        self.set_screen()
        self.window.push_handlers(self)
    
    def set_screen(self):
        ''' should be called after resizing, fullscreen, etc. '''
        size = self.window.get_size()
        self.screen_shortside = min(*size)
        self.screen_longside = max(*size)
        CONFIG.screen_size = Vector(size)
        self.render_scale = self.window.get_framebuffer_size()[0] / size[0]  
        self.debug_text = DebugTextLayer()
          
    def set_scene(self, view_class:View, *args, **kwargs):
        scene = view_class(*args, **kwargs)
        scene.setup()
        self.window.show_view(scene)
    
    def run(self):
        arcade.run()
    
    def on_key_press(self, key:int, modifiers:int):
        print(f'on key press from CLIENT {key, modifiers}')
        self.key_inputs.append(key)
        if key == keys.GRAVE and not modifiers: 
            CONFIG.debug_f_keys[0] = not CONFIG.debug_f_keys[0]
        for i in range(13):
            if key == keys.__dict__[f'F{i+1}'] and not modifiers: 
                CONFIG.debug_f_keys[i+1] = not CONFIG.debug_f_keys[i+1]
    
    def on_key_release(self, key:int, modifiers:int):
        self.key_inputs.remove(key)
        if key == arcade.key.ESCAPE: arcade.exit()  ### for convenience

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int):
        self.mouse_screen_position = Vector(x, y)

    def on_mouse_drag(self, x: int, y: int, dx: int, dy: int, buttons: int, modifiers: int):
        pass
    
    def on_mouse_scroll(self, x: int, y: int, scroll_x: int, scroll_y: int):
        pass
    
    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        print('mouse press from window')
        if button == arcade.MOUSE_BUTTON_LEFT:
            GAME.last_abs_pos_mouse_lb_pressed = GAME.abs_cursor_position
        # if GAME.player_controller: 
            # GAME.player_controller.on_mouse_press(x=x, y=y, button=button, modifiers=modifiers)
    
    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int):
        if button == arcade.MOUSE_BUTTON_LEFT:
            GAME.last_abs_pos_mouse_lb_released = GAME.abs_cursor_position
        # if GAME.player_controller: 
            # GAME.player_controller.on_mouse_release(x=x, y=y, button=button, modifiers=modifiers)

    
    @property
    def lstick(self) -> Vector:
        ''' returns raw info of left stick (-1, -1) ~ (1, 1) '''
        if not self.gamepad: return None
        x = map_range_abs(self.gamepad.x, CONFIG.gamepad_deadzone_lstick, 1, 0, 1, True)
        y = map_range_abs(self.gamepad.y, CONFIG.gamepad_deadzone_lstick, 1, 0, 1, True) * -1
        return Vector(x, y)
    
    @property
    def rstick(self) -> Vector:
        ''' returns raw info of left stick (-1, -1) ~ (1, 1) '''
        if not self.gamepad: return None
        x = map_range_abs(self.gamepad.rx, CONFIG.gamepad_deadzone_rstick, 1, 0, 1, True)
        y = map_range_abs(self.gamepad.ry, CONFIG.gamepad_deadzone_rstick, 1, 0, 1, True) * -1
        return Vector(x, y)
    
    def _get_move_input(self):
        if self.gamepad:
            return self.lstick
        else:
            return self.input_move.clamp_length(1) * (0.5 if self.walk_key_engaged else 1)

    move_input:Vector = property(_get_move_input)
    ''' returns movement direction vector (-1, -1) ~ (1, 1) '''
    
    def _get_target_point(self):
        if self.gamepad:
            if self.rstick.length > 0.5:
                return (self.rstick.unit * CONFIG.screen_size.y / 2 + self.abs_screen_center) * self.render_scale
        else:
            return self.abs_cursor_position
    
    target_point:Vector = property(_get_target_point)
    ''' returns relative target point '''
    
    def _get_cursor_position(self) -> Vector:
        # if not self.mouse_input: return Vector()
        return self.mouse_screen_position * self.render_scale
    
    cursor_position:Vector = property(_get_cursor_position)
    ''' returns relative mouse cursor point '''
    
    def _get_abs_cursor_position(self) -> Vector:
        return self.mouse_screen_position + self.abs_screen_center - CONFIG.screen_size / 2
        # return self.mouse_input + self.window.current_camera.position
    
    abs_cursor_position:Vector = property(_get_abs_cursor_position)
    ''' get absolute position in world, pointed by mouse cursor '''


if __name__ != "__main__":
    print("include", __name__, ":", __file__)
    GAME = Client()
    print('GAME initialized')
