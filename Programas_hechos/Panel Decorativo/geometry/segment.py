from abc import ABC, abstractmethod


class Segment(ABC):

    @abstractmethod
    def bbox(self):
        pass

    @abstractmethod
    def start_point(self):
        pass

    @abstractmethod
    def end_point(self):
        pass