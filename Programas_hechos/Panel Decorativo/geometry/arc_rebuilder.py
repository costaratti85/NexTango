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


def _angle_distance(a, b):
    """Minimum angular distance between two angles in [0, 360)."""
    d = abs(a - b) % 360.0
    return min(d, 360.0 - d)


def add_arc(fig, source_arc, points):

    if len(points) < 2:
        return

    p_start = points[0]
    p_end = points[-1]

    if points_close(p_start, p_end):
        return

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

    if len(points) >= 3:

        p_mid = points[len(points) // 2]

        direction = orientation(
            p_start,
            p_mid,
            p_end,
        )

    else:

        # Only 2 points — the cross product of (p_mid=p_start, p_end) is always
        # zero, so orientation() is unreliable.  Instead, infer direction from
        # the source arc: whichever of a1/a2 is closer to source_arc.start_angle
        # becomes the "start" of the rebuilt arc (CCW ordering preserved).
        src_start = source_arc.start_angle % 360.0

        if _angle_distance(a1, src_start) <= _angle_distance(a2, src_start):
            direction = "ccw"   # a1 ~ src start, a2 ~ src end → same direction
        else:
            direction = "cw"    # a1 ~ src end, a2 ~ src start → reversed

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

        cw_arc = ArcSegment(
            source_arc.cx,
            source_arc.cy,
            source_arc.radius,
            a2,
            a1,
        )
        # _flipped keeps start_point()/end_point() in polyline order (a1→a2)
        # while export_dxf() still draws the arc using the swapped a2→a1 angles.
        cw_arc._flipped = True
        fig.add(cw_arc)


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

        # Scan backwards to find the contiguous "closing" group at the tail.
        # There can be 1 closing segment (same-margin case) or 2 (corner case,
        # where the two free nodes lie on perpendicular margins and the path
        # routes through the clip-rect corner).  All closing segments are held
        # back and added at the end with corrected endpoints.
        #
        # Why: the clipper clips chords (straight lines between discretised arc
        # points) so a clipped boundary point lies on the chord, NOT on the
        # circle.  When add_arc() maps that point back via atan2 + cos/sin it
        # lands on the circle at a slightly different position.  Without this
        # correction the closing LINE starts/ends at the chord point while the
        # adjacent ARC entity ends/starts on the circle — producing a gap.
        closing_start_idx = len(metas)
        while (
            closing_start_idx > 0
            and metas[closing_start_idx - 1].get("source_type") == "closing"
        ):
            closing_start_idx -= 1

        has_closing = closing_start_idx < len(metas)
        process_count = closing_start_idx

        i = 0

        while i < process_count:

            meta = metas[i]

            source = meta.get("source")
            source_type = meta.get(
                "source_type",
                "unknown",
            )

            j = i + 1

            while j < process_count:

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

        if has_closing and fig.entities:
            # Closing endpoints corrected to the actual arc/line entity endpoints.
            # Any intermediate corner point (corner case) is taken verbatim from
            # the polyline — it is an exact clip-rect vertex, not a chord
            # interpolation, so it needs no correction.
            p_first = fig.entities[-1].end_point()
            p_last = fig.entities[0].start_point()
            intermediate = points[closing_start_idx + 1 : len(metas)]
            current = p_first
            for pt in intermediate:
                add_line(fig, current, pt)
                current = pt
            add_line(fig, current, p_last)

        return fig

    def rebuild_all(self, polylines):

        result = []

        for polyline in polylines:

            result.append(
                self.rebuild_polyline(polyline)
            )

        return result