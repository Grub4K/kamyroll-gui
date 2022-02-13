from dataclasses import dataclass
from enum import Enum

from .image_set import ImageSet
from .stream import Stream
from .subtitle import Subtitle
from .metadata import Metadata



class StreamResponseType(Enum):
    EPISODE = "episode"
    MOVIE = "movie"


@dataclass
class StreamResponse:
    type: StreamResponseType
    channel_id: str
    metadata: Metadata
    images: dict[str, ImageSet]
    streams: list[Stream]
    subtitles: list[Subtitle]
