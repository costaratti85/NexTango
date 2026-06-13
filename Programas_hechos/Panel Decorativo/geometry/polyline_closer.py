from geometry.polyline import (
    Polyline,
    points_close,
)


EPSILON = 1e-5

LEFT = "left"
RIGHT = "right"
BOTTOM = "bottom"
TOP = "top"


class PolylineCloser:

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

    def point_side(self, p):

        x, y = p

        if abs(x - self.xmin) <= EPSILON:
            return LEFT

        if abs(x - self.xmax) <= EPSILON:
            return RIGHT

        if abs(y - self.ymin) <= EPSILON:
            return BOTTOM

        if abs(y - self.ymax) <= EPSILON:
            return TOP

        return None

    def corner_between(self, side_a, side_b):

        pair = {side_a, side_b}

        if pair == {LEFT, BOTTOM}:
            return (self.xmin, self.ymin)

        if pair == {LEFT, TOP}:
            return (self.xmin, self.ymax)

        if pair == {RIGHT, BOTTOM}:
            return (self.xmax, self.ymin)

        if pair == {RIGHT, TOP}:
            return (self.xmax, self.ymax)

        return None

    def boundary_path(self, start, end):

        side_start = self.point_side(start)
        side_end = self.point_side(end)

        if side_start is None or side_end is None:
            return [end]

        if side_start == side_end:
            return [end]

        corner = self.corner_between(
            side_start,
            side_end,
        )

        if corner is not None:

            if (
                points_close(start, corner)
                or points_close(end, corner)
            ):
                return [end]

            return [
                corner,
                end,
            ]

        return [end]

    def close_polyline(self, polyline):

        if len(polyline.points) < 2:
            return polyline

        first = polyline.points[0]
        last = polyline.points[-1]

        if points_close(first, last):
            return polyline

        closed = Polyline()

        closed.points = list(polyline.points)
        closed.segment_sources = list(
            polyline.segment_sources
        )

        closing_points = self.boundary_path(
            last,
            first,
        )

        current = last

        for point in closing_points:

            closed.add_segment(
                current[0],
                current[1],
                point[0],
                point[1],
                None,
                "closing",
            )

            current = point

        return closed

    def close_all(self, polylines):

        result = []

        for polyline in polylines:

            result.append(
                self.close_polyline(polyline)
            )

        return result