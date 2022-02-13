from dataclasses import dataclass
from datetime import datetime, timedelta

from kamyroll_gui.utils import json_helper



@dataclass
class Metadata:
    title: str
    duration: timedelta
    description: str
    year: int

    @classmethod
    def factory(cls, data, /):
        if data["type"] == "episode":
            return _episode_metadata_from_response_dict(data)
        elif data["type"] == "movie":
            return _movie_metadata_from_response_dict(data)

        return NotImplemented


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


def _episode_metadata_from_response_dict(data):
    series_meta = data["parent_metadata"]
    episode_meta = data["episode_metadata"]

    duration_ms = episode_meta["duration_ms"]
    duration = timedelta(milliseconds=duration_ms)

    air_date = episode_meta["episode_air_date"]
    release_date = json_helper.load(air_date, datetime)

    return EpisodeMetadata(title=episode_meta["title"],
        description=episode_meta["description"], duration=duration,
        series=series_meta["title"], season=episode_meta["season_number"],
        season_name=episode_meta["season_title"],
        episode=episode_meta["episode_number"],
        episode_disp=episode_meta["episode"],
        date=release_date, year=release_date.year)


def _movie_metadata_from_response_dict(data, /):
    movie_meta = data["movie_metadata"]

    duration_ms = movie_meta["duration_ms"]
    duration = timedelta(milliseconds=duration_ms)

    return MovieMetadata(title=movie_meta["title"],
        description=movie_meta["description"], duration=duration,
        year=movie_meta["movie_release_year"])
