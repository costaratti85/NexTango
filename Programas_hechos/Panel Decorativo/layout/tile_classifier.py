from geometry.bbox import BoundingBox


INTERIOR = "interior"

LEFT = "left"
RIGHT = "right"

TOP = "top"
BOTTOM = "bottom"

TOP_LEFT = "top_left"
TOP_RIGHT = "top_right"

BOTTOM_LEFT = "bottom_left"
BOTTOM_RIGHT = "bottom_right"

OUTSIDE = "outside"


class TileClassifier:

    def __init__(
        self,
        xmin,
        ymin,
        xmax,
        ymax,
    ):

        self.xmin = xmin
        self.ymin = ymin

        self.xmax = xmax
        self.ymax = ymax

    def classify_bbox(self, bbox: BoundingBox):

        left = bbox.min_x < self.xmin
        right = bbox.max_x > self.xmax

        bottom = bbox.min_y < self.ymin
        top = bbox.max_y > self.ymax

        if (
            bbox.max_x < self.xmin or
            bbox.min_x > self.xmax or
            bbox.max_y < self.ymin or
            bbox.min_y > self.ymax
        ):
            return OUTSIDE

        if left and top:
            return TOP_LEFT

        if right and top:
            return TOP_RIGHT

        if left and bottom:
            return BOTTOM_LEFT

        if right and bottom:
            return BOTTOM_RIGHT

        if left:
            return LEFT

        if right:
            return RIGHT

        if top:
            return TOP

        if bottom:
            return BOTTOM

        return INTERIOR