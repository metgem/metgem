# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'E:\git\metgem\metgem_app\ui\import_user_database_dialog.ui',
# licensing of 'E:\git\metgem\metgem_app\ui\import_user_database_dialog.ui' applies.
#
# Created: Sat Mar  5 14:42:53 2022
#      by: pyside2-uic  running on PySide2 5.13.2
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_ImportUserDatabaseDialog(object):
    def setupUi(self, ImportUserDatabaseDialog):
        ImportUserDatabaseDialog.setObjectName("ImportUserDatabaseDialog")
        ImportUserDatabaseDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        ImportUserDatabaseDialog.resize(319, 163)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icons/images/main.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        ImportUserDatabaseDialog.setWindowIcon(icon)
        self.verticalLayout = QtWidgets.QVBoxLayout(ImportUserDatabaseDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.groupBox = QtWidgets.QGroupBox(ImportUserDatabaseDialog)
        self.groupBox.setFlat(True)
        self.groupBox.setObjectName("groupBox")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.groupBox)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.editInputFile = QtWidgets.QLineEdit(self.groupBox)
        self.editInputFile.setMinimumSize(QtCore.QSize(200, 0))
        self.editInputFile.setObjectName("editInputFile")
        self.horizontalLayout.addWidget(self.editInputFile)
        self.btBrowseInputFile = QtWidgets.QPushButton(self.groupBox)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/icons/images/folder-open.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btBrowseInputFile.setIcon(icon1)
        self.btBrowseInputFile.setObjectName("btBrowseInputFile")
        self.horizontalLayout.addWidget(self.btBrowseInputFile)
        self.verticalLayout.addWidget(self.groupBox)
        self.groupBox_2 = QtWidgets.QGroupBox(ImportUserDatabaseDialog)
        self.groupBox_2.setFlat(True)
        self.groupBox_2.setObjectName("groupBox_2")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.groupBox_2)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.editDatabaseName = QtWidgets.QLineEdit(self.groupBox_2)
        self.editDatabaseName.setMaxLength(128)
        self.editDatabaseName.setObjectName("editDatabaseName")
        self.horizontalLayout_2.addWidget(self.editDatabaseName)
        self.verticalLayout.addWidget(self.groupBox_2)
        self.buttonBox = QtWidgets.QDialogButtonBox(ImportUserDatabaseDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Close)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(ImportUserDatabaseDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), ImportUserDatabaseDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), ImportUserDatabaseDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(ImportUserDatabaseDialog)

    def retranslateUi(self, ImportUserDatabaseDialog):
        ImportUserDatabaseDialog.setWindowTitle(QtWidgets.QApplication.translate("ImportUserDatabaseDialog", "Import User Database", None, -1))
        self.groupBox.setTitle(QtWidgets.QApplication.translate("ImportUserDatabaseDialog", "Import file", None, -1))
        self.editInputFile.setPlaceholderText(QtWidgets.QApplication.translate("ImportUserDatabaseDialog", "Choose a file to import", None, -1))
        self.btBrowseInputFile.setText(QtWidgets.QApplication.translate("ImportUserDatabaseDialog", "&Browse...", None, -1))
        self.groupBox_2.setTitle(QtWidgets.QApplication.translate("ImportUserDatabaseDialog", "Database name", None, -1))
        self.editDatabaseName.setPlaceholderText(QtWidgets.QApplication.translate("ImportUserDatabaseDialog", "Choose a name for database", None, -1))

import ui_rc
