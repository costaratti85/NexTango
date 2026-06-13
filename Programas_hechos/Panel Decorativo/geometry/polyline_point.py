class PolylinePoint:

    def __init__(
        self,
        x,
        y,
        source=None,
        source_type="unknown",
    ):

        self.x = x
        self.y = y
        self.source = source
        self.source_type = source_type

    def as_tuple(self):

        return (
            self.x,
            self.y,
        )