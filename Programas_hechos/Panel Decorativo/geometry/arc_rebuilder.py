import math

from geometry.figure import Figure
from geometry.line_segment import LineSegment
from geometry.arc_segment import ArcSegment
from geometry.polyline import points_close


def angle_from_point(cx, cy, point):

    x, y = point

    angle = math.degrees(
        math.atan2(
            y - cy,
            x - cx,
        )
    )

    if angle < 0:
        angle += 360.0

    return angle


def orientation(p1, p2, p3):

    cross = (
        (p2[0] - p1[0])
        * (p3[1] - p1[1])
        - (p2[1] - p1[1])
        * (p3[0] - p1[0])
    )

    if cross >= 0:
        return "ccw"

    return "cw"


def add_line(fig, p1, p2):

    if points_close(p1, p2):
        return

    fig.add(
        LineSegment(
            p1[0],
            p1[1],
            p2[0],
            p2[1],
        )
    )


def add_arc(fig, source_arc, points):

    if len(points) < 2:
        return

    p_start = points[0]
    p_end = points[-1]

    if points_close(p_start, p_end):
        return

    if len(points) >= 3:
        p_mid = points[len(points) // 2]
    else:
        p_mid = p_start

    a1 = angle_from_point(
        source_arc.cx,
        source_arc.cy,
        p_start,
    )

    a2 = angle_from_point(
        source_arc.cx,
        source_arc.cy,
        p_end,
    )

    direction = orientation(
        p_start,
        p_mid,
        p_end,
    )

    if direction == "ccw":

        fig.add(
            ArcSegment(
                source_arc.cx,
                source_arc.cy,
                source_arc.radius,
                a1,
                a2,
            )
        )

    else:

        fig.add(
            ArcSegment(
                source_arc.cx,
                source_arc.cy,
                source_arc.radius,
                a2,
                a1,
            )
        )


class ArcRebuilder:

    def __init__(
        self,
        min_arc_points=2,
        tolerance=0.08,
        max_radius=500,
    ):

        self.min_arc_points = min_arc_points
        self.tolerance = tolerance
        self.max_radius = max_radius

    def rebuild_polyline(self, polyline):

        fig = Figure()

        points = polyline.points
        metas = polyline.segment_sources

        if len(points) < 2:
            return fig

        i = 0

        while i < len(metas):

            meta = metas[i]

            source = meta.get("source")
            source_type = meta.get(
                "source_type",
                "unknown",
            )

            j = i + 1

            while j < len(metas):

                next_meta = metas[j]

                if (
                    next_meta.get("source_type")
                    != source_type
                ):
                    break

                if (
                    next_meta.get("source")
                    is not source
                ):
                    break

                j += 1

            group_points = points[i : j + 1]

            if (
                source_type == "arc"
                and source is not None
            ):

                add_arc(
                    fig,
                    source,
                    group_points,
                )

            else:

                for k in range(
                    len(group_points) - 1
                ):

                    add_line(
                        fig,
                        group_points[k],
                        group_points[k + 1],
                    )

            i = j

        return fig

    def rebuild_all(self, polylines):

        result = []

        for polyline in polylines:

            result.append(
                self.rebuild_polyline(polyline)
            )

        return result