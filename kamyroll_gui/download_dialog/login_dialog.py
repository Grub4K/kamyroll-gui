from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
)



class LoginDialog(QDialog):
    def __init__(self, parent, /):
        super().__init__(parent)
        self.setWindowTitle("Input Login data - Kamyroll")

        self.form_layout = QFormLayout()
        self.setLayout(self.form_layout)

        self.username = QLineEdit()
        self.username.setTextMargins(5, 5, 5, 5)
        self.username.setPlaceholderText("Enter E-Mail")
        self.username.textEdited.connect(self.validate)
        self.add_input_row("E-Mail", self.username)

        self.password = QLineEdit()
        self.password.setTextMargins(5, 5, 5, 5)
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setPlaceholderText("Enter Password")
        self.password.textEdited.connect(self.validate)
        self.add_input_row("Password", self.password)

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.ok_button = buttonBox.button(QDialogButtonBox.Ok)
        self.form_layout.addWidget(buttonBox)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

    def add_input_row(self, name, widget, /):
        name_label = QLabel(name)
        temp_layout = QVBoxLayout()
        temp_layout.addWidget(widget)

        self.form_layout.addRow(name_label, temp_layout)

    def validate(self, /):
        username = self.username.text()
        password = self.password.text()
        is_valid = bool(username and password)
        self.ok_button.setEnabled(is_valid)

    def get_data(self, /):
        username = self.username.text()
        password = self.password.text()
        return username, password
