import os

from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QSplashScreen, QProgressBar, QLabel, qApp

from version import FULLVERSION


class SplashScreen(QSplashScreen):
    def __init__(self):
        splash_pix = QPixmap(os.path.join(os.path.dirname(__file__), 'splash.svg'))
        super().__init__(splash_pix, Qt.WindowStaysOnTopHint)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setMask(splash_pix.mask())

        self.pbar = QProgressBar(self)
        self.pbar.setMaximum(100)
        self.pbar.setGeometry(20, splash_pix.height()-50, splash_pix.width()-40, 20)
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
                background: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 #727378,
                stop: 0.4999 #727478,
                stop: 0.5 #727378,
                stop: 1 #3d404d );
                border-radius: 5px;
                border: 1px solid black;
            }""")

        v = f"Version: {FULLVERSION}"
        self.version = QLabel(self)
        self.version.setText(v)
        self.version.move(splash_pix.width()-self.fontMetrics().width(v)-40, splash_pix.height()-145)

    def setValue(self, value):
        self.pbar.setValue(value)

    def show(self):
        super().show()
        qApp.processEvents()

    def showMessage(self, message: str, alignment: int=Qt.AlignBottom | Qt.AlignCenter, color=Qt.black):
        super().showMessage(message, alignment, color)
        qApp.processEvents()

splash = SplashScreen()
splash.show()

splash.showMessage("Loading numpy library...")
import numpy
splash.setValue(5)

splash.showMessage("Loading pandas library...")
import pandas
splash.setValue(10)

splash.showMessage("Loading pyarrow library...")
import pyarrow
splash.setValue(15)

splash.showMessage("Loading igraph library...")
import igraph
splash.setValue(20)

splash.showMessage("Loading scipy library...")
import scipy
splash.setValue(25)

splash.showMessage("Loading lxml library...")
import lxml
splash.setValue(30)

splash.showMessage("Loading pyteomics library...")
import pyteomics
splash.setValue(35)

splash.showMessage("Loading sklearn library...")
import sklearn
splash.setValue(40)

splash.showMessage("Loading matplotlib library...")
import matplotlib
splash.setValue(50)

splash.showMessage("Loading Configuration module...")
import lib.config
splash.setValue(55)

splash.showMessage("Loading Errors modules...")
import lib.errors
splash.setValue(60)

splash.showMessage("Loading Logger module...")
import lib.logger
splash.setValue(65)

splash.showMessage("Loading GraphML parser module...")
import lib.graphml
splash.setValue(70)

splash.showMessage("Loading Databases module...")
import lib.database
splash.setValue(75)

splash.showMessage("Loading User interface module...")
import lib.ui
splash.setValue(90)

splash.showMessage("Loading Workers module...")
import lib.workers
splash.setValue(95)

splash.showMessage("Loading Project module...")
import lib.save
splash.setValue(100)

splash.showMessage("")
