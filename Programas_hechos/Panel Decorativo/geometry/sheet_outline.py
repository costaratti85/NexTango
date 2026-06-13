from geometry.polyline import Polyline


def create_sheet_outline(
    x,
    y,
    width,
    height,
):

    poly = Polyline()

    poly.add_point(x, y)
    poly.add_point(x + width, y)
    poly.add_point(x + width, y + height)
    poly.add_point(x, y + height)
    poly.add_point(x, y)

    return poly