from geometry.line_segment import (
    LineSegment,
)


INSIDE = 0

LEFT = 1
RIGHT = 2
BOTTOM = 4
TOP = 8


class RectClipper:

    def __init__(
        self,
        xmin,
        ymin,
        xmax,
        ymax,
    ):

        self.xmin = xmin
        self.ymin = ymin

        self.xmax = xmax
        self.ymax = ymax

    def compute_code(self, x, y):

        code = INSIDE

        if x < self.xmin:
            code |= LEFT

        elif x > self.xmax:
            code |= RIGHT

        if y < self.ymin:
            code |= BOTTOM

        elif y > self.ymax:
            code |= TOP

        return code

    def clip_segment(self, segment):

        x1 = segment.x1
        y1 = segment.y1

        x2 = segment.x2
        y2 = segment.y2

        code1 = self.compute_code(
            x1,
            y1,
        )

        code2 = self.compute_code(
            x2,
            y2,
        )

        while True:

            #
            # totalmente adentro
            #

            if (
                code1 == 0 and
                code2 == 0
            ):

                return LineSegment(
                    x1,
                    y1,
                    x2,
                    y2,
                )

            #
            # totalmente afuera
            #

            if code1 & code2:

                return None

            #
            # elegir punto exterior
            #

            if code1 != 0:
                code_out = code1
            else:
                code_out = code2

            #
            # intersecciones
            #

            if code_out & TOP:

                x = x1 + (
                    (x2 - x1)
                    * (
                        self.ymax - y1
                    )
                    / (y2 - y1)
                )

                y = self.ymax

            elif code_out & BOTTOM:

                x = x1 + (
                    (x2 - x1)
                    * (
                        self.ymin - y1
                    )
                    / (y2 - y1)
                )

                y = self.ymin

            elif code_out & RIGHT:

                y = y1 + (
                    (y2 - y1)
                    * (
                        self.xmax - x1
                    )
                    / (x2 - x1)
                )

                x = self.xmax

            elif code_out & LEFT:

                y = y1 + (
                    (y2 - y1)
                    * (
                        self.xmin - x1
                    )
                    / (x2 - x1)
                )

                x = self.xmin

            #
            # reemplazar punto
            #

            if code_out == code1:

                x1 = x
                y1 = y

                code1 = self.compute_code(
                    x1,
                    y1,
                )

            else:

                x2 = x
                y2 = y

                code2 = self.compute_code(
                    x2,
                    y2,
                )