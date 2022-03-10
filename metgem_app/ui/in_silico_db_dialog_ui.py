# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'E:\git\metgem\metgem_app\ui\in_silico_db_dialog.ui',
# licensing of 'E:\git\metgem\metgem_app\ui\in_silico_db_dialog.ui' applies.
#
# Created: Sat Mar  5 14:42:54 2022
#      by: pyside2-uic  running on PySide2 5.13.2
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_InSilicoDBDialog(object):
    def setupUi(self, InSilicoDBDialog):
        InSilicoDBDialog.setObjectName("InSilicoDBDialog")
        InSilicoDBDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        InSilicoDBDialog.resize(1018, 520)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icons/images/main.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        InSilicoDBDialog.setWindowIcon(icon)
        self.verticalLayout = QtWidgets.QVBoxLayout(InSilicoDBDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.browser = QWebEngineView(InSilicoDBDialog)
        self.browser.setObjectName("browser")
        self.verticalLayout.addWidget(self.browser)
        self.buttonBox = QtWidgets.QDialogButtonBox(InSilicoDBDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(InSilicoDBDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), InSilicoDBDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), InSilicoDBDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(InSilicoDBDialog)

    def retranslateUi(self, InSilicoDBDialog):
        InSilicoDBDialog.setWindowTitle(QtWidgets.QApplication.translate("InSilicoDBDialog", "In Silico Databases", None, -1))

from PySide2.QtWebEngineWidgets import QWebEngineView
import ui_rc
