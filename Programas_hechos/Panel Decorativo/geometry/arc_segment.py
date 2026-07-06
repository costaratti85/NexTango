import math

from geometry.bbox import BoundingBox


class ArcSegment:

    def __init__(
        self,
        cx,
        cy,
        radius,
        start_angle,
        end_angle,
    ):

        self.cx = cx
        self.cy = cy
        self.radius = radius
        self.start_angle = start_angle
        self.end_angle = end_angle
        # When True, start_point/end_point are swapped so the EntityStitcher
        # can chain this arc in reverse direction without changing which arc is
        # drawn.  export_dxf always uses start_angle/end_angle unchanged.
        self._flipped = False

    def _point_at(self, angle_deg):

        a = math.radians(angle_deg)

        return (
            self.cx + math.cos(a) * self.radius,
            self.cy + math.sin(a) * self.radius,
        )

    def start_point(self):

        return self._point_at(
            self.end_angle if self._flipped else self.start_angle
        )

    def end_point(self):

        return self._point_at(
            self.start_angle if self._flipped else self.end_angle
        )

    def reversed(self):
        """Return the same geometric arc with start/end connectivity swapped.

        The EntityStitcher calls this when it needs to chain an entity in the
        opposite direction.  For a LINE this is transparent (same path), but for
        an ARC swapping start_angle/end_angle would produce the *complementary*
        arc (the other 360-θ degrees around the circle) — a completely different
        cut path.  Instead we toggle _flipped so connectivity is correct while
        export_dxf still draws the original arc.
        """

        result = ArcSegment(
            self.cx,
            self.cy,
            self.radius,
            self.start_angle,
            self.end_angle,
        )

        result._flipped = not self._flipped

        return result

    def bbox(self):

        return BoundingBox(
            self.cx - self.radius,
            self.cy - self.radius,
            self.cx + self.radius,
            self.cy + self.radius,
        )

    def translated(self, dx, dy):

        result = ArcSegment(
            self.cx + dx,
            self.cy + dy,
            self.radius,
            self.start_angle,
            self.end_angle,
        )

        result._flipped = self._flipped

        return result

    def export_dxf(self, msp):
        # CCW span: (end - start) % 360. abs() gives wrong result for arcs
        # crossing 0° (e.g. start=350, end=10 → abs gives 340, not 20).
        span = (self.end_angle - self.start_angle) % 360
        if span == 0 or span >= 350:
            # near-complete arc → output as CIRCLE (cleaner laser path, no tiny gap)
            msp.add_circle(
                (self.cx, self.cy),
                self.radius,
            )
        else:
            msp.add_arc(
                (self.cx, self.cy),
                self.radius,
                self.start_angle,
                self.end_angle,
            )
