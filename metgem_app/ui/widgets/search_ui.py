# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'E:\git\metgem\metgem_app\ui\widgets\search.ui',
# licensing of 'E:\git\metgem\metgem_app\ui\widgets\search.ui' applies.
#
# Created: Sat Mar  5 14:43:05 2022
#      by: pyside2-uic  running on PySide2 5.13.2
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(400, 40)
        self.horizontalLayout = QtWidgets.QHBoxLayout(Form)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.leSearch = QtWidgets.QLineEdit(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.leSearch.sizePolicy().hasHeightForWidth())
        self.leSearch.setSizePolicy(sizePolicy)
        self.leSearch.setMinimumSize(QtCore.QSize(300, 0))
        self.leSearch.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.leSearch.setBaseSize(QtCore.QSize(0, 0))
        self.leSearch.setObjectName("leSearch")
        self.horizontalLayout.addWidget(self.leSearch)
        self.btSearch = QtWidgets.QToolButton(Form)
        self.btSearch.setText("")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icons/images/system-search.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btSearch.setIcon(icon)
        self.btSearch.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self.btSearch.setObjectName("btSearch")
        self.horizontalLayout.addWidget(self.btSearch)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(QtWidgets.QApplication.translate("Form", "Form", None, -1))
        self.leSearch.setPlaceholderText(QtWidgets.QApplication.translate("Form", "Search", None, -1))

import ui_rc
