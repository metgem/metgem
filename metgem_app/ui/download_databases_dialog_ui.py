# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'E:\git\metgem\metgem_app\ui\download_databases_dialog.ui',
# licensing of 'E:\git\metgem\metgem_app\ui\download_databases_dialog.ui' applies.
#
# Created: Sat Mar  5 14:42:51 2022
#      by: pyside2-uic  running on PySide2 5.13.2
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        Dialog.resize(472, 529)
        Dialog.setModal(True)
        self.verticalLayout = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.btSelectAll = QtWidgets.QToolButton(Dialog)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icons/images/select-all.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btSelectAll.setIcon(icon)
        self.btSelectAll.setObjectName("btSelectAll")
        self.horizontalLayout.addWidget(self.btSelectAll)
        self.btSelectNone = QtWidgets.QToolButton(Dialog)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/icons/images/select-none.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btSelectNone.setIcon(icon1)
        self.btSelectNone.setObjectName("btSelectNone")
        self.horizontalLayout.addWidget(self.btSelectNone)
        self.btSelectInvert = QtWidgets.QToolButton(Dialog)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/icons/images/select-invert.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btSelectInvert.setIcon(icon2)
        self.btSelectInvert.setObjectName("btSelectInvert")
        self.horizontalLayout.addWidget(self.btSelectInvert)
        self.frame = QtWidgets.QFrame(Dialog)
        self.frame.setFrameShape(QtWidgets.QFrame.VLine)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame.setObjectName("frame")
        self.horizontalLayout.addWidget(self.frame)
        self.btRefresh = QtWidgets.QToolButton(Dialog)
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap(":/icons/images/refresh.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btRefresh.setIcon(icon3)
        self.btRefresh.setObjectName("btRefresh")
        self.horizontalLayout.addWidget(self.btRefresh)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.treeDatabases = LoadingTreeWidget(Dialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(4)
        sizePolicy.setHeightForWidth(self.treeDatabases.sizePolicy().hasHeightForWidth())
        self.treeDatabases.setSizePolicy(sizePolicy)
        self.treeDatabases.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.treeDatabases.setProperty("showDropIndicator", False)
        self.treeDatabases.setAlternatingRowColors(True)
        self.treeDatabases.setHeaderHidden(True)
        self.treeDatabases.setObjectName("treeDatabases")
        self.treeDatabases.headerItem().setText(0, "1")
        self.verticalLayout.addWidget(self.treeDatabases)
        self.scrollArea = QtWidgets.QScrollArea(Dialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.scrollArea.sizePolicy().hasHeightForWidth())
        self.scrollArea.setSizePolicy(sizePolicy)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 456, 83))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.labelDesc = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.labelDesc.sizePolicy().hasHeightForWidth())
        self.labelDesc.setSizePolicy(sizePolicy)
        self.labelDesc.setText("")
        self.labelDesc.setTextFormat(QtCore.Qt.RichText)
        self.labelDesc.setWordWrap(True)
        self.labelDesc.setOpenExternalLinks(True)
        self.labelDesc.setObjectName("labelDesc")
        self.verticalLayout_2.addWidget(self.labelDesc)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.verticalLayout.addWidget(self.scrollArea)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Close)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(Dialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), Dialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QtWidgets.QApplication.translate("Dialog", "Download databases", None, -1))
        self.btSelectAll.setToolTip(QtWidgets.QApplication.translate("Dialog", "Select all items", None, -1))
        self.btSelectAll.setText(QtWidgets.QApplication.translate("Dialog", "Select &all", None, -1))
        self.btSelectNone.setToolTip(QtWidgets.QApplication.translate("Dialog", "Select nothing", None, -1))
        self.btSelectNone.setText(QtWidgets.QApplication.translate("Dialog", "Select &none", None, -1))
        self.btSelectInvert.setToolTip(QtWidgets.QApplication.translate("Dialog", "Invert selection", None, -1))
        self.btSelectInvert.setText(QtWidgets.QApplication.translate("Dialog", "&Invert selection", None, -1))
        self.btRefresh.setToolTip(QtWidgets.QApplication.translate("Dialog", "Refresh list", None, -1))
        self.btRefresh.setText(QtWidgets.QApplication.translate("Dialog", "...", None, -1))

from metgem_app.ui.widgets import LoadingTreeWidget
import ui_rc
