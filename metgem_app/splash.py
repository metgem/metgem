import os

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QPainter
from PyQt5.QtWidgets import QSplashScreen, QProgressBar, QLabel, qApp


class SplashScreen(QSplashScreen):
    def __init__(self):
        self.splash_pix = QPixmap(os.path.join(os.path.dirname(__file__), 'splash.png'))
        super().__init__(self.splash_pix, Qt.WindowStaysOnTopHint | Qt.SplashScreen)

        self.setMask(self.splash_pix.mask())
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.__message = ""
        self.__color = Qt.white
        self.__alignment = Qt.AlignBottom | Qt.AlignLeft
        self.__msgrect = self.rect().adjusted(355, 5, -270, -270)

        self.pbar = QProgressBar(self)
        self.pbar.setMaximum(100)
        self.pbar.setGeometry(350, self.splash_pix.height() - 265, self.splash_pix.width() - 680, 15)
        self.pbar.setAlignment(Qt.AlignCenter)
        self.pbar.setStyleSheet("""
            QProgressBar {
                border: 1px solid black;
                text-align: center;
                font-size: 10px;
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

        self.version = QLabel(self)
        self.version.setAlignment(Qt.AlignLeft)
        self.version.setStyleSheet("""
            QLabel {
                color : white;
            }""")

    def setValue(self, value):
        self.pbar.setValue(value)

    def setVersion(self, version):
        text = f"Version {version}"
        self.version.setText(text)
        self.version.move(self.splash_pix.width() - self.fontMetrics().width(text) - 332,
                          self.splash_pix.height() - 265)
        geom = self.pbar.geometry()
        geom.setWidth(geom.width() - self.fontMetrics().width(text) - 10)
        self.pbar.setGeometry(geom)

    def show(self):
        super().show()
        qApp.processEvents()

    def showMessage(self, message: str, alignment: int = Qt.AlignBottom | Qt.AlignLeft, color=Qt.white):
        self.__message = message
        self.__alignment = alignment
        self.__color = color
        self.messageChanged.emit(message)
        self.repaint()
        qApp.processEvents()

    def drawContents(self, painter: QPainter):
        painter.setPen(self.__color)
        painter.drawText(self.__msgrect, self.__alignment, self.__message)
