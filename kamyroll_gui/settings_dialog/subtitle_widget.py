import logging
from functools import partial

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QGridLayout,
    QLabel,
    QPushButton,
    QWidget,
)

from kamyroll_gui.data_types.stream_response import StreamResponse
from kamyroll_gui.settings import Settings

from ..data_types import Locale



class SubtitleWidget(QWidget):
    _logger = logging.getLogger(__name__).getChild(__qualname__)

    def __init__(self, settings: Settings, stream_response: StreamResponse = None, /):
        super().__init__()

        self.settings = settings
        self.check_boxes = []

        self.selected = set()

        layout = QGridLayout()
        layout.setAlignment(Qt.AlignTop)
        self.setLayout(layout)
        self.setHidden(False)

        subtitle_language_label = QLabel("Subtitle languages:")
        layout.addWidget(subtitle_language_label, 0, 0, 1, 2)

        select_all_button = QPushButton("Select all")
        select_all_button.clicked.connect(lambda: self.set_all_state(True))
        layout.addWidget(select_all_button, 1, 0)

        select_all_button = QPushButton("Deselect all")
        select_all_button.clicked.connect(lambda: self.set_all_state(False))
        layout.addWidget(select_all_button, 1, 1)

        index = 0
        total_rows = (len(Locale) // 2) - 1
        enabled_locale = self.settings.subtitle_locales

        if stream_response is not None:
            self.settings.subtitle_locales = []

        for locale in Locale:
            if locale in [Locale.NONE, Locale.UNDEFINED]:
                continue

            column, row = divmod(index, total_rows)
            index += 1

            check_box = QCheckBox(str(locale))

            if stream_response is not None:
                self._logger.debug("Stream response subs: %s in %s",
                    locale, stream_response.subtitles)
                # FIXME: Dirty fix for checking locale
                response_locales = {subtitle.locale for subtitle in stream_response.subtitles}
                if locale in response_locales:
                    if locale in enabled_locale:
                        check_box.setChecked(True)
                        self.settings.subtitle_locales.append(locale)
                    check_box.setEnabled(True)
                else:
                    check_box.setEnabled(False)
            else:
                if locale in enabled_locale:
                    check_box.setChecked(True)
                check_box.setEnabled(True)

            check_box.stateChanged.connect(partial(self.select_subtitle, locale))

            self.check_boxes.append(check_box)
            layout.addWidget(check_box, row+2, column)

    def select_subtitle(self, locale, state, /):
        selected = bool(state)
        subtitle_locales = self.settings.subtitle_locales

        if selected and locale not in subtitle_locales:
            subtitle_locales.append(locale)

        elif locale in subtitle_locales:
            subtitle_locales.remove(locale)

    def set_all_state(self, state, /):
        for check_box in self.check_boxes:
            if check_box.isEnabled():
                check_box.setChecked(state)
