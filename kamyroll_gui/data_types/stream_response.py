from dataclasses import dataclass
from enum import Enum

from .channel import Channel
from .stream import Stream
from .subtitle import Subtitle
from .metadata import Metadata



class StreamResponseType(Enum):
    EPISODE = "episode"
    MOVIE = "movie"


@dataclass
class StreamResponse:
    type: StreamResponseType
    channel: Channel
    metadata: Metadata
    images: dict[str, str]
    streams: list[Stream]
    subtitles: list[Subtitle]
