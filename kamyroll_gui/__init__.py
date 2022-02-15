def main():
    import logging
    import sys

    from pathlib import Path
    from datetime import datetime

    from PySide6.QtGui import QIcon
    from PySide6 import __version__ as pyside_version
    from PySide6.QtCore import __version__ as qt_version
    from PySide6.QtWidgets import QApplication

    from kamyroll_gui.main_widget import MainWidget



    filename = datetime.now().strftime("logs/kamyroll_%Y-%m-%d_%H-%M-%S.log")
    logfile = Path(filename)
    logfile.parent.mkdir(exist_ok=True)

    logging.basicConfig(level=logging.DEBUG, style='{',
        format='{asctime} | {name:<90} | {levelname:<8} | {message}',
        filename=str(logfile), filemode='w')

    logger = logging.getLogger(__name__)

    logger.info("Python version: %s", sys.version)
    logger.info("PySide version: %s (Qt v%s)", pyside_version, qt_version)

    app = QApplication([])
    app_icon = QIcon()
    app_icon.addFile("favicon.ico")
    app.setWindowIcon(app_icon)

    widget = MainWidget()
    widget.show()
    sys.exit(app.exec())
