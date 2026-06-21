from geometry.polyline import (
    Polyline,
    points_close,
)

# Spline-to-arc conversion can leave a sub-millimetre gap between the first
# and last point of an otherwise closed contour.  Use a looser threshold so
# the merge logic correctly reconnects the two wrap-around fragments instead
# of leaving each one with a long interior-to-boundary closing segment.
_CLOSE_THRESHOLD = 0.01


def is_closed(polyline):

    if len(polyline.points) < 3:
        return False

    p0 = polyline.points[0]
    pl = polyline.points[-1]

    return (
        abs(p0[0] - pl[0]) <= _CLOSE_THRESHOLD
        and abs(p0[1] - pl[1]) <= _CLOSE_THRESHOLD
    )


class PolylineClipper:

    def __init__(self, rect_clipper):

        self.rect_clipper = rect_clipper

    def clip_polyline(self, polyline):

        result = []
        current = None

        segments = polyline.segments()

        for segment in segments:

            clipped = self.rect_clipper.clip_segment(
                segment
            )

            if clipped is None:

                if current is not None:

                    if len(current.points) >= 2:
                        result.append(current)

                    current = None

                continue

            source = getattr(
                segment,
                "source",
                None,
            )

            source_type = getattr(
                segment,
                "source_type",
                "unknown",
            )

            if current is None:
                current = Polyline()
            elif not points_close(
                current.points[-1],
                (clipped.x1, clipped.y1),
            ):
                # Gap between current fragment's last point and this segment's
                # start — two different boundary clip points created by
                # consecutive outside segments.  Close the current fragment so
                # that segment_sources stay aligned with points, then open a
                # fresh one starting at the new clip point.
                if len(current.points) >= 2:
                    result.append(current)
                current = Polyline()

            current.add_segment(
                clipped.x1,
                clipped.y1,
                clipped.x2,
                clipped.y2,
                source,
                source_type,
            )

        if current is not None:

            if len(current.points) >= 2:
                result.append(current)

        if (
            is_closed(polyline)
            and len(result) >= 2
        ):

            first_fragment = result[0]
            last_fragment = result[-1]

            if (
                points_close(
                    first_fragment.points[0],
                    polyline.points[0],
                )
                and points_close(
                    last_fragment.points[-1],
                    polyline.points[-1],
                )
            ):

                merged = Polyline()

                merged.points = (
                    last_fragment.points
                    + first_fragment.points[1:]
                )

                merged.segment_sources = (
                    last_fragment.segment_sources
                    + first_fragment.segment_sources
                )

                result = (
                    [merged]
                    + result[1:-1]
                )

        return result