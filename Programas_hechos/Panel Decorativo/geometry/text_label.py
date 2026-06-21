class TextLabel:

    def __init__(
        self,
        text,
        x,
        y,
        height=100,
        right_align=False,
    ):

        self.text = text
        self.x = x
        self.y = y
        self.height = height
        self.right_align = right_align

    def translated(self, dx, dy):

        return TextLabel(
            self.text,
            self.x + dx,
            self.y + dy,
            self.height,
            self.right_align,
        )

    def export_dxf(self, msp):
        # MTEXT attachment_point: 3=TR (top-right, text extends left — right-aligned)
        #                         7=BL (bottom-left, text extends right — left-aligned)
        # TEXT halign=2 is not reliably rendered by all CAD viewers.
        attachment_point = 3 if self.right_align else 7
        msp.add_mtext(
            self.text,
            dxfattribs={
                "insert": (self.x, self.y),
                "char_height": self.height,
                "width": 0,
                "attachment_point": attachment_point,
            },
        )
