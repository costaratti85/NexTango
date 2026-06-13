import ezdxf


class MixedDXFExporter:

    def save(
        self,
        items,
        filename,
    ):

        doc = ezdxf.new("R2010")
        msp = doc.modelspace()

        for item in items:

            if hasattr(item, "export_dxf"):

                item.export_dxf(msp)

            elif hasattr(item, "entities"):

                item.export_dxf(msp)

            elif hasattr(item, "points"):

                pts = []

                for p in item.points:

                    if hasattr(p, "as_tuple"):
                        pts.append(p.as_tuple())
                    else:
                        pts.append(p)

                msp.add_lwpolyline(
                    pts,
                    close=True,
                )

        doc.saveas(filename)