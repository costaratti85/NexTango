import ezdxf

from geometry.piece import Piece

from geometry.line_segment import (
    LineSegment,
)

from geometry.arc_segment import (
    ArcSegment,
)


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

        return piece