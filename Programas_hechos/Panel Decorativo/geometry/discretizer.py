import math

from geometry.polyline import Polyline
from geometry.line_segment import LineSegment
from geometry.arc_segment import ArcSegment


class Discretizer:

    def __init__(self, arc_step_degrees=5):

        self.arc_step_degrees = arc_step_degrees

    def discretize_piece(self, piece):

        result = []

        for entity in piece.entities:

            result.append(
                self.discretize_entity(entity)
            )

        return result

    def discretize_entity(self, entity):

        if isinstance(entity, LineSegment):

            poly = Polyline()

            poly.add_segment(
                entity.x1,
                entity.y1,
                entity.x2,
                entity.y2,
                entity,
                "line",
            )

            return poly

        if isinstance(entity, ArcSegment):

            return self.discretize_arc(entity)

        raise Exception("Entidad no soportada")

    def discretize_arc(self, arc):

        poly = Polyline()

        start = arc.start_angle
        end = arc.end_angle

        if end <= start:
            end += 360

        points = []

        angle = start

        while angle < end:

            a = math.radians(angle)

            points.append(
                (
                    arc.cx + math.cos(a) * arc.radius,
                    arc.cy + math.sin(a) * arc.radius,
                )
            )

            angle += self.arc_step_degrees

        a = math.radians(end)

        points.append(
            (
                arc.cx + math.cos(a) * arc.radius,
                arc.cy + math.sin(a) * arc.radius,
            )
        )

        for i in range(len(points) - 1):

            x1, y1 = points[i]
            x2, y2 = points[i + 1]

            poly.add_segment(
                x1,
                y1,
                x2,
                y2,
                arc,
                "arc",
            )

        return poly