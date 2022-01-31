from dataclasses import dataclass

from .locale import Locale
from .stream_type import StreamType



@dataclass
class Stream:
    type: StreamType
    type_name: str
    audio_locale: Locale
    hardsub_locale: Locale
    url: str
