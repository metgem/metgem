import os

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QPainter
from PyQt5.QtWidgets import QSplashScreen, QProgressBar, QLabel, qApp

from .version import FULLVERSION


class SplashScreen(QSplashScreen):
    def __init__(self):
        splash_pix = QPixmap(os.path.join(os.path.dirname(__file__), 'splash.png'))
        super().__init__(splash_pix, Qt.WindowStaysOnTopHint | Qt.SplashScreen)

        self.setMask(splash_pix.mask())
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.__message = ""
        self.__color = Qt.black
        self.__alignment = Qt.AlignBottom | Qt.AlignCenter
        self.__msgrect = self.rect().adjusted(5, 5, -5, -85)

        self.pbar = QProgressBar(self)
        self.pbar.setMaximum(100)
        self.pbar.setGeometry(100, splash_pix.height()-130, splash_pix.width()-200, 20)
        self.pbar.setAlignment(Qt.AlignCenter)
        self.pbar.setStyleSheet("""
            QProgressBar {
                border: 1px solid black;
                text-align: center;
                padding: 1px;
                border-radius: 5px;
                background: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 #fff,
                stop: 0.4999 #eee,
                stop: 0.5 #ddd,
                stop: 1 #eee );
                height: 15px;
            }

            QProgressBar::chunk {
                background: QLinearGradient( x1: 0, y1: 0, x2: 1, y2: 0,
                stop: 0 #ffadad,
                stop: 1 #ff6666);
                border-radius: 5px;
                border: 1px solid black;
            }""")

        v = f"Version: {FULLVERSION}"
        self.version = QLabel(self)
        self.version.setText(v)
        self.version.move(splash_pix.width()-self.fontMetrics().width(v)-125, splash_pix.height()-180)

    def setValue(self, value):
        self.pbar.setValue(value)

    def show(self):
        super().show()
        qApp.processEvents()

    def showMessage(self, message: str, alignment: int=Qt.AlignBottom | Qt.AlignCenter, color=Qt.black):
        self.__message = message
        self.__alignment = alignment
        self.__color = color
        self.messageChanged.emit(message)
        self.repaint()
        qApp.processEvents()

    def drawContents(self, painter: QPainter):
        painter.setPen(self.__color)
        painter.drawText(self.__msgrect, self.__alignment, self.__message)
