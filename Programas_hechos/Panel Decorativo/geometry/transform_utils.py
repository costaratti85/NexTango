from geometry.polyline import Polyline


def translate_item(item, dx, dy):

    if hasattr(item, "translated"):
        return item.translated(dx, dy)

    if hasattr(item, "points"):

        result = Polyline()

        result.points = [
            (x + dx, y + dy)
            for x, y in item.points
        ]

        result.segment_sources = list(
            item.segment_sources
        )

        return result

    return item


def translate_items(items, dx, dy):

    return [
        translate_item(item, dx, dy)
        for item in items
    ]