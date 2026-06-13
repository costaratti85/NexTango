import ezdxf


class PolylineDXFExporter:

    def save_polylines(
        self,
        polylines,
        filename,
    ):

        doc = ezdxf.new("R2010")
        msp = doc.modelspace()

        for poly in polylines:

            if len(poly.points) < 2:
                continue

            msp.add_lwpolyline(
                poly.points,
                close=True,
            )

        doc.saveas(filename)