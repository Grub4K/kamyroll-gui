import re
import logging
import typing
import dataclasses
from datetime import datetime, timedelta

from enum import Enum
from pathlib import Path
from types import GenericAlias, NoneType



DATETIME_RE = re.compile(r""
    + r"(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})"
    + r"(?:T| )"
    + r"(?P<hours>\d+):(?P<minutes>\d+):(?P<seconds>\d+)(?P<fraction>\.\d+)?"
    + r"(?:(?P<tzinfo>Z|\+|-)(?:(?P<tzhours>\d{2}):(?P<tzminutes>\d{2}))?)?")
NATIVE_TYPES = [str, bool, int, float, NoneType]
T = typing.TypeVar("T", bound=type)

_logger = logging.getLogger(__name__)


class DumpError(TypeError):
    pass

class LoadError(ValueError):
    pass


def dump(data):
    if isinstance(data, Enum):
        return data.value

    if dataclasses.is_dataclass(data):
        return dump(dataclasses.asdict(data))

    if isinstance(data, dict):
        return {
            key: dump(value)
            for key, value in data.items()
        }

    if isinstance(data, list):
        return [
            dump(value)
            for value in data
        ]

    if isinstance(data, re.Pattern):
        return data.pattern

    if isinstance(data, Path):
        return str(data.absolute().resolve().as_posix())

    if isinstance(data, datetime):
        return data.isoformat(sep=" ", timespec="milliseconds")

    for data_type in NATIVE_TYPES:
        if isinstance(data, data_type):
            return data

    message = f"Type {type(data)} is not supported for dumping"
    raise DumpError(message)

def load(data, field_type: T, /, resolve_factory=True) -> T:
    if type(data) is field_type:
        return_value = data

    elif field_type in NATIVE_TYPES:
        _logger.error("Cannot parse value %r, incompatible with type %s",
            data, field_type)
        raise LoadError(f"{type(data)} is incompatible with {field_type}")

    elif isinstance(field_type, GenericAlias):
        type_origin = typing.get_origin(field_type)
        if type_origin is list:
            if not isinstance(data, list):
                raise LoadError

            (sub_type,) = typing.get_args(field_type)
            return_value = [load(value, sub_type) for value in data]

        elif type_origin is dict:
            if not isinstance(data, dict):
                raise LoadError

            # For a json the key will always be str
            # We dont force a conversion here
            _, sub_type = typing.get_args(field_type)
            return_value = {
                key: load(value, sub_type)
                for key, value in data.items()
            }

        else:
            _logger.error("Cannot parse value %r, type %s is unknown",
                data, field_type)
            raise LoadError(f"The type {field_type} is unknown")

    elif issubclass(field_type, Enum):
        return_value = field_type(data)

    elif dataclasses.is_dataclass(field_type):
        if not isinstance(data, dict):
            raise LoadError(f"Type {field_type} expects a dict")
        factory_function = getattr(field_type, "factory", None)
        if resolve_factory and factory_function is not None:
            return_value = _execute_factory(factory_function, data, field_type)
        else:
            rebuilt_data = {}
            for field in dataclasses.fields(field_type):
                value = data.get(field.name)
                factory_function = getattr(field.type, "factory", None)
                if resolve_factory and factory_function is not None:
                    parsed_value = _execute_factory(factory_function, data, field.type)
                elif value is not None:
                    parsed_value = load(value, field.type)
                elif field.default is not dataclasses.MISSING:
                    parsed_value = load(field.default, field.type)
                elif field.default_factory is not dataclasses.MISSING:
                    parsed_value = load(field.default_factory(), field.type)
                else:
                    message = f"The required key {field.name} is missing"
                    raise LoadError(message)

                rebuilt_data[field.name] = parsed_value

            return_value = field_type(**rebuilt_data)

    elif field_type is re.Pattern:
        if not isinstance(data, str):
            raise LoadError(f"Type {re.Pattern} expects a string")

        return_value = re.compile(data)

    elif field_type is Path:
        if not isinstance(data, str):
            raise LoadError(f"Type {Path} expects a string")
        return_value = Path(data)

    elif field_type is datetime:
        return_value = _parse_datetime(data)

    else:
        factory_function = getattr(field_type, "factory", None)
        if resolve_factory and factory_function is not None:
            return_value = _execute_factory(factory_function, data, field_type)
        else:
            _logger.error("Type %s is unsupported", field_type)
            raise LoadError(f"Type {field_type} is unsupported")

    return typing.cast(T, return_value)

def load_from_factory(data, cls):
    return load(data, cls, resolve_factory=False)


def _execute_factory(factory_function, data, field_type):
    try:
        return_value = factory_function(data)

    except KeyError as error:
        message = f"Error while invoking factory, key {error} missing"
        raise LoadError(message) from None

    except Exception as error:
        message = f"Unknown error while invoking factory: {error}"
        raise LoadError(message)

    if data is NotImplemented:
        message = "Invalid data found while processing input"
        raise LoadError(message)

    if not isinstance(return_value, field_type):
        message = f"{type(return_value)} is incompatible with {field_type}"
        raise LoadError(message)

    if dataclasses.is_dataclass(return_value):
        for field in dataclasses.fields(return_value):
            value = getattr(return_value, field.name)
            if not isinstance(value, field.type):
                message = f"{type(data)} is incompatible with {field.type}"
                raise LoadError(message)

    return return_value

def _parse_datetime(data):
    if isinstance(data, int):
        return datetime.utcfromtimestamp(data)
    elif not isinstance(data, str):
        raise LoadError("Type datetime expects a str or int")

    match = DATETIME_RE.fullmatch(data)
    if not match:
        raise LoadError("Unknown date format")

    year = int(match["year"])
    month = int(match["month"])
    day = int(match["day"])
    hours = int(match["hours"])
    minutes = int(match["minutes"])
    seconds = int(match["seconds"])
    seconds_fraction = float(match["fraction"] or 0)
    microseconds = int(seconds_fraction * 1_000_000)


    parsed = datetime(year=year, month=month, day=day,
        hour=hours, minute=minutes, second=seconds, microsecond=microseconds)
    tzinfo = match["tzinfo"]
    if tzinfo in ["+", "-"]:
        tzhours = int(match["tzhours"])
        tzminutes = int(match["tzminutes"])
        tzdiff = timedelta(hours=tzhours, minutes=tzminutes)

        if tzinfo == "+":
            parsed -= tzdiff
        elif tzinfo == "-":
            parsed += tzdiff

    return parsed
