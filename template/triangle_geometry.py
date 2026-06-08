from manim import *

class LessonScene(Scene):
    def construct(self):
        # Right triangle using plain list vertices (not np.array in list)
        tri = Polygon([0,0,0], [3,0,0], [0,2,0], color=BLUE, fill_opacity=0.3)
        label_a = MathTex("a").next_to(tri, DOWN)
        label_b = MathTex("b").next_to(tri, LEFT)
        label_c = MathTex("c").move_to([1.8, 1.2, 0])

        self.play(Create(tri))
        self.play(Write(label_a), Write(label_b), Write(label_c))

        formula = MathTex("a^2 + b^2 = c^2").to_edge(UP)
        self.play(Write(formula))
        self.wait(2)
