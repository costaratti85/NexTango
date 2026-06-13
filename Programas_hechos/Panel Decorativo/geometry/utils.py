import math


EPSILON = 1e-6


def almost_equal(a, b, eps=EPSILON):
    return abs(a - b) <= eps


def normalize_angle(angle):
    angle = angle % 360.0

    if angle < 0:
        angle += 360.0

    return angle


def angle_between(angle, start, end):

    angle = normalize_angle(angle)
    start = normalize_angle(start)
    end = normalize_angle(end)

    if start <= end:
        return start <= angle <= end

    return angle >= start or angle <= end


def point_angle(cx, cy, x, y):

    angle = math.degrees(
        math.atan2(y - cy, x - cx)
    )

    return normalize_angle(angle)