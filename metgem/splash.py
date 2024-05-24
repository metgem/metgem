import os

from PySide6.QtCore import Qt, QCoreApplication, QRect
from PySide6.QtGui import QPixmap, QPainter
from PySide6.QtWidgets import QSplashScreen, QProgressBar, QLabel


class SplashScreen(QSplashScreen):
    def __init__(self):
        self.splash_pix = QPixmap(os.path.join(os.path.dirname(__file__), 'splash.png'))
        super().__init__(self.splash_pix, Qt.WindowStaysOnTopHint | Qt.SplashScreen)

        self.__message = ""
        self.__color = Qt.black
        self.__alignment = Qt.AlignBottom | Qt.AlignLeft
        self.__msgrect = QRect(25, self.rect().height() - 60, self.rect().width() - 50, 15)

        self.pbar = QProgressBar(self)
        self.pbar.setMaximum(100)
        self.pbar.setGeometry(20, self.rect().height() - 40, self.rect().width() - 40, 15)
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
                stop: 0 #ffffff,
                stop: 1 #9a9a9a);
                border-radius: 5px;
                border: 1px solid black;
            }""")

        self.version = QLabel(self)
        self.version.setGeometry(25, self.rect().height() - 60, self.rect().width() - 50, 15)
        self.version.setAlignment(Qt.AlignRight)
        self.version.setStyleSheet("""
            QLabel {
                color : black;
            }""")

    def setValue(self, value):
        self.pbar.setValue(value)

    def setVersion(self, version):
        text = f"Version {version}"
        self.version.setText(text)

    def show(self):
        super().show()
        QCoreApplication.processEvents()

    def showMessage(self, message: str, alignment: int = Qt.AlignBottom | Qt.AlignLeft, color=Qt.black):
        self.__message = message
        self.__alignment = alignment
        self.__color = color
        self.messageChanged.emit(message)
        self.repaint()
        QCoreApplication.processEvents()

    def drawContents(self, painter: QPainter):
        painter.setPen(self.__color)
        painter.drawText(self.__msgrect, self.__alignment, self.__message)
