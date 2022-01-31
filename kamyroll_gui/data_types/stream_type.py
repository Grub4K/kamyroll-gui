from enum import Enum



class StreamType(Enum):
    ADAPTIVE_HLS = "adaptive_hls"
    MOBILE_MP4 = "mobile_mp4"

    def __str__(self, /):
        return _CLEAR_NAME_LOOKUP[self]

    def __repr__(self, /):
        return f'<{self.__class__.__name__}.{self.name}>'


_CLEAR_NAME_LOOKUP = {
    StreamType.ADAPTIVE_HLS: "Adaptive, HLS",
    StreamType.MOBILE_MP4: "Mobile, mp4, HLS",
}
