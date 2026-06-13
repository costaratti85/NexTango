import math

from geometry.point import Point


EPSILON = 1e-6


def point_angle(cx, cy, x, y):

    angle = math.degrees(
        math.atan2(y - cy, x - cx)
    )

    if angle < 0:
        angle += 360.0

    return angle


def angle_in_range(angle, start, end):

    while angle < start:
        angle += 360.0

    return (
        start - EPSILON <= angle <= end + EPSILON
    )


def line_vertical_intersection(p1, p2, x):

    dx = p2.x - p1.x

    if abs(dx) < EPSILON:
        return None

    t = (x - p1.x) / dx

    if t < 0 or t > 1:
        return None

    y = p1.y + t * (p2.y - p1.y)

    return Point(x, y)


def line_horizontal_intersection(p1, p2, y):

    dy = p2.y - p1.y

    if abs(dy) < EPSILON:
        return None

    t = (y - p1.y) / dy

    if t < 0 or t > 1:
        return None

    x = p1.x + t * (p2.x - p1.x)

    return Point(x, y)


def arc_vertical_intersections(
    center,
    radius,
    start_angle,
    end_angle,
    x,
):

    dx = x - center.x

    if abs(dx) > radius:
        return []

    dy = math.sqrt(radius * radius - dx * dx)

    result = []

    for y in [center.y + dy, center.y - dy]:

        angle = point_angle(
            center.x,
            center.y,
            x,
            y,
        )

        if angle_in_range(
            angle,
            start_angle,
            end_angle,
        ):

            while angle < start_angle:
                angle += 360.0

            result.append(
                (
                    Point(x, y),
                    angle,
                )
            )

    return result


def arc_horizontal_intersections(
    center,
    radius,
    start_angle,
    end_angle,
    y,
):

    dy = y - center.y

    if abs(dy) > radius:
        return []

    dx = math.sqrt(radius * radius - dy * dy)

    result = []

    for x in [center.x + dx, center.x - dx]:

        angle = point_angle(
            center.x,
            center.y,
            x,
            y,
        )

        if angle_in_range(
            angle,
            start_angle,
            end_angle,
        ):

            while angle < start_angle:
                angle += 360.0

            result.append(
                (
                    Point(x, y),
                    angle,
                )
            )

    return result