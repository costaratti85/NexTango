from layout.pattern_instance import (
    PatternInstance,
)


class PatternGenerator:

    def __init__(
        self,
        piece,
        step_x,
        step_y,
        classifier,
        variant_manager,
    ):

        self.piece = piece

        self.step_x = step_x
        self.step_y = step_y

        self.classifier = classifier

        self.variant_manager = (
            variant_manager
        )

    def generate(
        self,
        width,
        height,
    ):

        result = []

        bbox = self.piece.bbox()

        cols = int(width / self.step_x) + 3
        rows = int(height / self.step_y) + 3

        for row in range(rows):

            for col in range(cols):

                dx = col * self.step_x
                dy = row * self.step_y

                moved = bbox.moved(dx, dy)

                classification = (
                    self.classifier
                    .classify_bbox(moved)
                )

                if classification == "outside":
                    continue

                variant = (
                    self.variant_manager
                    .get_variant(
                        classification
                    )
                )

                result.append(
                    PatternInstance(
                        variant,
                        dx,
                        dy,
                        classification,
                    )
                )

        return result