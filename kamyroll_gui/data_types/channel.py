from enum import Enum



class Channel(Enum):
    CRUNCHYROLL = "crunchyroll"
    FUNIMATION = "funimation"
    ADN = "adn"

    def __str__(self, /):
        return _CLEAR_NAME_LOOKUP[self]

_CLEAR_NAME_LOOKUP = {
    Channel.CRUNCHYROLL: "Crunchyroll",
    Channel.FUNIMATION: "Funimation",
    Channel.ADN: "Anime Digital Network",
}
