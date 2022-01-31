from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QLineEdit,
    QVBoxLayout,
)

from .utils import api


class ValidatedUrlInputDialog(QDialog):
    def __init__(self, /, parent=None, text=None):
        super().__init__(parent)
        self.setWindowTitle("URL Input - Kamyroll")
        self.setMinimumWidth(400)

        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QLabel("Enter a valid url:"))

        text = text or ""
        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText("URL")
        self.line_edit.textEdited.connect(self.validate)
        self.line_edit.setText(text)
        layout.addWidget(self.line_edit)

        self.validity_label = QLabel(" ")
        layout.addWidget(self.validity_label)

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.ok_button = buttonBox.button(QDialogButtonBox.Ok)
        self.validate(text)
        layout.addWidget(buttonBox)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)


    def validate(self, url, /):
        if not url:
            self.validity_label.setText(" ")
            self.ok_button.setDisabled(True)
            return

        result = api.parse_url(url)
        if not result:
            self.ok_button.setDisabled(True)
            self.validity_label.setStyleSheet("color: red;")
            self.validity_label.setText(" Not a valid URL")
            return

        self.ok_button.setEnabled(True)
        self.name, self.params = result

        self.validity_label.setStyleSheet("color: green;")
        self.validity_label.setText(f" Valid URL for {self.name}")

    def get_text(self, /):
        if self.line_edit.hasAcceptableInput():
            return self.line_edit.text()
