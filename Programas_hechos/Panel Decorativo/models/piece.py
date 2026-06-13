class Piece:

    def __init__(self, name=""):
        self.name = name
        self.polylines = []

    def add_polyline(self, polyline):
        self.polylines.append(polyline)

    def bbox(self):

        if not self.polylines:
            return None

        first = self.polylines[0].bbox()

        min_x = first.min_x
        min_y = first.min_y
        max_x = first.max_x
        max_y = first.max_y

        for pl in self.polylines[1:]:

            b = pl.bbox()

            min_x = min(min_x, b.min_x)
            min_y = min(min_y, b.min_y)
            max_x = max(max_x, b.max_x)
            max_y = max(max_y, b.max_y)

        from geometry.bbox import BoundingBox

        return BoundingBox(min_x, min_y, max_x, max_y)