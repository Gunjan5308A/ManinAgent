from manim import *

class LessonScene(Scene):
    def construct(self):
        # Number line
        nl = NumberLine(x_range=[-4, 4, 1], length=8, include_numbers=True)
        self.play(Create(nl))

        # Dot sliding along the line
        dot = Dot(nl.n2p(0), color=YELLOW)
        self.play(FadeIn(dot))
        self.play(dot.animate.move_to(nl.n2p(3)), run_time=2)

        # Labels and equations
        eq = MathTex("x = 3").to_edge(UP)
        self.play(Write(eq))
        self.wait(1)

        # Bar chart style: stacked rectangles
        bars = VGroup(*[
            Rectangle(width=0.6, height=v, fill_opacity=0.8, fill_color=color, stroke_width=0)
            .move_to([i * 0.9 - 1.8, v / 2 - 1, 0])
            for i, (v, color) in enumerate([(1, RED), (2, GREEN), (1.5, BLUE), (0.8, ORANGE)])
        ])
        self.play(Create(bars))
        self.wait(2)
