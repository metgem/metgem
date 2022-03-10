# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'E:\git\metgem\metgem_app\ui\query_databases_dialog.ui',
# licensing of 'E:\git\metgem\metgem_app\ui\query_databases_dialog.ui' applies.
#
# Created: Sat Mar  5 14:42:57 2022
#      by: pyside2-uic  running on PySide2 5.13.2
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        Dialog.resize(210, 350)
        self.verticalLayout = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.btSelectAll = QtWidgets.QToolButton(Dialog)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icons/images/select-all.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btSelectAll.setIcon(icon)
        self.btSelectAll.setObjectName("btSelectAll")
        self.horizontalLayout_2.addWidget(self.btSelectAll)
        self.btSelectNone = QtWidgets.QToolButton(Dialog)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/icons/images/select-none.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btSelectNone.setIcon(icon1)
        self.btSelectNone.setObjectName("btSelectNone")
        self.horizontalLayout_2.addWidget(self.btSelectNone)
        self.btSelectInvert = QtWidgets.QToolButton(Dialog)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/icons/images/select-invert.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btSelectInvert.setIcon(icon2)
        self.btSelectInvert.setObjectName("btSelectInvert")
        self.horizontalLayout_2.addWidget(self.btSelectInvert)
        self.frame = QtWidgets.QFrame(Dialog)
        self.frame.setFrameShape(QtWidgets.QFrame.VLine)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame.setObjectName("frame")
        self.horizontalLayout_2.addWidget(self.frame)
        self.btSaveSelection = QtWidgets.QToolButton(Dialog)
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap(":/icons/images/document-save.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btSaveSelection.setIcon(icon3)
        self.btSaveSelection.setObjectName("btSaveSelection")
        self.horizontalLayout_2.addWidget(self.btSaveSelection)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem1)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.groupBox = QtWidgets.QGroupBox(Dialog)
        self.groupBox.setFlat(True)
        self.groupBox.setObjectName("groupBox")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.groupBox)
        self.horizontalLayout.setContentsMargins(0, -1, 0, -1)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.lstDatabases = QtWidgets.QListWidget(self.groupBox)
        self.lstDatabases.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.lstDatabases.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.lstDatabases.setTabKeyNavigation(True)
        self.lstDatabases.setProperty("showDropIndicator", False)
        self.lstDatabases.setAlternatingRowColors(True)
        self.lstDatabases.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        self.lstDatabases.setObjectName("lstDatabases")
        self.horizontalLayout.addWidget(self.lstDatabases)
        self.verticalLayout.addWidget(self.groupBox)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(Dialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), Dialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QtWidgets.QApplication.translate("Dialog", "Query databases", None, -1))
        self.btSelectAll.setToolTip(QtWidgets.QApplication.translate("Dialog", "Select all items", None, -1))
        self.btSelectAll.setText(QtWidgets.QApplication.translate("Dialog", "Select &all", None, -1))
        self.btSelectNone.setToolTip(QtWidgets.QApplication.translate("Dialog", "Select nothing", None, -1))
        self.btSelectNone.setText(QtWidgets.QApplication.translate("Dialog", "Select &none", None, -1))
        self.btSelectInvert.setToolTip(QtWidgets.QApplication.translate("Dialog", "Invert selection", None, -1))
        self.btSelectInvert.setText(QtWidgets.QApplication.translate("Dialog", "&Invert selection", None, -1))
        self.btSaveSelection.setText(QtWidgets.QApplication.translate("Dialog", "Save selection", None, -1))
        self.groupBox.setTitle(QtWidgets.QApplication.translate("Dialog", "Databases", None, -1))

import ui_rc
