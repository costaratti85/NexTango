import math

from geometry.bbox import BoundingBox


class ArcSegment:

    def __init__(
        self,
        cx,
        cy,
        radius,
        start_angle,
        end_angle,
    ):

        self.cx = cx
        self.cy = cy
        self.radius = radius
        self.start_angle = start_angle
        self.end_angle = end_angle

    def start_point(self):

        a = math.radians(self.start_angle)

        return (
            self.cx + math.cos(a) * self.radius,
            self.cy + math.sin(a) * self.radius,
        )

    def end_point(self):

        a = math.radians(self.end_angle)

        return (
            self.cx + math.cos(a) * self.radius,
            self.cy + math.sin(a) * self.radius,
        )

    def reversed(self):

        return ArcSegment(
            self.cx,
            self.cy,
            self.radius,
            self.end_angle,
            self.start_angle,
        )

    def bbox(self):

        return BoundingBox(
            self.cx - self.radius,
            self.cy - self.radius,
            self.cx + self.radius,
            self.cy + self.radius,
        )

    def translated(self, dx, dy):

        return ArcSegment(
            self.cx + dx,
            self.cy + dy,
            self.radius,
            self.start_angle,
            self.end_angle,
        )

    def export_dxf(self, msp):

        if abs(self.end_angle - self.start_angle) >= 360:

            msp.add_circle(
                (self.cx, self.cy),
                self.radius,
            )

        else:

            msp.add_arc(
                (self.cx, self.cy),
                self.radius,
                self.start_angle,
                self.end_angle,
            )