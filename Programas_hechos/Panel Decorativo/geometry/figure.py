class Figure:

    def __init__(self):

        self.entities = []

    def add(self, entity):

        self.entities.append(entity)

    def bbox(self):

        if not self.entities:
            return None

        box = self.entities[0].bbox()

        for e in self.entities[1:]:

            eb = e.bbox()

            box.expand(eb.min_x, eb.min_y)
            box.expand(eb.max_x, eb.max_y)

        return box

    def translated(self, dx, dy):

        result = Figure()

        for e in self.entities:
            result.add(e.translated(dx, dy))

        return result

    def export_dxf(self, msp):

        for e in self.entities:
            e.export_dxf(msp)