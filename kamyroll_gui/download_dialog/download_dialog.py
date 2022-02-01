import logging
from dataclasses import asdict

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QMessageBox,
    QProgressBar,
    QTextEdit,
    QVBoxLayout,
)

from ..settings_dialog.settings_dialog import SettingsDialog
from ..data_types import StreamResponseType
from ..settings import manager
from ..utils import api

from .argument_helper import get_arguments
from .login_dialog import LoginDialog
from .ffmpeg import FFmpeg
from .download_selector import (
    SelectionError,
    selection_from_stream_response,
    selection_from_subtitle_list,
    subtitles_from_stream_response,
)



TOTAL_BASE_FORMAT = "Downloading {type} {index} of {total}:"
EPISODE_BASE_FORMAT = "{series} Season {season} Episode {episode_disp}"
MOVIE_BASE_FORMAT = "{title}"

class DownloadDialog(QDialog):
    _logger = logging.getLogger(__name__).getChild(__qualname__)

    def __init__(self, parent,  links, /, subtitle_only=False, strict=True):
        super().__init__(parent)
        self.setWindowTitle("Download - Kamyroll")
        self.setFixedSize(600, 400)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.credentials = {}
        self.settings = manager.settings

        self.halt_execution = False
        self.links = links
        self.length = len(links)
        self.subtitle_only = subtitle_only
        self.type_name = "subtitle" if subtitle_only else "item"
        self.position = 0
        self.is_running = False
        self.strict = strict
        self.ask_login = self.settings.use_own_credentials
        self.successful_items = []

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.progress_label = QLabel()
        layout.addWidget(self.progress_label)

        self.overall_progress = QProgressBar()
        self.overall_progress.setMaximum(len(links))
        self.overall_progress.setValue(self.position)
        layout.addWidget(self.overall_progress)

        self.ffmpeg_progress_label = QLabel()
        layout.addWidget(self.ffmpeg_progress_label)

        self.ffmpeg_progress = QProgressBar()
        self.ffmpeg_progress.setMaximum(1)
        self.ffmpeg_progress.setValue(0)
        layout.addWidget(self.ffmpeg_progress)

        self.text_edit = QTextEdit()
        text_font = QFont("Monospace")
        text_font.setStyleHint(QFont.TypeWriter)
        self.text_edit.setFont(text_font)
        self.text_edit.setReadOnly(True)
        self.text_edit.setLineWrapMode(QTextEdit.NoWrap)
        layout.addWidget(self.text_edit)

        self.ffmpeg = FFmpeg(self, self.ffmpeg_progress, self.text_edit,
            self.ffmpeg_success, self.ffmpeg_fail)
        self.is_running = True
        QTimer.singleShot(0, self.enqueue_next_download)

    def enqueue_next_download(self, /):
        if self.position >= self.length:
            return

        self.ffmpeg_progress.setValue(0)
        self.ffmpeg_progress.setMaximum(0)
        self.ffmpeg_progress_label.setText("Querying api")
        current_item = self.links[self.position]
        self.progress_label.setText(TOTAL_BASE_FORMAT.format(
            type=self.type_name, index=self.position+1, total=self.length))
        self.overall_progress.setValue(self.position)
        parsed_data = api.parse_url(current_item)
        if parsed_data is None:
            raise ValueError("Somehow the url is not a valid one")
        channel_id, params = parsed_data

        settings = self.settings

        username = None
        password = None
        if self.ask_login:
            if channel_id in self.credentials:
                username, password = self.credentials[channel_id]
            else:
                dialog = LoginDialog(self)
                if self.halt_execution:
                    return
                if dialog.exec() == QDialog.Accepted:
                    data = dialog.get_data()
                    username, password = data
                    self.credentials[channel_id] = data
                else:
                    # Disable the dialog next time
                    self.ask_login = False

        try:
            stream_response = api.get_media(channel_id, params, username, password)
        except api.ApiError as error:
            message = f"The api call failed:\n{error}"
            QMessageBox.critical(self, "Error - Kamyroll", message)
            if self.halt_execution:
                return
            QTimer.singleShot(0, self.safe_enqueue_next)
            return

        format_data = asdict(stream_response.metadata)
        if stream_response.type is StreamResponseType.EPISODE:
            info_text = EPISODE_BASE_FORMAT.format(**format_data)
        else: # elif stream_response.type is StreamResponseType.MOVIE:
            info_text = MOVIE_BASE_FORMAT.format(**format_data)

        sub_label_text = f"Downloading {info_text}:"
        self.ffmpeg_progress_label.setText(sub_label_text)

        try:
            try:
                if self.halt_execution:
                    return
                selection = self.get_selection(stream_response, settings)
            except SelectionError as error:
                dialog = SettingsDialog(self, settings, stream_response,
                    self.subtitle_only)
                if self.halt_execution:
                    return
                if dialog.exec() != QDialog.Accepted:
                    QTimer.singleShot(0, self.safe_enqueue_next)
                    return

                new_settings = dialog.settings
                if dialog.apply_to_all:
                    self.settings = new_settings
                if self.halt_execution:
                    return
                selection = self.get_selection(stream_response, new_settings)
        except Exception as error:
            self._logger.error("Error during selection: %s", error)
            QMessageBox.critical(self, "Download Error - Kamyroll", str(error))
            if self.halt_execution:
                return
            QTimer.singleShot(0, self.safe_enqueue_next)
            return

        arguments = get_arguments(settings, selection, stream_response.metadata,
            stream_response.images, self.subtitle_only)
        self.ffmpeg.start(arguments, stream_response.metadata.duration)

    def get_selection(self, stream_response, settings, /):
        if self.subtitle_only:
            selected_subtitles = subtitles_from_stream_response(
                stream_response, settings)
            selection = selection_from_subtitle_list(selected_subtitles)
        else:
            selection = selection_from_stream_response(stream_response,
                settings)
        return selection

    def ffmpeg_fail(self, /):
        self.ffmpeg.stop()
        QMessageBox.critical(self, "Error - Kamyroll", "The download failed.")
        self.safe_enqueue_next()

    def ffmpeg_success(self, /):
        self.successful_items.append(self.position)
        self.safe_enqueue_next()

    def safe_enqueue_next(self, /):
        if self.halt_execution:
            return

        self.position += 1

        if self.position < self.length:
            QTimer.singleShot(0, self.enqueue_next_download)
            return

        self.is_running = False
        self.progress_label.setText(TOTAL_BASE_FORMAT.format(
            type=self.type_name, index=self.length, total=self.length))
        self.overall_progress.setValue(self.length)
        self.ffmpeg_progress.setMaximum(1)
        self.ffmpeg_progress.setValue(1)
        if self.successful_items:
            QMessageBox.information(self, "Info - Kamyroll", "The download is finished.")
        else:
            QMessageBox.information(self, "Info - Kamyroll", "No items were downloaded.")

    def reject(self):
        if not self.is_running:
            self.halt_execution = True
            self.ffmpeg.stop()
            return super().accept()

        response = QMessageBox.question(self, "Terminate download? - Kamyroll",
            "A Download is in progress. Exiting now will terminate the download progess.\n\nAre you sure you want to quit?")
        if response == QMessageBox.Yes:
            self.ffmpeg.stop()
            return super().reject()
