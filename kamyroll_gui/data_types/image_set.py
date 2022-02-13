import bisect

from dataclasses import dataclass

from ..utils import json_helper



@dataclass
class Image:
    width: int
    height: int
    source: str


class ImageSet:
    def __init__(self, image_data, /):
        self._image_data = image_data
        self._image_data.sort(key=lambda x: x.width)

    @property
    def max(self, /):
        return self._image_data[-1]

    @property
    def min(self, /):
        return self._image_data[0]

    def get_by_width(self, width, /):
        index = bisect.bisect(self._image_data, width,
            hi=len(self._image_data)-1, key=lambda x: x.width)

        return self._image_data[index]

    def get_by_height(self, height, /):
        index = bisect.bisect(self._image_data, height,
            hi=len(self._image_data)-1, key=lambda x: x.height)
        if index is not None:
            return self._image_data[index]

    @classmethod
    def factory(cls, data, /):
        image_data = [
            json_helper.load(entry, Image)
            for entry in data
        ]

        return cls(image_data)
