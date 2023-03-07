from lib.ddd import *
from lib.ddd.view import TitleScreen

class TestTitle(TitleScreen):
    
    def start_game(self):
        GAME.set_scene(DDDTest)


class VesselBody(DynamicBody):
    
    def setup(self, **kwargs) -> None:
        
        return super().setup(**kwargs)
    

class UnderwaterMovement(PhysicsMovement):
    '''
    배수량, 밸러스트 배분, 추력 및 추진 위치
    부력 등의 특징을 이동 컴포넌트가 가진다? 바디가 가져야 할 것 같음.
    이동 컴포넌트는 힘 주고 이동시 방향타 적용하는 것.
    밸러스트는 피치와 롤을 잡아서 평형을 유지하는 것이 주 목적이고 상승 하강시 피치를 조절하는 것은 방향타 날개가 주 역할을 한다.
    
    '''


class Submarine(Character):
    
    def __init__(self, body: DynamicBody, hp: float = 100, **kwargs) -> None:
        super().__init__(body, hp, **kwargs)
        self.camera: CameraHandler = None
        
    
    def setup(self, **kwargs) -> None:
        self.camera = CameraHandler(body = self.body)


class DDDTest(View):
    
    def setup(self):
        arcade.set_background_color(colors.OCEAN_BOAT_BLUE)
        
        self.space = PhysicsSpace()
        self.player_layer = ObjectLayer(self.space)
        self.debris_layer = ObjectLayer(self.space)
        
        self.player = DynamicObject(
            DynamicBody(
                SpriteCircle(32)
            )
        )
        
        self.camera = self.player.camera
        

    
    
        
def main():
    CLOCK.use_engine_tick = True
    
    GAME.set_window((1280, 720))
    GAME.set_scene(TestTitle)
    GAME.run()

if __name__ == '__main__':
    main()
