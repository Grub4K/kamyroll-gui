import logging
import dataclasses
import tempfile

from ..utils.filename import format_name
from ..utils.web_manager import web_manager
from ..data_types.metadata import EpisodeMetadata



_logger = logging.getLogger(__name__)


def get_arguments(settings, selection, metadata, images, subtitles_only, /):
    output_path = _get_output_path(settings, metadata)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    arguments = _get_input_args(selection, subtitles_only)

    if not subtitles_only:
        image_mapping_args = []
        if settings.write_metadata:
            poster = images.get("poster_tall")
            if poster is not None:
                position = len(arguments) // 2
                image_input_args, image_mapping_args = _get_image_args(
                    poster, position, settings.separate_subtitles)
                arguments += image_input_args

        if not settings.compress_streams:
            arguments.extend(["-c:a", "copy", "-c:v", "copy"])

        if settings.write_metadata:
            arguments += _get_metadata_args(selection, metadata)

        arguments += _get_video_mapping_args(selection)
        if not settings.separate_subtitles:
            arguments += _get_subtitle_mapping_args(selection)
        if settings.write_metadata:
            arguments += image_mapping_args

        arguments.append(str(output_path))

    if settings.separate_subtitles or subtitles_only:
        subtitle_path = output_path.parent.joinpath(
            settings.subtitle_prefix, output_path.name)
        subtitle_path.parent.mkdir(parents=True, exist_ok=True)

        arguments += _get_separate_subtitle_args(selection,
            subtitle_path, subtitles_only)

    _logger.debug("Constructed ffmpeg arguments: %s", arguments)
    return arguments


def _get_output_path(settings, metadata):
    format_data = dataclasses.asdict(metadata)
    if isinstance(metadata, EpisodeMetadata):
        filename = format_name(settings.episode_format, format_data)
    else: # elif isinstance(metadata, MovieMetadata):
        filename = format_name(settings.movie_format, format_data)

    if settings.separate_subtitles:
        return settings.download_path.joinpath(filename + ".mp4")

    return settings.download_path.joinpath(filename + ".mkv")


def _get_input_args(download_selection, subtitles_only):
    input_args = []

    if not subtitles_only:
        input_args.extend(["-i", download_selection.url])
    for subtitle in download_selection.subtitles:
        input_args.extend(["-i", subtitle.url])

    return input_args


def _get_video_mapping_args(download_selection):
    mapping_args = []

    for program_id in download_selection.program_ids:
        mapping_args.extend(["-map", f"0:p:{program_id}:v?"])
        mapping_args.extend(["-map", f"0:p:{program_id}:a?"])

    hardsub_info = download_selection.hardsub_info
    if not hardsub_info.is_native:
        mapping_args.extend(['-vf', f'subtitles={hardsub_info.url}'])

    return mapping_args


def _get_subtitle_mapping_args(download_selection):
    arguments = []

    # We have one prior argument, so start from 1
    index_range = range(1, len(download_selection.subtitles)+1)
    for index in index_range:
        arguments.extend(["-map", str(index)])

    return arguments


def _get_separate_subtitle_args(download_selection, base_path, subtitles_only):
    arguments = []

    start = 0 if subtitles_only else 1
    for index, subtitle in enumerate(download_selection.subtitles, start):
        arguments.extend(["-map", str(index)])

        subtitle_language = subtitle.locale.to_iso_639_2()
        suffix = f".{subtitle_language}.ass"
        sub_output_path = base_path.with_suffix(suffix)
        arguments.append(str(sub_output_path))

    return arguments


def _get_metadata_args(download_selection, metadata, /):
    arguments = []

    audio_language = download_selection.audio_locale.to_iso_639_2()
    arguments.extend(["-metadata:s:a:0", f"language={audio_language}"])

    hardsub_language = download_selection.hardsub_info.locale.to_iso_639_2()
    if hardsub_language:
        arguments.extend(["-metadata:s:v:0", f"language={hardsub_language}"])

    for index, subtitle in enumerate(download_selection.subtitles):
        sublang = subtitle.locale.to_iso_639_2()
        arguments.extend([f"-metadata:s:s:{index}", f"language={sublang}"])

    arguments.extend([
        "-metadata", f"title={metadata.title}",
        "-metadata", f"year={metadata.year}",
        "-metadata", f"description={metadata.description}",
    ])

    if isinstance(metadata, EpisodeMetadata):
        arguments.extend([
            "-metadata", f"show={metadata.series}",
            "-metadata", f"season_number={metadata.season}",
            "-metadata", f"episode_sort={metadata.episode}",
            "-metadata", f"episode_id={metadata.episode_disp}",
            "-metadata", f"date={metadata.date}",
        ])

    return arguments

def _get_image_args(image, position, is_mp4):
    filename = _get_temp_image_file(image)
    if is_mp4:
        return ([
            "-i", filename
        ], [
            "-map", str(position),
            # "-c:v:1", "mjpeg",
            f"-disposition:v:1", "attached_pic",
        ])

    return ([
    ], [
        "-attach", filename,
        "-metadata:s:t", "mimetype=image/jpeg",
    ])

def _get_temp_image_file(image):
    data = web_manager.get(image)
    with tempfile.NamedTemporaryFile("wb", prefix="kamyroll_",
            suffix=".jpeg", delete=False) as file:
        _logger.debug("Created tempfile: %s", file.name)
        file.write(data)

    return file.name
