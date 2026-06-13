from dataclasses import dataclass
import math


@dataclass
class Point:
    x: float
    y: float

    def distance_to(self, other: "Point") -> float:
        return math.hypot(other.x - self.x, other.y - self.y)

    def copy(self):
        return Point(self.x, self.y)