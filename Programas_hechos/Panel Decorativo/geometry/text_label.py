class TextLabel:

    def __init__(
        self,
        text,
        x,
        y,
        height=100,
    ):

        self.text = text
        self.x = x
        self.y = y
        self.height = height

    def translated(self, dx, dy):

        return TextLabel(
            self.text,
            self.x + dx,
            self.y + dy,
            self.height,
        )

    def export_dxf(self, msp):

        msp.add_text(
            self.text,
            dxfattribs={
                "height": self.height,
            },
        ).set_placement(
            (self.x, self.y)
        )