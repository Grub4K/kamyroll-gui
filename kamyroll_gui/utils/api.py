import re
import json
import logging

from datetime import datetime, timedelta

from .web_manager import web_manager
from .blocking import wait
from ..data_types import (
    Channel,
    EpisodeMetadata,
    Locale,
    Stream,
    Subtitle,
    StreamType,
    StreamResponse,
    StreamResponseType,
    MovieMetadata,
)



BASE_URL = "https://kamyroll-server.herokuapp.com"

REGEXES = [
    ("crunchyroll", re.compile(r"https://beta\.crunchyroll\.com/(?:[a-z]{2,}/)?watch/(?P<id>[A-Z0-9]+)/")),
    ("funimation", re.compile(r"https://www\.funimation\.com/v/(?P<slug_show>[a-z\-]+)/(?P<slug_episode>[a-z\-]+)")),
    ("adn", re.compile(r"https://animedigitalnetwork\.fr/video/[^/]+/(?P<id>[0-9]+)-")),
]


_logger = logging.getLogger(__name__)


class ApiError(Exception):
    pass


def parse_url(url):
    for name, regexp in REGEXES:
        match = regexp.match(url)
        if not match:
            continue

        return name, match.groupdict()
    return None


def get_media(name, params, /, username=None, password=None, retries=3):
    use_login = username and password
    use_bypass = False

    params["channel_id"] = name

    if name=="adn":
        params["country"] = "fr"

    if use_login:
        params["email"] = username
        params["password"] = password
    else:
        use_bypass = True

    if retries <= 1:
        retries = 1
    data = {}
    for _ in range(retries):
        params["bypass"] = "true"
        if not use_bypass:
            del params["bypass"]

        data = call_api("/v1/streams", params=params)
        if "error" in data:
            return_val = _handle_error(data["code"], data["message"],
                use_login, name)
            if return_val is not None:
                use_bypass = return_val
            continue
        try:
            return _stream_response_from_response_dict(data)
        except Exception as error:
            message = f"Unknown error while parsing response: {error}"
            raise ApiError(message)

    _logger.error("Api call failed after too many retries")
    message = data.get("message") or "Unknown error"
    raise ApiError(message)


def call_api(path, /, params=None):
    _logger.info("Calling api endpoing %s with %s", path, params)
    url = BASE_URL + path
    data = web_manager.get(url, params=params)

    # TEMP: this checks if we have internet
    if not data:
        raise ApiError("Internet or API not available")

    json_data = {}
    try:
        json_data = json.loads(data)
    except ValueError as exception:
        _logger.error("Error decoding returned json: %s", exception)

    if "error" in json_data:
        error_code = json_data.get("code", "unknown")
        error_message = json_data.get("message", "Unknown Error")
        _logger.error("Api call returned '%s': %s", error_code, error_message)
        json_data["code"] = error_code
        json_data["message"] = error_message

    return json_data


def _handle_error(code, message, use_login, channel_id):
    _logger.error("Api returned error code %s: %s", code, message)

    match code:
        case "premium_only":
            if use_login:
                message += "\nConsider using the premium bypass"
                raise ApiError(message)

            if channel_id == "funimation":
                return False
            # this should only ever happen if
            # the api backend user runs out of premium
            raise ApiError("Unexpected bypass error, try again later")

        case "bad_player_connection":
            wait(2000)

        case "bad_initialize":
            wait(2000)

        case "unknown_id":
            raise ApiError("The provided id of the url is not valid")

        case _:
            wait(1000)
    return


def _stream_response_from_response_dict(data, /):
    try:
        response_type_str = data["type"]
        channel_id = data["channel_id"]
        stream_dicts = data["streams"]
        subtitle_dicts = data["subtitles"]
        images_dict = data["images"]
    except KeyError as error:
        message = f"Key {error} missing in response json"
        raise ApiError(message) from None

    try:
        response_type = StreamResponseType(response_type_str)
    except ValueError as error:
        message = f"Unknown stream response type: {error}"
        raise ApiError(message) from None

    try:
        channel = Channel(channel_id)
    except ValueError as error:
        message = f"Unknown channel: {error}"
        raise ApiError(message) from None

    metadata = None
    if response_type is StreamResponseType.EPISODE:
        metadata = _episode_metadata_from_response_dict(data)
    elif response_type is StreamResponseType.MOVIE:
        metadata = _movie_metadata_from_response_dict(data)
    if metadata is None:
        raise ApiError("Error parsing metadata")

    images = _pictures_from_response_dict(images_dict)

    streams: list[Stream] = []
    for stream_dict in stream_dicts:
        stream = _stream_from_response_dict(stream_dict)
        if stream is not None:
            streams.append(stream)

    subtitles = []
    for subtitle_dict in subtitle_dicts:
        subtitle = _subtitle_from_response_dict(subtitle_dict)
        if subtitle is not None:
            subtitles.append(subtitle)

    return StreamResponse(type=response_type, images=images, metadata=metadata,
        channel=channel, streams=streams, subtitles=subtitles)


def _pictures_from_response_dict(data):
    parsed_data = {}

    for name, value in data.items():
        if value:
            url = value[-1].get("source")
            if url:
                parsed_data[name] = url

    return parsed_data


def _episode_metadata_from_response_dict(data, /):
    try:
        series_meta = data["parent_metadata"]
        episode_meta = data["episode_metadata"]
        series = series_meta["title"]
        season = episode_meta["season_number"]
        season_name = episode_meta["season_title"]
        episode = episode_meta["episode_number"]
        episode_disp = episode_meta["episode"]
        title = episode_meta["title"]
        duration_ms = episode_meta["duration_ms"]
        description = episode_meta["description"]
        air_date: str = episode_meta["episode_air_date"]
    except KeyError as error:
        _logger.error("Error parsing metadata: Key %s does not exist in json", error)
        return None

    duration = timedelta(milliseconds=duration_ms)
    if air_date.endswith("Z"):
        air_date = air_date.removesuffix("Z")
    release_date = datetime.fromisoformat(air_date)

    return EpisodeMetadata(title=title, description=description,
        duration=duration, series=series,
        season=season, season_name=season_name,
        episode=episode, episode_disp=episode_disp,
        date=release_date, year=release_date.year)


def _movie_metadata_from_response_dict(data, /):
    try:
        movie_meta = data["movie_metadata"]
        title = movie_meta["title"]
        duration_ms = movie_meta["duration_ms"]
        description = movie_meta["description"]
        year = movie_meta["movie_release_year"]
    except KeyError as error:
        _logger.error("Error parsing metadata: Key %s does not exist in json", error)
        return None

    duration = timedelta(milliseconds=duration_ms)

    return MovieMetadata(title=title, description=description,
        duration=duration, year=year)


def _stream_from_response_dict(data, /):
    try:
        stream_type_str = data["type"]
        audio_locale_str = data["audio_locale"]
        hardsub_locale_str = data["hardsub_locale"]
        url = data["url"]
    except KeyError as error:
        _logger.error("Error parsing stream: Key %s does not exist in json", error)
        return None

    try:
        audio_locale = Locale(audio_locale_str)
    except ValueError as error:
        _logger.error("Error parsing stream: audio locale: %s", error)
        return None

    try:
        hardsub_locale = Locale(hardsub_locale_str)
    except ValueError as error:
        _logger.error("Error parsing stream: hardsub locale: %s", error)
        return None

    suffix = None
    try:
        stream_type = StreamType(stream_type_str)
    except ValueError as error:
        _logger.error("Error parsing stream: %s", error)
        return None

    if stream_type_str.startswith("simulcast"):
        suffix = " (Simulcast)"
        stream_type_str = stream_type_str.removeprefix("simulcast_")
    elif stream_type_str.startswith("uncut"):
        suffix = " (Uncut)"
        stream_type_str = stream_type_str.removeprefix("uncut_")

    type_name = str(stream_type)
    if suffix:
        type_name += suffix

    return Stream(type=stream_type, type_name=type_name,
        audio_locale=audio_locale, hardsub_locale=hardsub_locale, url=url)

def _subtitle_from_response_dict(data, /):
    try:
        locale_str = data["locale"]
        url = data["url"]
        sub_format = data["format"]
    except KeyError as error:
        _logger.error("Error parsing subtitle: %s", error)
        return None

    try:
        locale = Locale(locale_str)
    except ValueError as error:
        _logger.error("Error parsing subtitle: %s", error)
        return None

    return Subtitle(locale=locale, url=url, format=sub_format)
