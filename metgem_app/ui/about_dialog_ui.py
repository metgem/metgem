# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'E:\git\metgem\metgem_app\ui\about_dialog.ui',
# licensing of 'E:\git\metgem\metgem_app\ui\about_dialog.ui' applies.
#
# Created: Sat Mar  5 14:42:48 2022
#      by: pyside2-uic  running on PySide2 5.13.2
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_AboutDialog(object):
    def setupUi(self, AboutDialog):
        AboutDialog.setObjectName("AboutDialog")
        AboutDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        AboutDialog.resize(512, 381)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icons/images/main.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        AboutDialog.setWindowIcon(icon)
        AboutDialog.setModal(True)
        self.gridLayout = QtWidgets.QGridLayout(AboutDialog)
        self.gridLayout.setObjectName("gridLayout")
        self.buttonBox = QtWidgets.QDialogButtonBox(AboutDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Close)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 8, 0, 1, 1)
        self.lblLogo = QtWidgets.QLabel(AboutDialog)
        self.lblLogo.setText("")
        self.lblLogo.setPixmap(QtGui.QPixmap(":/logo/images/main-wide.svg"))
        self.lblLogo.setScaledContents(False)
        self.lblLogo.setObjectName("lblLogo")
        self.gridLayout.addWidget(self.lblLogo, 0, 0, 1, 1)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem, 1, 0, 1, 1)
        self.lblVersion = QtWidgets.QLabel(AboutDialog)
        self.lblVersion.setObjectName("lblVersion")
        self.gridLayout.addWidget(self.lblVersion, 5, 0, 1, 2)
        self.lblTitle = QtWidgets.QLabel(AboutDialog)
        font = QtGui.QFont()
        font.setPointSize(9)
        font.setWeight(75)
        font.setItalic(False)
        font.setBold(True)
        self.lblTitle.setFont(font)
        self.lblTitle.setObjectName("lblTitle")
        self.gridLayout.addWidget(self.lblTitle, 4, 0, 1, 2)
        self.tabWidget = QtWidgets.QTabWidget(AboutDialog)
        self.tabWidget.setObjectName("tabWidget")
        self.about = QtWidgets.QWidget()
        self.about.setObjectName("about")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.about)
        self.verticalLayout.setObjectName("verticalLayout")
        self.txtAbout = QtWidgets.QTextBrowser(self.about)
        self.txtAbout.setOpenExternalLinks(True)
        self.txtAbout.setObjectName("txtAbout")
        self.verticalLayout.addWidget(self.txtAbout)
        self.tabWidget.addTab(self.about, "")
        self.authors = QtWidgets.QWidget()
        self.authors.setObjectName("authors")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.authors)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.txtAuthors = QtWidgets.QTextBrowser(self.authors)
        self.txtAuthors.setOpenExternalLinks(True)
        self.txtAuthors.setObjectName("txtAuthors")
        self.verticalLayout_2.addWidget(self.txtAuthors)
        self.tabWidget.addTab(self.authors, "")
        self.data = QtWidgets.QWidget()
        self.data.setObjectName("data")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.data)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.txtData = QtWidgets.QTextBrowser(self.data)
        self.txtData.setOpenExternalLinks(True)
        self.txtData.setObjectName("txtData")
        self.verticalLayout_3.addWidget(self.txtData)
        self.tabWidget.addTab(self.data, "")
        self.license = QtWidgets.QWidget()
        self.license.setObjectName("license")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.license)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.txtLicense = QtWidgets.QTextBrowser(self.license)
        self.txtLicense.setOpenExternalLinks(True)
        self.txtLicense.setObjectName("txtLicense")
        self.verticalLayout_4.addWidget(self.txtLicense)
        self.tabWidget.addTab(self.license, "")
        self.libraries = QtWidgets.QWidget()
        self.libraries.setObjectName("libraries")
        self.verticalLayout_5 = QtWidgets.QVBoxLayout(self.libraries)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.txtLibraries = QtWidgets.QTextBrowser(self.libraries)
        self.txtLibraries.setOpenExternalLinks(True)
        self.txtLibraries.setObjectName("txtLibraries")
        self.verticalLayout_5.addWidget(self.txtLibraries)
        self.tabWidget.addTab(self.libraries, "")
        self.gridLayout.addWidget(self.tabWidget, 7, 0, 1, 1)
        spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem1, 6, 0, 1, 1)

        self.retranslateUi(AboutDialog)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), AboutDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), AboutDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(AboutDialog)

    def retranslateUi(self, AboutDialog):
        AboutDialog.setWindowTitle(QtWidgets.QApplication.translate("AboutDialog", "About MetGem", None, -1))
        self.lblVersion.setText(QtWidgets.QApplication.translate("AboutDialog", "Version Unknown", None, -1))
        self.lblTitle.setText(QtWidgets.QApplication.translate("AboutDialog", "MetGem", None, -1))
        self.txtAbout.setHtml(QtWidgets.QApplication.translate("AboutDialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Noto Sans\'; font-size:10pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt;\">(c) 2018-2019, CNRS/ICSN</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'MS Shell Dlg 2\'; font-size:8.25pt;\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><a href=\"http://metgem.github.io\"><span style=\" font-family:\'MS Shell Dlg 2\'; font-size:8pt; text-decoration: underline; color:#0000ff;\">http://metgem.github.io</span></a></p></body></html>", None, -1))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.about), QtWidgets.QApplication.translate("AboutDialog", "&About", None, -1))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.authors), QtWidgets.QApplication.translate("AboutDialog", "A&uthors", None, -1))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.data), QtWidgets.QApplication.translate("AboutDialog", "&Data", None, -1))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.license), QtWidgets.QApplication.translate("AboutDialog", "&License Agreement", None, -1))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.libraries), QtWidgets.QApplication.translate("AboutDialog", "&Third-party libraries", None, -1))

import ui_rc
