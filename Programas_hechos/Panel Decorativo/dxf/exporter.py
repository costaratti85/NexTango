import ezdxf

from geometry.line_segment import LineSegment
from geometry.arc_segment import ArcSegment


class DXFExporter:

    def save_piece(self, piece, filename):

        doc = ezdxf.new("R2010")
        msp = doc.modelspace()

        for poly in piece.polylines:

            for seg in poly.segments:

                if isinstance(seg, LineSegment):

                    msp.add_line(
                        (seg.start.x, seg.start.y),
                        (seg.end.x, seg.end.y),
                    )

                elif isinstance(seg, ArcSegment):

                    msp.add_arc(
                        center=(seg.center.x, seg.center.y),
                        radius=seg.radius,
                        start_angle=seg.start_angle,
                        end_angle=seg.end_angle,
                    )

        doc.saveas(filename)