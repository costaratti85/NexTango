from geometry.transform_utils import (
    translate_items,
)


class FigureVariantCache:

    def __init__(
        self,
        process_border_figure,
    ):

        self.process_border_figure = (
            process_border_figure
        )

        self.cache = {}

    def get(
        self,
        figure_index,
        figure,
        classification,
        base_dx,
        base_dy,
        window_xmin,
        window_ymin,
        window_xmax,
        window_ymax,
    ):

        key = (
            figure_index,
            classification,
            round(base_dx, 6),
            round(base_dy, 6),
            round(window_xmin, 6),
            round(window_ymin, 6),
            round(window_xmax, 6),
            round(window_ymax, 6),
        )

        if key in self.cache:

            cached_items = self.cache[key]

        else:

            moved = figure.translated(
                base_dx,
                base_dy,
            )

            if classification == "interior":

                cached_items = [moved]

            else:

                cached_items = self.process_border_figure(
                    moved,
                    window_xmin,
                    window_ymin,
                    window_xmax,
                    window_ymax,
                )

            self.cache[key] = cached_items

        return cached_items