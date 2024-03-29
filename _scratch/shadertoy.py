import arcade
from arcade.experimental import Shadertoy


class MyGame(arcade.Window):

    def __init__(self):
        # Call the parent constructor
        super().__init__(width=1280, height=720, title="Shader Demo", resizable=True)

        # Keep track of total run-time
        self.time = 0.0

        # File name of GLSL code
        # file_name = "fractal_pyramid.glsl"
        # file_name = "cyber_fuji_2020.glsl"
        # file_name = "_scratch/shadertest_flame.glsl"
        file_name = "_scratch/shaders/2dshadow.glsl"
        # file_name = "flame.glsl"
        # file_name = "star_nest.glsl"

        # Create a shader from it
        self.shadertoy = Shadertoy(size=self.get_size(),
                                   main_source=open(file_name).read())

    def on_draw(self):
        self.clear()
        mouse_pos = self.mouse["x"], self.mouse["y"]
        self.shadertoy.render(time=self.time, mouse_position=mouse_pos)

    def on_update(self, dt):
        # Keep track of elapsed time
        self.time += dt


if __name__ == "__main__":
    MyGame()
    arcade.run()