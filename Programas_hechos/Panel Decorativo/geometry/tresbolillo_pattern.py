import math

from geometry.piece import Piece
from geometry.arc_segment import ArcSegment


def create_tresbolillo_piece(
    diameter,
    distance,
):

    radius = diameter / 2.0

    dx = distance * math.sin(
        math.radians(60)
    )

    dy = distance * 0.5

    piece = Piece()

    piece.add(
        ArcSegment(
            0,
            0,
            radius,
            0,
            360,
        )
    )

    piece.add(
        ArcSegment(
            dx,
            dy,
            radius,
            0,
            360,
        )
    )

    step_x = dx * 2
    step_y = distance

    return piece, step_x, step_y