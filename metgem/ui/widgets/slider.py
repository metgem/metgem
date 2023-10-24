from PySide6.QtGui import QMouseEvent, QShowEvent
from PySide6.QtWidgets import QSlider


class Slider(QSlider):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._default_value = self.minimum() + round((self.maximum() - self.minimum()) / 10)

    def resetValue(self):
        self.setValue(self._default_value)

    def defaultValue(self):
        return self._default_value

    def showEvent(self, event: QShowEvent):
        self._default_value = self.minimum() + round((self.maximum() - self.minimum()) / 10)
        self.resetValue()

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        self.resetValue()
