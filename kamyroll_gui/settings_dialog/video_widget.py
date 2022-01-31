from functools import lru_cache
import logging

from PySide6.QtCore import Qt

from PySide6.QtWidgets import (
    QVBoxLayout,
    QComboBox,
    QWidget,
    QLabel,
)

from kamyroll_gui.data_types.stream_response import StreamResponse
from kamyroll_gui.settings import Settings

from ..utils import m3u8
from ..utils.web_manager import web_manager
from ..data_types import (
    Locale,
    Resolution,
)



class VideoWidget(QWidget):
    _logger = logging.getLogger(__name__).getChild(__qualname__)

    def __init__(self, settings: Settings, stream_response: StreamResponse = None, /):
        super().__init__()

        self.settings = settings
        self.stream_response = stream_response

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        self.setLayout(layout)



        self.audio_locale = QComboBox()
        for locale in self.get_audio_locales():
            if locale in [Locale.NONE, Locale.UNDEFINED]:
                continue
            self.audio_locale.addItem(str(locale), locale)

        audio_locale_label = QLabel("Audio language:")
        audio_locale_label.setBuddy(self.audio_locale)
        layout.addWidget(audio_locale_label)
        layout.addWidget(self.audio_locale)

        self.hardsub_locale = QComboBox()
        for locale in self.get_hardsub_locales():
            if locale is Locale.UNDEFINED:
                continue
            self.hardsub_locale.addItem(str(locale), locale)

        hardsub_language_label = QLabel("Hardsub language:")
        hardsub_language_label.setBuddy(self.hardsub_locale)
        layout.addWidget(hardsub_language_label)
        layout.addWidget(self.hardsub_locale)

        self.video_height = QComboBox()
        for resolution in Resolution:
            self.video_height.addItem(f"{resolution}p", resolution)
        self.video_width_label = QLabel("Maximum Resolution:")
        self.video_width_label.setBuddy(self.video_height)
        layout.addWidget(self.video_width_label)
        layout.addWidget(self.video_height)

        selected_audio_index = self.audio_locale.findData(settings.audio_locale)
        self.audio_locale.setCurrentIndex(selected_audio_index)
        selected_hardsub_index = self.hardsub_locale.findData(settings.hardsub_locale)
        self.hardsub_locale.setCurrentIndex(selected_hardsub_index)
        selected_resolution_index = self.video_height.findData(settings.video_height)
        self.video_height.setCurrentIndex(selected_resolution_index)

        self.set_audio_locale()
        self.set_hardsub_locale()
        self.set_video_height()

        self.audio_locale.currentIndexChanged.connect(self.set_audio_locale)
        self.hardsub_locale.currentIndexChanged.connect(self.set_hardsub_locale)
        self.video_height.currentIndexChanged.connect(self.set_video_height)

    def get_audio_locales(self, /):
        if self.stream_response is None:
            return Locale
        audio_locales = set()
        for stream in self.stream_response.streams:
            audio_locales.add(stream.audio_locale)
        return list(audio_locales)

    def get_hardsub_locales(self, /):
        if self.stream_response is None:
            return Locale

        selected_audio_locale = self.audio_locale.currentData()
        hardsub_locales = set()
        for stream in self.stream_response.streams:
            if stream.audio_locale != selected_audio_locale:
                continue
            hardsub_locales.add(stream.hardsub_locale)
        # Add bakeable hardsubs
        if Locale.NONE in hardsub_locales:
            for subtitle in self.stream_response.subtitles:
                hardsub_locales.add(subtitle.locale)
        return list(hardsub_locales)

    def set_audio_locale(self, /):
        self.settings.audio_locale = self.audio_locale.currentData()
        if self.stream_response is None:
            return

        self.hardsub_locale.clear()
        for locale in self.get_hardsub_locales():
            if locale == Locale.UNDEFINED:
                continue
            self.hardsub_locale.addItem(str(locale), locale)
        selected_hardsub_index = self.hardsub_locale.findData(
            self.settings.hardsub_locale)
        if selected_hardsub_index != -1:
            self.hardsub_locale.setCurrentIndex(selected_hardsub_index)
        else:
            self.hardsub_locale.setCurrentIndex(0)

    def set_hardsub_locale(self, /):
        selected_hardsub_locale = self.hardsub_locale.currentData()
        self.settings.hardsub_locale = selected_hardsub_locale
        if self.stream_response is None:
            return

        selected_audio_locale = self.audio_locale.currentData()

        suitable_streams = set()
        for stream in self.stream_response.streams:
            if stream.audio_locale != selected_audio_locale:
                continue
            if stream.hardsub_locale != selected_hardsub_locale:
                continue

            suitable_streams.add(stream.url)

        if not suitable_streams:
            # We need baked subs, use Locale.NONE
            for stream in self.stream_response.streams:
                if stream.audio_locale != selected_audio_locale:
                    continue
                if stream.hardsub_locale != Locale.NONE:
                    continue

                suitable_streams.add(stream.url)

        all_resolutions = set()
        for url in suitable_streams:
            resolutions = self._get_resolutions(url)
            all_resolutions.update(resolutions)

        current_width = self.video_height.currentData()
        self.video_height.clear()
        for resolution in all_resolutions:
            self.video_height.addItem(f"{resolution}p", resolution)
        current_width_index = self.video_height.findData(current_width)
        self._logger.debug("Using resolution index %s, current_width is %s",
            repr(current_width_index), current_width)
        if current_width_index != -1:
            self.video_height.setCurrentIndex(current_width_index)
        else:
            self._logger.debug("Set currnt index to 0")
            self.video_height.setCurrentIndex(0)

    def set_video_height(self, /):
        self.settings.video_height = self.video_height.currentData()

    @lru_cache
    def _get_resolutions(self, url, /):
        data = web_manager.get(url).decode()
        resolutions = m3u8.get_resolutions(data)
        return list(resolutions)
