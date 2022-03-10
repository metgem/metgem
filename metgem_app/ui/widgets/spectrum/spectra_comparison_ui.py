# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'E:\git\metgem\metgem_app\ui\widgets\spectrum\spectra_comparison.ui',
# licensing of 'E:\git\metgem\metgem_app\ui\widgets\spectrum\spectra_comparison.ui' applies.
#
# Created: Sat Mar  5 14:43:11 2022
#      by: pyside2-uic  running on PySide2 5.13.2
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_Spectra(object):
    def setupUi(self, Spectra):
        Spectra.setObjectName("Spectra")
        Spectra.resize(400, 300)
        self.horizontalLayout = QtWidgets.QHBoxLayout(Spectra)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.splitter = QtWidgets.QSplitter(Spectra)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName("splitter")
        self.widgetSpectra = ExtendedSpectrumWidget(self.splitter)
        self.widgetSpectra.setObjectName("widgetSpectra")
        self.widgetFragmentsList = FragmentsListWidget(self.splitter)
        self.widgetFragmentsList.setObjectName("widgetFragmentsList")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.widgetFragmentsList)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.horizontalLayout.addWidget(self.splitter)

        self.retranslateUi(Spectra)
        QtCore.QMetaObject.connectSlotsByName(Spectra)

    def retranslateUi(self, Spectra):
        Spectra.setWindowTitle(QtWidgets.QApplication.translate("Spectra", "Form", None, -1))

from metgem_app.ui.widgets.spectrum import ExtendedSpectrumWidget, FragmentsListWidget
