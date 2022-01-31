from dataclasses import dataclass
from datetime import datetime, timedelta



@dataclass
class Metadata:
    title: str
    duration: timedelta
    description: str
    year: int


@dataclass
class EpisodeMetadata(Metadata):
    series: str
    season: int
    season_name: str
    episode: int
    episode_disp: str
    date: datetime


@dataclass
class MovieMetadata(Metadata):
    pass
