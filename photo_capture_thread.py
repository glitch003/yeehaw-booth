from PyQt6.QtCore import QThread, pyqtSignal

class PhotoCaptureThread(QThread):
    finished = pyqtSignal(list)

    def __init__(self, frames):
        super().__init__()
        self.frames = frames

    def run(self):
        self.finished.emit(self.frames) 