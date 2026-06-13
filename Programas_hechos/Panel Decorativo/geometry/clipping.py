from geometry.point import Point
from geometry.line_segment import LineSegment
from geometry.arc_segment import ArcSegment

from geometry.intersections import (
    line_vertical_intersection,
    line_horizontal_intersection,
    arc_vertical_intersections,
    arc_horizontal_intersections,
)

import math


INSIDE = 0
LEFT = 1
RIGHT = 2
BOTTOM = 4
TOP = 8

EPSILON = 1e-6


def normalize_angle(angle):

    angle = angle % 360.0

    if angle < 0:
        angle += 360.0

    return angle


def point_inside(x, y, xmin, ymin, xmax, ymax):

    return (
        xmin <= x <= xmax and
        ymin <= y <= ymax
    )


def compute_out_code(x, y, xmin, ymin, xmax, ymax):

    code = INSIDE

    if x < xmin:
        code |= LEFT

    elif x > xmax:
        code |= RIGHT

    if y < ymin:
        code |= BOTTOM

    elif y > ymax:
        code |= TOP

    return code


def clip_line(segment, xmin, ymin, xmax, ymax):

    x1 = segment.start.x
    y1 = segment.start.y

    x2 = segment.end.x
    y2 = segment.end.y

    outcode1 = compute_out_code(
        x1, y1,
        xmin, ymin, xmax, ymax
    )

    outcode2 = compute_out_code(
        x2, y2,
        xmin, ymin, xmax, ymax
    )

    accept = False

    while True:

        if not (outcode1 | outcode2):

            accept = True
            break

        elif outcode1 & outcode2:

            break

        else:

            outcode_out = outcode1 or outcode2

            if outcode_out & TOP:

                p = line_horizontal_intersection(
                    segment.start,
                    segment.end,
                    ymax
                )

            elif outcode_out & BOTTOM:

                p = line_horizontal_intersection(
                    segment.start,
                    segment.end,
                    ymin
                )

            elif outcode_out & RIGHT:

                p = line_vertical_intersection(
                    segment.start,
                    segment.end,
                    xmax
                )

            elif outcode_out & LEFT:

                p = line_vertical_intersection(
                    segment.start,
                    segment.end,
                    xmin
                )

            else:
                return None

            if p is None:
                return None

            if outcode_out == outcode1:

                x1 = p.x
                y1 = p.y

                outcode1 = compute_out_code(
                    x1, y1,
                    xmin, ymin, xmax, ymax
                )

            else:

                x2 = p.x
                y2 = p.y

                outcode2 = compute_out_code(
                    x2, y2,
                    xmin, ymin, xmax, ymax
                )

    if not accept:
        return None

    return LineSegment(
        Point(x1, y1),
        Point(x2, y2),
    )


def clip_arc(arc, xmin, ymin, xmax, ymax):

    start = normalize_angle(arc.start_angle)
    end = normalize_angle(arc.end_angle)

    full_circle = abs(start - end) < EPSILON

    if full_circle:
        end = start + 360.0

    elif end <= start:
        end += 360.0

    split_angles = [start, end]

    intersections = []

    for x in [xmin, xmax]:

        intersections.extend(
            arc_vertical_intersections(
                arc.center,
                arc.radius,
                start,
                end,
                x,
            )
        )

    for y in [ymin, ymax]:

        intersections.extend(
            arc_horizontal_intersections(
                arc.center,
                arc.radius,
                start,
                end,
                y,
            )
        )

    for p, angle in intersections:

        a = angle

        while a < start:
            a += 360.0

        split_angles.append(a)

    split_angles = sorted(split_angles)

    cleaned = []

    for a in split_angles:

        if not cleaned:
            cleaned.append(a)

        elif abs(a - cleaned[-1]) > EPSILON:
            cleaned.append(a)

    split_angles = cleaned

    result = []

    for i in range(len(split_angles) - 1):

        a1 = split_angles[i]
        a2 = split_angles[i + 1]

        amid = (a1 + a2) / 2.0

        r = math.radians(amid)

        x = arc.center.x + arc.radius * math.cos(r)
        y = arc.center.y + arc.radius * math.sin(r)

        if point_inside(
            x, y,
            xmin, ymin, xmax, ymax
        ):

            result.append(
                ArcSegment(
                    arc.center,
                    arc.radius,
                    a1,
                    a2,
                )
            )

    return result