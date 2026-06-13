from geometry.line_segment import LineSegment
from geometry.bbox import BoundingBox


EPSILON = 1e-6


def points_close(a, b):

    return (
        abs(a[0] - b[0]) <= EPSILON
        and
        abs(a[1] - b[1]) <= EPSILON
    )


class Polyline:

    def __init__(self):

        self.points = []
        self.segment_sources = []

    def add_point(self, x, y, source=None, source_type="unknown"):

        self.points.append((x, y))

    def add_existing_point(self, point):

        if hasattr(point, "x"):
            self.points.append((point.x, point.y))
        else:
            self.points.append(point)

    def add_segment(
        self,
        x1,
        y1,
        x2,
        y2,
        source=None,
        source_type="unknown",
    ):

        start = (x1, y1)
        end = (x2, y2)

        if not self.points:
            self.points.append(start)

        else:
            last = self.points[-1]

            if not points_close(last, start):
                self.points.append(start)

        self.points.append(end)

        self.segment_sources.append(
            {
                "source": source,
                "source_type": source_type,
            }
        )

    def segments(self):

        result = []

        for i in range(len(self.points) - 1):

            x1, y1 = self.points[i]
            x2, y2 = self.points[i + 1]

            segment = LineSegment(
                x1,
                y1,
                x2,
                y2,
            )

            if i < len(self.segment_sources):

                meta = self.segment_sources[i]

                segment.source = meta.get("source")
                segment.source_type = meta.get(
                    "source_type",
                    "unknown",
                )

            else:

                segment.source = None
                segment.source_type = "unknown"

            result.append(segment)

        return result

    def bbox(self):

        if not self.points:
            return None

        x, y = self.points[0]

        box = BoundingBox(
            x,
            y,
            x,
            y,
        )

        for x, y in self.points[1:]:

            box.expand(x, y)

        return box

    def raw_points(self):

        return list(self.points)