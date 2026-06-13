from geometry.figure import Figure


EPSILON = 1e-5


def points_close(a, b):

    return (
        abs(a[0] - b[0]) <= EPSILON
        and
        abs(a[1] - b[1]) <= EPSILON
    )


class EntityStitcher:

    def stitch(self, entities):

        remaining = list(entities)
        figures = []

        while remaining:

            current = Figure()
            current.add(remaining.pop(0))

            changed = True

            while changed:

                changed = False

                current_start = current.entities[0].start_point()
                current_end = current.entities[-1].end_point()

                for i, other in enumerate(remaining):

                    other_start = other.start_point()
                    other_end = other.end_point()

                    if points_close(current_end, other_start):

                        current.add(other)
                        remaining.pop(i)
                        changed = True
                        break

                    if points_close(current_end, other_end):

                        current.add(other.reversed())
                        remaining.pop(i)
                        changed = True
                        break

                    if points_close(current_start, other_end):

                        new_figure = Figure()
                        new_figure.add(other)

                        for e in current.entities:
                            new_figure.add(e)

                        current = new_figure
                        remaining.pop(i)
                        changed = True
                        break

                    if points_close(current_start, other_start):

                        new_figure = Figure()
                        new_figure.add(other.reversed())

                        for e in current.entities:
                            new_figure.add(e)

                        current = new_figure
                        remaining.pop(i)
                        changed = True
                        break

            figures.append(current)

        return figures