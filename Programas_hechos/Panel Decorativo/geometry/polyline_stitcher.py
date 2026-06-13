from geometry.polyline import Polyline, points_close


def reversed_polyline(polyline):

    result = Polyline()

    result.points = list(reversed(polyline.points))
    result.segment_sources = list(
        reversed(polyline.segment_sources)
    )

    return result


def append_polyline(current, other):

    current.points.extend(other.points[1:])
    current.segment_sources.extend(other.segment_sources)


def prepend_polyline(current, other):

    result = Polyline()

    result.points = (
        other.points
        + current.points[1:]
    )

    result.segment_sources = (
        other.segment_sources
        + current.segment_sources
    )

    return result


class PolylineStitcher:

    def stitch(self, polylines):

        remaining = list(polylines)
        result = []

        while remaining:

            current = remaining.pop(0)

            changed = True

            while changed:

                changed = False

                current_start = current.points[0]
                current_end = current.points[-1]

                for i, other in enumerate(remaining):

                    other_start = other.points[0]
                    other_end = other.points[-1]

                    if points_close(current_end, other_start):

                        append_polyline(
                            current,
                            other,
                        )

                        remaining.pop(i)
                        changed = True
                        break

                    if points_close(current_end, other_end):

                        other_rev = reversed_polyline(
                            other
                        )

                        append_polyline(
                            current,
                            other_rev,
                        )

                        remaining.pop(i)
                        changed = True
                        break

                    if points_close(current_start, other_end):

                        current = prepend_polyline(
                            current,
                            other,
                        )

                        remaining.pop(i)
                        changed = True
                        break

                    if points_close(current_start, other_start):

                        other_rev = reversed_polyline(
                            other
                        )

                        current = prepend_polyline(
                            current,
                            other_rev,
                        )

                        remaining.pop(i)
                        changed = True
                        break

            result.append(current)

        return result