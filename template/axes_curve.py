from manim import *

class LessonScene(Scene):
    def construct(self):
        # Axes
        ax = Axes(x_range=[-3, 3, 1], y_range=[-2, 6, 1], axis_config={"include_numbers": True})
        self.play(Create(ax))

        # Plot a curve
        curve = ax.plot(lambda x: x**2, color=YELLOW)
        label = ax.get_graph_label(curve, label="x^2")
        self.play(Create(curve), Write(label))

        # Area under curve
        area = ax.get_area(curve, x_range=[0, 2], color=BLUE, opacity=0.3)
        self.play(FadeIn(area))
        self.wait(2)

        # Show a tangent line at x=1
        dot = Dot(ax.c2p(1, 1), color=RED)
        tangent = ax.plot(lambda x: 2*x - 1, x_range=[0, 2], color=RED)
        self.play(FadeIn(dot), Create(tangent))
        self.wait(2)
