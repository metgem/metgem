from PyQt5.QtGui import QMouseEvent, QShowEvent
from PyQt5.QtWidgets import QSlider


class Slider(QSlider):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._default_value = self.minimum() + round((self.maximum() - self.minimum()) / 2)

    def resetValue(self):
        self.setValue(self._default_value)

    def defaultValue(self):
        return self._default_value

    def showEvent(self, avent: QShowEvent):
        self._default_value = self.minimum() + round((self.maximum() - self.minimum())/2)
        self.resetValue()

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        self.resetValue()
