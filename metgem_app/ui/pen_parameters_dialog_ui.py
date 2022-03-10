# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'E:\git\metgem\metgem_app\ui\pen_parameters_dialog.ui',
# licensing of 'E:\git\metgem\metgem_app\ui\pen_parameters_dialog.ui' applies.
#
# Created: Sat Mar  5 14:42:55 2022
#      by: pyside2-uic  running on PySide2 5.13.2
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(326, 300)
        self.gridLayout = QtWidgets.QGridLayout(Dialog)
        self.gridLayout.setObjectName("gridLayout")
        self.lstPenColors = QtWidgets.QListWidget(Dialog)
        self.lstPenColors.setObjectName("lstPenColors")
        self.gridLayout.addWidget(self.lstPenColors, 3, 5, 1, 1)
        self.lstPenStyles = QtWidgets.QListWidget(Dialog)
        self.lstPenStyles.setIconSize(QtCore.QSize(64, 64))
        self.lstPenStyles.setUniformItemSizes(True)
        self.lstPenStyles.setObjectName("lstPenStyles")
        self.gridLayout.addWidget(self.lstPenStyles, 3, 0, 1, 5)
        self.label_3 = QtWidgets.QLabel(Dialog)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 0, 5, 1, 1)
        self.label = QtWidgets.QLabel(Dialog)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 6, 0, 1, 6)
        self.label_2 = QtWidgets.QLabel(Dialog)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 4, 0, 1, 1)
        self.spinPenSize = QtWidgets.QSpinBox(Dialog)
        self.spinPenSize.setMinimum(8)
        self.spinPenSize.setMaximum(2048)
        self.spinPenSize.setObjectName("spinPenSize")
        self.gridLayout.addWidget(self.spinPenSize, 4, 1, 1, 3)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 4, 4, 1, 1)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem1, 4, 5, 1, 1)

        self.retranslateUi(Dialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), Dialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QtWidgets.QApplication.translate("Dialog", "Dialog", None, -1))
        self.label_3.setText(QtWidgets.QApplication.translate("Dialog", "Color", None, -1))
        self.label.setText(QtWidgets.QApplication.translate("Dialog", "Style", None, -1))
        self.label_2.setText(QtWidgets.QApplication.translate("Dialog", "Size", None, -1))

