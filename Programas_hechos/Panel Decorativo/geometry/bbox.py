class BoundingBox:

    def __init__(
        self,
        min_x,
        min_y,
        max_x,
        max_y,
    ):

        self.min_x = min_x
        self.min_y = min_y

        self.max_x = max_x
        self.max_y = max_y

    def expand(self, x, y):

        self.min_x = min(self.min_x, x)
        self.min_y = min(self.min_y, y)

        self.max_x = max(self.max_x, x)
        self.max_y = max(self.max_y, y)

    @property
    def width(self):
        return self.max_x - self.min_x

    @property
    def height(self):
        return self.max_y - self.min_y

    def moved(self, dx, dy):

        return BoundingBox(
            self.min_x + dx,
            self.min_y + dy,
            self.max_x + dx,
            self.max_y + dy,
        )