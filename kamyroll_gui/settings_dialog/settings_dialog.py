import logging
from dataclasses import replace

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QMessageBox,
    QPushButton,
    QGridLayout,
    QVBoxLayout,
    QWidget,
)

from kamyroll_gui.settings import Settings
from ..data_types import StreamResponse

from .subtitle_widget import SubtitleWidget
from .video_widget import VideoWidget
from .filename_widget import FilenameWidget



class SettingsDialog(QDialog):
    _logger = logging.getLogger(__name__).getChild(__qualname__)

    def __init__(self, parent, settings: Settings, /, stream_response: StreamResponse = None,
            subtitle_only=False):
        super().__init__(parent)
        self.setWindowTitle("Settings - Kamyroll")

        self.stream_response = stream_response
        self.is_constrained = stream_response is not None
        self.apply_to_all = False

        # copy data, we dont want to affect actual preference until apply
        self.settings = replace(settings)

        self.main_layout = QGridLayout()
        self.main_layout.setColumnStretch(0, 2)
        self.main_layout.setColumnStretch(1, 1)
        self.setLayout(self.main_layout)

        if not self.is_constrained:
            self.filename_widget = FilenameWidget(self.settings)
            self.main_layout.addWidget(self.filename_widget, 0, 0, 1, 2)

        boxes_width = 2 if subtitle_only else 1
        self.subtitle_widget = SubtitleWidget(self.settings, stream_response)
        self.main_layout.addWidget(self.subtitle_widget, 1, 0, 2, boxes_width)

        if not subtitle_only:
            self.video_widget = VideoWidget(self.settings, stream_response)
            self.main_layout.addWidget(self.video_widget, 1, 1)

        if not self.is_constrained:
            self._create_checkboxes()

        self.apply_button = QPushButton("Apply")
        self.apply_button.clicked.connect(self.apply)
        self.main_layout.addWidget(self.apply_button, 3, 1)

        if self.is_constrained:
            self.apply_all_button = QPushButton("Apply to all")
            self.apply_all_button.clicked.connect(self.apply_all)
            self.main_layout.addWidget(self.apply_all_button, 4, 1)

    def _check_valid(self, /):
        if self.stream_response is None:
            if not self.filename_widget.is_valid():
                QMessageBox.warning(self, "Invalid filename format - Kamyroll",
                    "The filename format provided is invalid. " +
                    "Please provide a valid filename format. " +
                    "For more infos read the help on formatting the filename.",
                    QMessageBox.Ok)
                return False
        return True

    def apply(self, /):
        if not self._check_valid():
            return
        self.accept()

    def apply_all(self, /):
        if not self._check_valid():
            return
        self.apply_to_all = True
        self.accept()

    def _create_checkboxes(self, /):
        _checkbox_widget = QWidget()
        self.main_layout.addWidget(_checkbox_widget, 2, 1)

        _checkbox_layout = QVBoxLayout()
        _checkbox_widget.setLayout(_checkbox_layout)

        self.write_metadata = QCheckBox("Write Metadata")
        self.write_metadata.setToolTip("Write metadata like title and series into the file")
        self.write_metadata.stateChanged.connect(self.update_metadata)
        self.write_metadata.setChecked(self.settings.write_metadata)
        _checkbox_layout.addWidget(self.write_metadata)

        self.compress_streams = QCheckBox("Compress streams")
        self.compress_streams.setToolTip("Reencode the video and audio stream with the ffmpeg defaults")
        self.compress_streams.stateChanged.connect(self.update_compress_streams)
        self.compress_streams.setChecked(self.settings.compress_streams)
        _checkbox_layout.addWidget(self.compress_streams)

        self.use_own_credentials = QCheckBox("Use own login credentials")
        self.use_own_credentials.setToolTip("Force the use of self provided login credentials")
        self.use_own_credentials.stateChanged.connect(self.update_use_own_credentials)
        self.use_own_credentials.setChecked(self.settings.use_own_credentials)
        _checkbox_layout.addWidget(self.use_own_credentials)

        self.use_strict_matching_box = QCheckBox("Use strict matching")
        self.use_strict_matching_box.setToolTip("Fail if the desired resolution or subtitles are not available")
        self.use_strict_matching_box.stateChanged.connect(self.update_strict_matching)
        self.use_strict_matching_box.setChecked(self.settings.strict_matching)
        _checkbox_layout.addWidget(self.use_strict_matching_box)

    def update_metadata(self, state, /):
        self.settings.write_metadata = bool(state)

    def update_compress_streams(self, state, /):
        self.settings.compress_streams = bool(state)

    def update_use_own_credentials(self, state, /):
        self.settings.use_own_credentials = bool(state)

    def update_strict_matching(self, state, /):
        self.settings.strict_matching = bool(state)
