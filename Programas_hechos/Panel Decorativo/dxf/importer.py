import math

import ezdxf

from geometry.piece import Piece

from geometry.line_segment import (
    LineSegment,
)

from geometry.arc_segment import (
    ArcSegment,
)


def _bulge_to_arc(x1, y1, x2, y2, bulge):
    """Convert a LWPOLYLINE bulge segment to (cx, cy, radius, start_angle, end_angle, is_cw).

    Uses the same math as dxf_spline_to_arcs.process_lwpolyline so that
    both paths produce geometrically identical results.
    Returns None for degenerate (zero-length) segments.
    """
    dx = x2 - x1
    dy = y2 - y1
    chord = math.sqrt(dx * dx + dy * dy)
    if chord < 1e-10:
        return None

    radius = abs(chord / (2.0 * math.sin(2.0 * math.atan(bulge))))
    perp_x = -dy / chord
    perp_y = dx / chord
    sagitta = radius * math.cos(2.0 * math.atan(bulge))
    cx = (x1 + x2) / 2.0 + perp_x * sagitta
    cy = (y1 + y2) / 2.0 + perp_y * sagitta

    start_angle = math.degrees(math.atan2(y1 - cy, x1 - cx))
    end_angle = math.degrees(math.atan2(y2 - cy, x2 - cx))

    is_cw = bulge < 0
    if is_cw:
        start_angle, end_angle = end_angle, start_angle

    return cx, cy, radius, start_angle, end_angle, is_cw


class DXFImporter:

    def load(self, filename):

        doc = ezdxf.readfile(filename)

        msp = doc.modelspace()

        piece = Piece()

        for entity in msp:

            dxftype = entity.dxftype()

            #
            # LINE
            #

            if dxftype == "LINE":

                start = entity.dxf.start
                end = entity.dxf.end

                piece.add(

                    LineSegment(
                        start.x,
                        start.y,
                        end.x,
                        end.y,
                    )

                )

            #
            # ARC
            #

            elif dxftype == "ARC":

                center = entity.dxf.center

                piece.add(

                    ArcSegment(
                        center.x,
                        center.y,
                        entity.dxf.radius,
                        entity.dxf.start_angle,
                        entity.dxf.end_angle,
                    )

                )

            #
            # CIRCLE
            #

            elif dxftype == "CIRCLE":

                center = entity.dxf.center

                piece.add(

                    ArcSegment(
                        center.x,
                        center.y,
                        entity.dxf.radius,
                        0,
                        360,
                    )

                )

            #
            # LWPOLYLINE — explode each segment to LineSegment / ArcSegment
            #

            elif dxftype == "LWPOLYLINE":

                try:
                    vertices = list(entity.get_points(format="xyseb"))
                except Exception:
                    continue

                n = len(vertices)
                if n < 2:
                    continue

                is_closed = bool(entity.dxf.flags & 1)
                limit = n if is_closed else n - 1

                for i in range(limit):
                    curr = vertices[i]
                    nxt = vertices[(i + 1) % n]

                    x1, y1 = curr[0], curr[1]
                    x2, y2 = nxt[0], nxt[1]
                    bulge = curr[4] if len(curr) > 4 else 0.0

                    if abs(bulge) < 1e-10:
                        piece.add(LineSegment(x1, y1, x2, y2))
                    else:
                        result = _bulge_to_arc(x1, y1, x2, y2, bulge)
                        if result is None:
                            continue
                        cx, cy, radius, start_angle, end_angle, is_cw = result
                        seg = ArcSegment(cx, cy, radius, start_angle, end_angle)
                        if is_cw:
                            seg._flipped = True
                        piece.add(seg)

        return piece