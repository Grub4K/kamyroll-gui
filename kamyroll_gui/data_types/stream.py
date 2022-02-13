from dataclasses import dataclass

from .locale import Locale
from .stream_type import StreamType

from ..utils import json_helper



_STREAM_TYPE_NAME_DICT = {
    "adaptive_hls": "Adaptive, HLS",
    "mobile_mp4": "Mobile, mp4, HLS",
}

@dataclass
class Stream:
    type: StreamType
    type_name: str
    audio_locale: str
    hardsub_locale: str
    url: str

    @classmethod
    def factory(cls, data):
        stream_type = data["type"]
        suffix = None
        if stream_type.startswith("simulcast"):
            suffix = " (Simulcast)"
            stream_type = stream_type.removeprefix("simulcast_")
        elif stream_type.startswith("uncut"):
            suffix = " (Uncut)"
            stream_type = stream_type.removeprefix("uncut_")

        data["type"] = stream_type

        type_name = _STREAM_TYPE_NAME_DICT.get(stream_type, "Unknown")
        if suffix:
            type_name += suffix

        data["type_name"] = type_name

        return json_helper.load_from_factory(data, cls)
