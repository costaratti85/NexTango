from geometry.bbox import BoundingBox


class Piece:

    def __init__(self):

        self.entities = []

    def add(self, entity):

        self.entities.append(entity)

    def bbox(self):

        first = True

        box = None

        for e in self.entities:

            eb = e.bbox()

            if first:

                box = BoundingBox(
                    eb.min_x,
                    eb.min_y,
                    eb.max_x,
                    eb.max_y,
                )

                first = False

            else:

                box.expand(
                    eb.min_x,
                    eb.min_y,
                )

                box.expand(
                    eb.max_x,
                    eb.max_y,
                )

        return box

    def translated(self, dx, dy):

        result = Piece()

        for e in self.entities:

            result.add(
                e.translated(dx, dy)
            )

        return result

    def export_dxf(self, msp):

        for e in self.entities:

            e.export_dxf(msp)