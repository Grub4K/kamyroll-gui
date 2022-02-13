from dataclasses import dataclass

from ..utils import json_helper


@dataclass
class Subtitle:
    locale: str
    source: str
    format: str

    @classmethod
    def factory(cls, data):
        data["source"] = data["url"]
        return json_helper.load_from_factory(data, cls)
