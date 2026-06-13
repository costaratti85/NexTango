from geometry.bbox import BoundingBox


class LineSegment:

    def __init__(self, x1, y1, x2, y2):

        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2

    def start_point(self):
        return (self.x1, self.y1)

    def end_point(self):
        return (self.x2, self.y2)

    def reversed(self):
        return LineSegment(
            self.x2,
            self.y2,
            self.x1,
            self.y1,
        )

    def bbox(self):

        return BoundingBox(
            min(self.x1, self.x2),
            min(self.y1, self.y2),
            max(self.x1, self.x2),
            max(self.y1, self.y2),
        )

    def translated(self, dx, dy):

        return LineSegment(
            self.x1 + dx,
            self.y1 + dy,
            self.x2 + dx,
            self.y2 + dy,
        )

    def export_dxf(self, msp):

        msp.add_line(
            (self.x1, self.y1),
            (self.x2, self.y2),
        )