# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'E:\git\metgem\metgem_app\ui\updates_dialog.ui',
# licensing of 'E:\git\metgem\metgem_app\ui\updates_dialog.ui' applies.
#
# Created: Sat Mar  5 14:42:59 2022
#      by: pyside2-uic  running on PySide2 5.13.2
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_UpdateDialog(object):
    def setupUi(self, UpdateDialog):
        UpdateDialog.setObjectName("UpdateDialog")
        UpdateDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        UpdateDialog.resize(381, 206)
        UpdateDialog.setModal(True)
        self.gridLayout = QtWidgets.QGridLayout(UpdateDialog)
        self.gridLayout.setObjectName("gridLayout")
        self.buttonBox = QtWidgets.QDialogButtonBox(UpdateDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Close)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 8, 0, 1, 4)
        self.lblNewVersion = QtWidgets.QLabel(UpdateDialog)
        self.lblNewVersion.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        self.lblNewVersion.setObjectName("lblNewVersion")
        self.gridLayout.addWidget(self.lblNewVersion, 6, 2, 1, 1)
        self.lblCurrentVersion = QtWidgets.QLabel(UpdateDialog)
        self.lblCurrentVersion.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        self.lblCurrentVersion.setObjectName("lblCurrentVersion")
        self.gridLayout.addWidget(self.lblCurrentVersion, 5, 2, 1, 1)
        self.lblReleaseNotes = QtWidgets.QLabel(UpdateDialog)
        self.lblReleaseNotes.setObjectName("lblReleaseNotes")
        self.gridLayout.addWidget(self.lblReleaseNotes, 2, 0, 1, 4)
        self.label_3 = QtWidgets.QLabel(UpdateDialog)
        self.label_3.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 6, 0, 1, 2)
        self.label = QtWidgets.QLabel(UpdateDialog)
        self.label.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 5, 0, 1, 2)
        self.lblReleaseNotesText = QtWidgets.QLabel(UpdateDialog)
        self.lblReleaseNotesText.setOpenExternalLinks(True)
        self.lblReleaseNotesText.setObjectName("lblReleaseNotesText")
        self.gridLayout.addWidget(self.lblReleaseNotesText, 3, 1, 1, 3)
        self.lblNewversion = QtWidgets.QLabel(UpdateDialog)
        self.lblNewversion.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        self.lblNewversion.setObjectName("lblNewversion")
        self.gridLayout.addWidget(self.lblNewversion, 0, 0, 1, 4)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 5, 3, 1, 1)
        spacerItem1 = QtWidgets.QSpacerItem(20, 10, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        self.gridLayout.addItem(spacerItem1, 4, 0, 1, 1)
        spacerItem2 = QtWidgets.QSpacerItem(20, 10, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        self.gridLayout.addItem(spacerItem2, 1, 0, 1, 1)
        spacerItem3 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem3, 7, 0, 1, 1)
        spacerItem4 = QtWidgets.QSpacerItem(20, 0, QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem4, 3, 0, 1, 1)

        self.retranslateUi(UpdateDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), UpdateDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), UpdateDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(UpdateDialog)

    def retranslateUi(self, UpdateDialog):
        UpdateDialog.setWindowTitle(QtWidgets.QApplication.translate("UpdateDialog", "Updates", None, -1))
        self.lblNewVersion.setText(QtWidgets.QApplication.translate("UpdateDialog", "v1.2.2", None, -1))
        self.lblCurrentVersion.setText(QtWidgets.QApplication.translate("UpdateDialog", "v1.2.1", None, -1))
        self.lblReleaseNotes.setText(QtWidgets.QApplication.translate("UpdateDialog", "<html><head/><body><p><span style=\" font-style:italic;\">What\'s new?</span></p></body></html>", None, -1))
        self.label_3.setText(QtWidgets.QApplication.translate("UpdateDialog", "New version:", None, -1))
        self.label.setText(QtWidgets.QApplication.translate("UpdateDialog", "Current Version:", None, -1))
        self.lblReleaseNotesText.setText(QtWidgets.QApplication.translate("UpdateDialog", "- Add support for MS1 spectra as input", None, -1))
        self.lblNewversion.setText(QtWidgets.QApplication.translate("UpdateDialog", "<html><head/><body><p><span style=\" font-weight:600;\">MetGem v1.2.2</span> is now available.</p></body></html>", None, -1))

