from geometry.piece import Piece
from geometry.arc_segment import ArcSegment
from geometry.line_segment import LineSegment


def create_cuadriculado_piece(hole_shape, hole_size_mm, offset_x_mm, offset_y_mm):
    """
    hole_shape:   'circle' o 'square'
    hole_size_mm: diametro (circle) o lado (square)
    offset_x_mm:  distancia centro a centro en X
    offset_y_mm:  distancia centro a centro en Y
    """
    piece = Piece()

    if hole_shape == "circle":
        radius = hole_size_mm / 2.0
        piece.add(ArcSegment(0, 0, radius, 0, 360))
    elif hole_shape == "square":
        half = hole_size_mm / 2.0
        piece.add(LineSegment(-half, -half,  half, -half))
        piece.add(LineSegment( half, -half,  half,  half))
        piece.add(LineSegment( half,  half, -half,  half))
        piece.add(LineSegment(-half,  half, -half, -half))

    step_x = offset_x_mm
    step_y = offset_y_mm
    return piece, step_x, step_y
