from PySide6.QtCore import (
    QEventLoop,
    QTimer,
)



def wait(milliseconds, /):
    timer = QTimer()
    timer.start(milliseconds)
    wait_for_event(timer.timeout)

def wait_for_event(event, /):
    loop = QEventLoop()
    event.connect(loop.quit)
    loop.exec()
