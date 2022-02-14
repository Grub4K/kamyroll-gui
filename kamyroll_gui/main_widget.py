from functools import partial
import logging

from PySide6.QtCore import QTimer, Qt

from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QGridLayout,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QWidget,
    QPushButton,
)

from .settings_dialog import SettingsDialog
from .download_dialog import DownloadDialog
from .validated_url_input_dialog import ValidatedUrlInputDialog
from .settings import manager
from .utils import api
from .utils.loading_overlay import LoadingOverlay


CONFIG_UPDATE_TIME = 15 * 60 * 1000
ABOUT_TEXT = """
Kamyroll is written in Python 3 using PySide (Qt)<br>
and was developed by <a href="https://github.com/Grub4K">Grub4K</a><br>
The source is available on <a href="https://github.com/Grub4K/kamyroll-gui">GitHub</a><br><br>
It uses the Kamyroll API developed by <a href="https://github.com/hyugogirubato">hyugogirubato</a>
"""

class MainWidget(QWidget):
    _logger = logging.getLogger(__name__).getChild(__qualname__)

    def __init__(self, /):
        super().__init__()
        self.setWindowTitle('Kamyroll')
        self.setMinimumSize(700, 500)

        self.url_correct = False
        self.first_time = True

        layout = QGridLayout()
        self.setLayout(layout)
        layout.setAlignment(Qt.AlignTop)

        layout.setColumnStretch(0, 10)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(2, 1)

        for row in range(10):
            layout.setRowStretch(row, 1)

        self.list_widget = QListWidget()
        self.list_widget.setDragEnabled(True)
        self.list_widget.viewport().setAcceptDrops(True)
        self.list_widget.setDragDropMode(QAbstractItemView.InternalMove)
        self.list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.list_widget.addItem("https://beta.crunchyroll.com/de/watch/GR3VWXP96/im-luffy-the-man-whos-gonna-be-king-of-the-pirates")
        self.list_widget.itemSelectionChanged.connect(self.check_selection)
        self.list_widget.itemDoubleClicked.connect(self.edit_item)
        layout.addWidget(self.list_widget, 0, 0, 10, 1)

        self.add_item_button = QPushButton("+ Add")
        self.add_item_button.clicked.connect(self.add_item)
        layout.addWidget(self.add_item_button, 0, 1)

        self.remove_item_button = QPushButton("- Remove")
        self.remove_item_button.setDisabled(True)
        self.remove_item_button.clicked.connect(self.remove_item)
        layout.addWidget(self.remove_item_button, 0, 2)

        about_button = QPushButton("About...")
        about_function = partial(QMessageBox.about, self, "About - Kamyroll",
            ABOUT_TEXT)
        about_button.clicked.connect(about_function)
        layout.addWidget(about_button, 4, 1, 1, 2)

        about_button = QPushButton("API Info")
        about_button.clicked.connect(self.show_api_info)
        layout.addWidget(about_button, 5, 1, 1, 2)

        self.settings_button = QPushButton("Settings")
        self.settings_button.clicked.connect(self.create_settings)
        layout.addWidget(self.settings_button, 7, 1, 1, 2)

        self.download_subs_button = QPushButton("Download Subtitles")
        self.download_subs_button.clicked.connect(self.create_subtitle_download_dialog)
        layout.addWidget(self.download_subs_button, 8, 1, 1, 2)

        self.download_button = QPushButton("Download All")
        self.download_button.clicked.connect(self.create_download_dialog)
        layout.addWidget(self.download_button, 9, 1, 1, 2)

        self._set_button_states()

        self.loading_overlay = LoadingOverlay(self, dot_count=8)
        layout.setAlignment(self.loading_overlay, Qt.AlignCenter)

        QTimer.singleShot(0, self.get_config)
        self.startTimer(CONFIG_UPDATE_TIME)

    def show_api_info(self, /):
        text_data = []

        text_data.append("These services are currently available:<ul>")
        for service in api.config.services:
            if not service.active:
                continue
            text_data.append(f"<li><a href='{service.website}'>{service.name}</a></li>")
        text_data.append("</ul><br>")

        text_data.append("Api developed by:<ul>")
        for developer in api.config.developers:
            text_data.append(f"<li><a href='{developer.github}'>{developer.name}</a></li>")
        text_data.append("</ul><br>")

        text_data.append(f"<br>Api last updated {api.config.updated}")

        QMessageBox.information(self, "API Info - Kamyroll", "".join(text_data))

    def get_config(self, /):
        if self.first_time:
            self.loading_overlay.show()
        api.get_config()
        if self.first_time:
            self.first_time = False
            self.loading_overlay.hide()

    def edit_item(self, item: QListWidgetItem, /):
        dialog = ValidatedUrlInputDialog(self, item.text())
        if dialog.exec() == QDialog.Accepted:
            value = dialog.line_edit.text()
            item.setText(value)

    def check_selection(self, /):
        selection = self.list_widget.selectedIndexes()
        self.remove_item_button.setEnabled(bool(selection))

    def create_settings(self, /):
        dialog = SettingsDialog(self, manager.settings)
        if dialog.exec() == QDialog.Accepted:
            manager.settings = dialog.settings
            manager.save()

    def remove_item(self, /):
        for item in self.list_widget.selectedItems():
            row = self.list_widget.row(item)
            self.list_widget.takeItem(row)
            del item

        self._set_button_states()

    def add_item(self, /):
        dialog = ValidatedUrlInputDialog(self)
        if dialog.exec() == QDialog.Accepted:
            value = dialog.line_edit.text()
            self.list_widget.addItem(value)

        self._set_button_states()

    def create_subtitle_download_dialog(self, /):
        if not manager.settings.subtitle_locales:
            QMessageBox.information(self, "Info - Kamyroll",
                "No subtitles are selected.\nSelect subtitles in the settings and try again.")
            return
        self._real_create_download_dialog(True)

    def create_download_dialog(self, /):
        self._real_create_download_dialog(False)

    def _set_button_states(self, /):
        disable_buttons = not self.list_widget.count()
        self.download_button.setDisabled(disable_buttons)
        self.download_subs_button.setDisabled(disable_buttons)

    def _real_create_download_dialog(self, subtitle_only, /):
        items = self._get_items()
        dialog = DownloadDialog(self, items, subtitle_only=subtitle_only)
        if dialog.exec() == QDialog.Accepted:
            self._logger.info("Finished downloading sequence")
        else:
            self._logger.error("Failed download")

        items_to_remove = [
            self.list_widget.item(row)
            for row in dialog.successful_items
        ]
        self._logger.debug("Removing %s (%s)", dialog.successful_items, items_to_remove)
        for item in items_to_remove:
            row = self.list_widget.row(item)
            self.list_widget.takeItem(row)

    def _get_items(self, /):
        items = []
        for row in range(self.list_widget.count()):
            item = self.list_widget.item(row).text()
            items.append(item)
        return items

    def timerEvent(self, _, /):
        self.get_config()

    def resizeEvent(self, event, /):
        self.loading_overlay.resize(event.size())
        event.accept()
