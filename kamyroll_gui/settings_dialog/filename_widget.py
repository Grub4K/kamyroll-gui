import logging
from dataclasses import (
    fields,
    MISSING,
)

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QGridLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QWidget,
)

from ..data_types.metadata import (
    EpisodeMetadata,
    MovieMetadata,
)



class FilenameWidget(QWidget):
    _logger = logging.getLogger(__name__).getChild(__qualname__)

    def __init__(self, settings, /):
        super().__init__()

        self.settings = settings

        layout = QGridLayout()
        layout.setAlignment(Qt.AlignTop)
        layout.setColumnStretch(0, 10)
        layout.setColumnStretch(1, 1)
        self.setLayout(layout)

        path_label = QLabel("Output directory:")
        layout.addWidget(path_label, 0, 0, 1, 2)

        self.path_edit = QLineEdit()
        self.path_edit.setReadOnly(True)
        self.path_edit.setTextMargins(5, 5, 5, 5)
        absolute_path = settings.download_path.resolve().absolute()
        self.path_edit.setText(str(absolute_path))
        layout.addWidget(self.path_edit, 1, 0)

        self.path_button = QPushButton("Browse...")
        self.path_button.clicked.connect(self.get_output_path)
        self.path_button.setStyleSheet("padding: 8px;")
        layout.addWidget(self.path_button, 1, 1)

        episode_filename_label = QLabel("Episode filename format:")
        layout.addWidget(episode_filename_label, 2, 0, 1, 2)

        self.episode_filename = QLineEdit()
        self.episode_filename.setTextMargins(5, 5, 5, 5)
        self.episode_filename.setStyleSheet("border: 1px solid black;")
        self.episode_filename.setPlaceholderText("Episode filename format")
        self.episode_filename.setText(settings.episode_format)
        self.episode_filename.editingFinished.connect(self.validate_episode)
        layout.addWidget(self.episode_filename, 3, 0, 1, 2)

        movie_filename_label = QLabel("Movie filename format:")
        layout.addWidget(movie_filename_label, 4, 0, 1, 2)

        self.movie_filename = QLineEdit()
        self.movie_filename.setTextMargins(5, 5, 5, 5)
        self.movie_filename.setPlaceholderText("Movie filename format")
        self.movie_filename.setText(settings.movie_format)
        self.episode_filename.editingFinished.connect(self.validate_movie)
        layout.addWidget(self.movie_filename, 5, 0, 1, 2)

        self.separate_subtitles_box = QCheckBox("Write separate subtitle files")
        self.separate_subtitles_box.setChecked(settings.separate_subtitles)
        self.separate_subtitles_box.stateChanged.connect(self.swap_sub_state)
        layout.addWidget(self.separate_subtitles_box, 6, 0, 1, 2)

        self.subtitle_prefix_label = QLabel("Subtitle prefix:")
        layout.addWidget(self.subtitle_prefix_label, 7, 0, 1, 2)

        self.subtitle_prefix = QLineEdit()
        self.subtitle_prefix.setTextMargins(5, 5, 5, 5)
        self.subtitle_prefix.setPlaceholderText("Subtitle prefix")
        self.subtitle_prefix.setText(settings.subtitle_prefix)
        self.subtitle_prefix.editingFinished.connect(self.set_subtitle_prefix)
        layout.addWidget(self.subtitle_prefix, 8, 0, 1, 2)

        self.swap_sub_state(settings.separate_subtitles)

    def validate_episode(self, /):
        example_data = self._default_dict_from_dataclass(EpisodeMetadata)
        self._validate_format(self.episode_filename, example_data)

    def validate_movie(self, /):
        example_data = self._default_dict_from_dataclass(MovieMetadata)
        self._validate_format(self.movie_filename, example_data)

    @staticmethod
    def _default_dict_from_dataclass(data, /):
        generated_dict = {}
        for field in fields(data):
            if field.default_factory is not MISSING:
                value = field.default_factory()
            else:
                value = field.type()
            generated_dict[field.name] = value
        return generated_dict

    def _validate_format(self, line_edit, example_data, /):
        value = line_edit.text()
        try:
            value.format(**example_data)
        except ValueError:
            self._logger.debug("Invalid format string")
            line_edit.setStyleSheet("border: 1px solid red;")
            line_edit.setToolTip("Invalid format string")
        except KeyError:
            self._logger.debug("Incorrect key used in format")
            line_edit.setStyleSheet("border: 1px solid red;")
            line_edit.setToolTip("Incorrect key used in format")
        else:
            self._logger.debug("Correct format")
            line_edit.setStyleSheet("border: 1px solid black;")
            line_edit.setToolTip("")

    def swap_sub_state(self, state, /):
        checked = bool(state)
        self.subtitle_prefix_label.setEnabled(checked)
        self.subtitle_prefix.setEnabled(checked)
        self.settings.separate_subtitles = checked

    def set_subtitle_prefix(self, /):
        self.settings.subtitle_prefix = self.subtitle_prefix.text()

    def get_output_path(self, /):
        title = "Select output path"
        base_path = str(self.settings.download_path)

        path = QFileDialog.getExistingDirectory(self, title, base_path,
            QFileDialog.ShowDirsOnly)
        if not path:
            return
        self._logger.info("Selected File: %s", path)

        download_path = Path(path)
        if download_path.is_reserved():
            QMessageBox.information(self, "Directory is reserved",
                "The directory you selected is unavailable, please select another one.")
            return

        self.settings.download_path = download_path
        self.path_edit.setText(str(download_path))

    def is_valid(self, /):
        return not (self.episode_filename.toolTip()
            or self.movie_filename.toolTip())
