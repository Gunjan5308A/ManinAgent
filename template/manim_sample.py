

from manim import *

class SquareToCircle(Scene):
    def construct(self):
        # Create a circle and a square
        circle = Circle()
        square = Square()
        
        # Style them
        circle.set_fill(PINK, opacity=0.5)
        
        # Play the animations
        self.play(Create(square))
        self.play(Transform(square, circle))
        self.play(FadeOut(square))
