import math

from PySide6.QtCore import Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QPainter,
    QPalette,
    QPen,
)
from PySide6.QtWidgets import (
    QWidget,
)



class LoadingOverlay(QWidget):
    def __init__(self, parent=None, /, dot_count=8, radius=50, interval=400):
        super().__init__(parent)
        self.dot_count = dot_count
        self.radius = radius
        self.interval = interval

        self.timer = None

        palette = self.palette()
        palette.setColor(QPalette.Base, Qt.transparent)

        self.hide()

    def paintEvent(self, event, /):
        painter = QPainter()
        painter.begin(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(event.rect(), QBrush(QColor(255, 255, 255, 127)))
        painter.setPen(QPen(Qt.NoPen))

        mid_x = self.width() / 2 - 10
        mid_y = self.height() / 2 - 10

        for step in range(self.dot_count):
            angle = 360 * step / self.dot_count - 90 + (360 / self.dot_count / 2)
            looping_offset = (self.counter - step) / self.dot_count
            should_show = 0 <= looping_offset <= 1
            if not should_show:
                continue
                # painter.setBrush(QBrush(QColor(127, 127, 127)))
            else:
                # if looping_offset > 0.5:
                #     looping_offset = 1.0 - looping_offset
                # r_color = int(127 * looping_offset + 190)
                painter.setBrush(QBrush(QColor(255, 127, 127)))
            off_x = self.radius * math.cos(math.radians(angle))
            off_y = self.radius * math.sin(math.radians(angle))
            painter.drawEllipse(int(mid_x + off_x), int(mid_y + off_y), 20, 20)

        painter.end()

    def showEvent(self, _, /):
        self.timer = self.startTimer(self.interval / self.dot_count)
        self.counter = 0.0

    def timerEvent(self, _, /):
        self.counter = (self.counter + 1) % (self.dot_count * 2)
        self.update()

    def hideEvent(self, _ , /):
        if self.timer is not None:
            self.killTimer(self.timer)
