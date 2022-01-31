import logging

from dataclasses import dataclass

from ..utils import m3u8
from ..utils.web_manager import web_manager
from ..data_types import (
    Locale,
    Subtitle,
)



_logger = logging.getLogger(__name__)


@dataclass
class HardsubInfo:
    is_native: bool
    locale: Locale
    url: str


@dataclass
class DownloadSelection:
    url: str
    audio_locale: Locale
    program_ids: list[int]
    hardsub_info: HardsubInfo
    subtitles: list[Subtitle]


class SelectionError(Exception):
    pass


def selection_from_stream_response(stream_response, settings):
    # Match on subtitle settings
    selected_subtitles = subtitles_from_stream_response(
        stream_response, settings)

    # match on video settings
    audio_matching_streams = [
        stream
        for stream in stream_response.streams
        if stream.audio_locale == settings.audio_locale
    ]
    if not audio_matching_streams:
        raise SelectionError("Could not find matching audio locale")

    matching_streams = [
        stream
        for stream in audio_matching_streams
        if stream.hardsub_locale == settings.hardsub_locale
    ]

    if matching_streams:
        hardsub_is_native = True
        hardsub_url = ""
    else:
        # We can bake softsubs in as a replacement for native hardsubs
        hardsub_is_native = False
        matching_streams = [
            stream
            for stream in audio_matching_streams
            if stream.hardsub_locale == Locale.NONE
        ]
        matching_subtitles = [
            subtitle
            for subtitle in stream_response.subtitles
            if subtitle.locale == settings.hardsub_locale
        ]
        if not bool(matching_streams) or not bool(matching_subtitles):
            raise SelectionError("Could not find matching hardsub locale")

        hardsub_url = matching_subtitles[0].url

    hardsub_info = HardsubInfo(is_native=hardsub_is_native,
        locale=settings.hardsub_locale, url=hardsub_url)

    # Get program ids to select the correct resolution
    program_url = matching_streams[0].url
    data = web_manager.get(program_url).decode()
    resolutions = m3u8.get_resolutions(data)
    if settings.video_height in resolutions:
        program_ids = resolutions[settings.video_height]
    else:
        if settings.strict_matching:
            raise SelectionError("Desired resolution not available")
        suitable_resolutions = [
            resolution
            for resolution in sorted(resolutions, reverse=True)
            if resolution <= settings.video_height
        ]
        if not suitable_resolutions:
            raise SelectionError("Desired resolution or smaller not available")
        program_ids = resolutions[suitable_resolutions[0]]

    return DownloadSelection(url=program_url,
        audio_locale=settings.audio_locale, hardsub_info=hardsub_info,
        subtitles=selected_subtitles, program_ids=program_ids)


def subtitles_from_stream_response(stream_response, settings):
    desired_subtitles = set(settings.subtitle_locales)

    selected_subtitles = []
    for subtitle in stream_response.subtitles:
        # Take only the first subtitle of a matching locale
        if subtitle.locale in desired_subtitles:
            selected_subtitles.append(subtitle)
            desired_subtitles.remove(subtitle.locale)

    if desired_subtitles:
        missing_locale_names = ", ".join(map(str, desired_subtitles))
        message = f"Missing subtitle locale(s): {missing_locale_names}"
        if settings.strict_matching:
            raise SelectionError(message)

        _logger.warning(message)

    return selected_subtitles


def selection_from_subtitle_list(subtitles):
    hardsub_info = HardsubInfo(is_native=True, locale=Locale.NONE, url="")
    return DownloadSelection(url="", audio_locale=Locale.NONE,
        hardsub_info=hardsub_info, program_ids=[], subtitles=subtitles)
