import json
import logging
import typing

from dataclasses import (
    asdict,
    dataclass,
    field,
    fields,
    is_dataclass,
)
from enum import Enum
from pathlib import Path
from types import GenericAlias

from .data_types import (
    Locale,
    Resolution,
)



_logger = logging.getLogger(__name__)


@dataclass
class Settings:
    audio_locale: Locale = Locale.JAPANESE_JP
    hardsub_locale: Locale = Locale.NONE
    subtitle_locales: list[Locale] = field(default_factory=list)
    video_height: Resolution = Resolution.R1080
    episode_format: str = "{series}/{series}.S{season}.E{episode}"
    subtitle_prefix: str = "subtitles"
    movie_format: str = "{title}"
    download_path: Path = Path("downloads")
    write_metadata: bool = False
    separate_subtitles: bool = False
    compress_streams: bool = False
    use_own_credentials: bool = False
    strict_matching: bool = False


class SettingsManager:
    def __init__(self, path, /):
        self.path = Path(path)
        self.load()

    def load(self, /):
        data = {}
        if self.path.exists():
            with self.path.open("rb") as file:
                try:
                    data = json.load(file)
                except ValueError as e:
                    _logger.warning("Error parsing settings json: %s", e)

        self.settings: Settings = self._parse_value(data, Settings)

        if not data:
            self.save()

    def save(self, /):
        data = self._dump_value(self.settings)

        with self.path.open("w") as file:
            json.dump(data, file, indent=4)

    @classmethod
    def _dump_value(cls, data):
        if isinstance(data, Enum):
            return data.value

        if is_dataclass(data):
            return cls._dump_value(asdict(data))

        if isinstance(data, dict):
            return {
                key: cls._dump_value(value)
                for key, value in data.items()
            }

        if isinstance(data, list):
            return [
                cls._dump_value(value)
                for value in data
            ]

        if isinstance(data, Path):
            return str(data.absolute().resolve().as_posix())

        for data_type in [int, str]:
            if isinstance(data, data_type):
                return data

    @classmethod
    def _parse_value(cls, data, field_type: type):
        if isinstance(field_type, GenericAlias):
            type_origin = typing.get_origin(field_type)
            if type_origin is list:
                if not isinstance(data, list):
                    return

                sub_type, = typing.get_args(field_type)
                constructed_list = []
                for value in data:
                    parsed_sub_value = cls._parse_value(value, sub_type)
                    if parsed_sub_value is not None:
                        constructed_list.append(parsed_sub_value)
                return constructed_list

            if type_origin is dict:
                if not isinstance(data, dict):
                    return

                _, sub_type = typing.get_args(field_type)
                constructed_dict = {}
                for key, value in data.items():
                    parsed_sub_value = cls._parse_value(value, sub_type)
                    if parsed_sub_value is not None:
                        constructed_dict[key] = parsed_sub_value
                return constructed_dict

        if type(data) is field_type:
            return data

        if issubclass(field_type, Enum):
            try:
                parsed_value = field_type(data)
            except ValueError:
                _logger.warning("%r is not of type %s", data, field_type)
                return

            return parsed_value

        if is_dataclass(field_type):
            rebuilt_data = {}
            for field in fields(field_type):
                value = data.get(field.name)
                if value is None:
                    continue

                parsed_value = cls._parse_value(value, field.type)
                if parsed_value is None:
                    continue

                rebuilt_data[field.name] = parsed_value

            return field_type(**rebuilt_data)

        if issubclass(field_type, Path):
            if not isinstance(data, str):
                return
            return Path(data)

        _logger.warning("Cannot parse value %r, type %s is unknown", data, field_type)


manager = SettingsManager("settings.json")
