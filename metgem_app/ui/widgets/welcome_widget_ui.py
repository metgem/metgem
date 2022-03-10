# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'E:\git\metgem\metgem_app\ui\widgets\welcome_widget.ui',
# licensing of 'E:\git\metgem\metgem_app\ui\widgets\welcome_widget.ui' applies.
#
# Created: Sat Mar  5 14:43:07 2022
#      by: pyside2-uic  running on PySide2 5.13.2
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_WelcomeScreen(object):
    def setupUi(self, WelcomeScreen):
        WelcomeScreen.setObjectName("WelcomeScreen")
        WelcomeScreen.resize(902, 473)
        WelcomeScreen.setStyleSheet("background-color: palette(dark);")
        self.horizontalLayout = QtWidgets.QHBoxLayout(WelcomeScreen)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.gridLayout_4 = QtWidgets.QGridLayout()
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.label = QtWidgets.QLabel(WelcomeScreen)
        self.label.setStyleSheet("font-size: 20pt; color: palette(base);")
        self.label.setAlignment(QtCore.Qt.AlignBottom|QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft)
        self.label.setObjectName("label")
        self.gridLayout_4.addWidget(self.label, 0, 0, 1, 6)
        self.lstRecentProjects = QtWidgets.QListWidget(WelcomeScreen)
        self.lstRecentProjects.setProperty("cursor", QtCore.Qt.PointingHandCursor)
        self.lstRecentProjects.setAutoFillBackground(True)
        self.lstRecentProjects.setStyleSheet("QListWidget\n"
"{\n"
"    text-decoration: underline;\n"
"    color: palette(midlight);\n"
"    background-color: palette(mid);\n"
"    selection-background-color: palette(mid);\n"
"}\n"
"\n"
"QToolTip\n"
"{\n"
"    color: palette(tooltiptext);\n"
"    background-color: palette(tooltip);\n"
"}")
        self.lstRecentProjects.setFrameShape(QtWidgets.QFrame.Box)
        self.lstRecentProjects.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.lstRecentProjects.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.lstRecentProjects.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.lstRecentProjects.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.lstRecentProjects.setTextElideMode(QtCore.Qt.ElideMiddle)
        self.lstRecentProjects.setUniformItemSizes(True)
        self.lstRecentProjects.setBatchSize(10)
        self.lstRecentProjects.setObjectName("lstRecentProjects")
        QtWidgets.QListWidgetItem(self.lstRecentProjects)
        QtWidgets.QListWidgetItem(self.lstRecentProjects)
        QtWidgets.QListWidgetItem(self.lstRecentProjects)
        QtWidgets.QListWidgetItem(self.lstRecentProjects)
        QtWidgets.QListWidgetItem(self.lstRecentProjects)
        QtWidgets.QListWidgetItem(self.lstRecentProjects)
        QtWidgets.QListWidgetItem(self.lstRecentProjects)
        QtWidgets.QListWidgetItem(self.lstRecentProjects)
        QtWidgets.QListWidgetItem(self.lstRecentProjects)
        QtWidgets.QListWidgetItem(self.lstRecentProjects)
        self.gridLayout_4.addWidget(self.lstRecentProjects, 6, 0, 1, 6)
        self.label_4 = QtWidgets.QLabel(WelcomeScreen)
        self.label_4.setStyleSheet("font-size: 20pt; color: palette(base);")
        self.label_4.setAlignment(QtCore.Qt.AlignBottom|QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft)
        self.label_4.setObjectName("label_4")
        self.gridLayout_4.addWidget(self.label_4, 4, 0, 2, 4)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout_4.addItem(spacerItem, 5, 4, 1, 1)
        self.btClearRecentProjects = QtWidgets.QPushButton(WelcomeScreen)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btClearRecentProjects.sizePolicy().hasHeightForWidth())
        self.btClearRecentProjects.setSizePolicy(sizePolicy)
        self.btClearRecentProjects.setMaximumSize(QtCore.QSize(16777215, 32))
        self.btClearRecentProjects.setCursor(QtCore.Qt.PointingHandCursor)
        self.btClearRecentProjects.setStyleSheet("QPushButton\n"
"{\n"
"    text-decoration: underline;\n"
"    color: palette(base);\n"
"    border: none;\n"
"}\n"
"\n"
"QToolTip\n"
"{\n"
"    color: palette(tooltiptext);\n"
"    background-color: palette(tooltip);\n"
"}")
        self.btClearRecentProjects.setFlat(True)
        self.btClearRecentProjects.setObjectName("btClearRecentProjects")
        self.gridLayout_4.addWidget(self.btClearRecentProjects, 5, 5, 1, 1)
        spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Maximum)
        self.gridLayout_4.addItem(spacerItem1, 3, 1, 1, 5)
        spacerItem2 = QtWidgets.QSpacerItem(20, 5, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Maximum)
        self.gridLayout_4.addItem(spacerItem2, 4, 5, 1, 1)
        self.btImportData = QtWidgets.QPushButton(WelcomeScreen)
        self.btImportData.setCursor(QtCore.Qt.PointingHandCursor)
        self.btImportData.setStyleSheet("QPushButton\n"
"{\n"
"    text-decoration: underline;\n"
"    color: palette(midlight);\n"
"    border: none;\n"
"}\n"
"\n"
"QToolTip\n"
"{\n"
"    color: palette(tooltiptext);\n"
"    background-color: palette(tooltip);\n"
"}")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icons/images/import-mgf.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btImportData.setIcon(icon)
        self.btImportData.setIconSize(QtCore.QSize(32, 32))
        self.btImportData.setFlat(True)
        self.btImportData.setObjectName("btImportData")
        self.gridLayout_4.addWidget(self.btImportData, 1, 1, 1, 2)
        self.btOpenProject = QtWidgets.QPushButton(WelcomeScreen)
        self.btOpenProject.setCursor(QtCore.Qt.PointingHandCursor)
        self.btOpenProject.setStyleSheet("QPushButton\n"
"{\n"
"    text-decoration: underline;\n"
"    color: palette(midlight);\n"
"    border: none;\n"
"}\n"
"\n"
"QToolTip\n"
"{\n"
"    color: palette(tooltiptext);\n"
"    background-color: palette(tooltip);\n"
"}")
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/icons/images/document-open.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btOpenProject.setIcon(icon1)
        self.btOpenProject.setIconSize(QtCore.QSize(32, 32))
        self.btOpenProject.setFlat(True)
        self.btOpenProject.setObjectName("btOpenProject")
        self.gridLayout_4.addWidget(self.btOpenProject, 2, 1, 1, 2)
        spacerItem3 = QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout_4.addItem(spacerItem3, 1, 3, 1, 3)
        self.label_16 = QtWidgets.QLabel(WelcomeScreen)
        self.label_16.setMaximumSize(QtCore.QSize(10, 16777215))
        self.label_16.setText("")
        self.label_16.setObjectName("label_16")
        self.gridLayout_4.addWidget(self.label_16, 1, 0, 1, 1)
        self.horizontalLayout.addLayout(self.gridLayout_4)
        spacerItem4 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem4)
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.label_17 = QtWidgets.QLabel(WelcomeScreen)
        self.label_17.setStyleSheet("QToolTip\n"
"{\n"
"    color: palette(tooltiptext);\n"
"    background-color: palette(tooltip);\n"
"}")
        self.label_17.setTextFormat(QtCore.Qt.RichText)
        self.label_17.setOpenExternalLinks(True)
        self.label_17.setObjectName("label_17")
        self.gridLayout.addWidget(self.label_17, 9, 2, 1, 1)
        self.label_12 = QtWidgets.QLabel(WelcomeScreen)
        self.label_12.setMaximumSize(QtCore.QSize(32, 32))
        self.label_12.setText("")
        self.label_12.setPixmap(QtGui.QPixmap(":/icons/images/git.svg"))
        self.label_12.setScaledContents(True)
        self.label_12.setObjectName("label_12")
        self.gridLayout.addWidget(self.label_12, 4, 1, 1, 1)
        self.label_11 = QtWidgets.QLabel(WelcomeScreen)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_11.sizePolicy().hasHeightForWidth())
        self.label_11.setSizePolicy(sizePolicy)
        self.label_11.setMaximumSize(QtCore.QSize(32, 32))
        self.label_11.setText("")
        self.label_11.setPixmap(QtGui.QPixmap(":/icons/images/browser.svg"))
        self.label_11.setScaledContents(True)
        self.label_11.setObjectName("label_11")
        self.gridLayout.addWidget(self.label_11, 3, 1, 1, 1)
        self.label_10 = QtWidgets.QLabel(WelcomeScreen)
        self.label_10.setText("")
        self.label_10.setPixmap(QtGui.QPixmap(":/icons/images/help.svg"))
        self.label_10.setObjectName("label_10")
        self.gridLayout.addWidget(self.label_10, 2, 1, 1, 1)
        spacerItem5 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem5, 5, 1, 1, 2)
        self.label_7 = QtWidgets.QLabel(WelcomeScreen)
        self.label_7.setStyleSheet("QToolTip\n"
"{\n"
"    color: palette(tooltiptext);\n"
"    background-color: palette(tooltip);\n"
"}")
        self.label_7.setTextFormat(QtCore.Qt.RichText)
        self.label_7.setOpenExternalLinks(True)
        self.label_7.setObjectName("label_7")
        self.gridLayout.addWidget(self.label_7, 4, 2, 1, 1)
        self.label_14 = QtWidgets.QLabel(WelcomeScreen)
        self.label_14.setMinimumSize(QtCore.QSize(32, 32))
        self.label_14.setMaximumSize(QtCore.QSize(32, 32))
        self.label_14.setText("")
        self.label_14.setPixmap(QtGui.QPixmap(":/icons/images/academic.svg"))
        self.label_14.setScaledContents(True)
        self.label_14.setObjectName("label_14")
        self.gridLayout.addWidget(self.label_14, 9, 1, 1, 1)
        self.label_3 = QtWidgets.QLabel(WelcomeScreen)
        self.label_3.setMinimumSize(QtCore.QSize(32, 32))
        self.label_3.setMaximumSize(QtCore.QSize(32, 32))
        self.label_3.setText("")
        self.label_3.setPixmap(QtGui.QPixmap(":/icons/images/academic.svg"))
        self.label_3.setScaledContents(True)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 8, 1, 1, 1)
        self.label_5 = QtWidgets.QLabel(WelcomeScreen)
        self.label_5.setToolTip("")
        self.label_5.setStyleSheet("QToolTip\n"
"{\n"
"    color: palette(tooltiptext);\n"
"    background-color: palette(tooltip);\n"
"}")
        self.label_5.setTextFormat(QtCore.Qt.RichText)
        self.label_5.setOpenExternalLinks(True)
        self.label_5.setObjectName("label_5")
        self.gridLayout.addWidget(self.label_5, 1, 2, 1, 1)
        spacerItem6 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem6, 10, 1, 1, 2)
        self.label_6 = QtWidgets.QLabel(WelcomeScreen)
        self.label_6.setStyleSheet("QToolTip\n"
"{\n"
"    color: palette(tooltiptext);\n"
"    background-color: palette(tooltip);\n"
"}")
        self.label_6.setTextFormat(QtCore.Qt.RichText)
        self.label_6.setOpenExternalLinks(True)
        self.label_6.setObjectName("label_6")
        self.gridLayout.addWidget(self.label_6, 2, 2, 1, 1)
        self.label_8 = QtWidgets.QLabel(WelcomeScreen)
        self.label_8.setStyleSheet("QToolTip\n"
"{\n"
"    color: palette(tooltiptext);\n"
"    background-color: palette(tooltip);\n"
"}")
        self.label_8.setTextFormat(QtCore.Qt.RichText)
        self.label_8.setOpenExternalLinks(True)
        self.label_8.setObjectName("label_8")
        self.gridLayout.addWidget(self.label_8, 3, 2, 1, 1)
        self.label_9 = QtWidgets.QLabel(WelcomeScreen)
        self.label_9.setText("")
        self.label_9.setPixmap(QtGui.QPixmap(":/icons/images/help.svg"))
        self.label_9.setObjectName("label_9")
        self.gridLayout.addWidget(self.label_9, 1, 1, 1, 1)
        self.label_15 = QtWidgets.QLabel(WelcomeScreen)
        self.label_15.setStyleSheet("QToolTip\n"
"{\n"
"    color: palette(tooltiptext);\n"
"    background-color: palette(tooltip);\n"
"}")
        self.label_15.setTextFormat(QtCore.Qt.RichText)
        self.label_15.setOpenExternalLinks(True)
        self.label_15.setObjectName("label_15")
        self.gridLayout.addWidget(self.label_15, 8, 2, 1, 1)
        spacerItem7 = QtWidgets.QSpacerItem(10, 20, QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem7, 1, 0, 1, 1)
        self.label_2 = QtWidgets.QLabel(WelcomeScreen)
        self.label_2.setStyleSheet("font-size: 20pt; color: palette(base);")
        self.label_2.setAlignment(QtCore.Qt.AlignBottom|QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 0, 0, 1, 3)
        self.label_18 = QtWidgets.QLabel(WelcomeScreen)
        self.label_18.setStyleSheet("font-size: 20pt; color: palette(base);")
        self.label_18.setAlignment(QtCore.Qt.AlignBottom|QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft)
        self.label_18.setObjectName("label_18")
        self.gridLayout.addWidget(self.label_18, 6, 0, 1, 3)
        self.label_13 = QtWidgets.QLabel(WelcomeScreen)
        self.label_13.setStyleSheet("color: palette(midlight);")
        self.label_13.setObjectName("label_13")
        self.gridLayout.addWidget(self.label_13, 7, 0, 1, 3)
        self.horizontalLayout.addLayout(self.gridLayout)
        spacerItem8 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem8)
        self.gridLayout_2 = QtWidgets.QGridLayout()
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.chkEnableNews = QtWidgets.QCheckBox(WelcomeScreen)
        self.chkEnableNews.setStyleSheet("QCheckBox\n"
"{\n"
"    color: palette(base);\n"
"}\n"
"\n"
"QToolTip\n"
"{\n"
"    color: palette(tooltiptext);\n"
"    background-color: palette(tooltip);\n"
"}")
        self.chkEnableNews.setObjectName("chkEnableNews")
        self.gridLayout_2.addWidget(self.chkEnableNews, 0, 1, 2, 1)
        self.lblNews = QtWidgets.QLabel(WelcomeScreen)
        self.lblNews.setStyleSheet("font-size: 20pt; color: palette(base);")
        self.lblNews.setAlignment(QtCore.Qt.AlignBottom|QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft)
        self.lblNews.setObjectName("lblNews")
        self.gridLayout_2.addWidget(self.lblNews, 0, 0, 2, 1)
        self.lstNews = QtWidgets.QListWidget(WelcomeScreen)
        self.lstNews.setProperty("cursor", QtCore.Qt.PointingHandCursor)
        self.lstNews.setAutoFillBackground(True)
        self.lstNews.setStyleSheet("QListWidget\n"
"{\n"
"    color: palette(midlight);\n"
"    background-color: palette(mid);\n"
"    selection-background-color: palette(mid);\n"
"}\n"
"\n"
"QToolTip\n"
"{\n"
"    color: palette(tooltiptext);\n"
"    background-color: palette(tooltip);\n"
"}")
        self.lstNews.setFrameShape(QtWidgets.QFrame.Box)
        self.lstNews.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.lstNews.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.lstNews.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.lstNews.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.lstNews.setResizeMode(QtWidgets.QListView.Adjust)
        self.lstNews.setObjectName("lstNews")
        self.gridLayout_2.addWidget(self.lstNews, 2, 0, 1, 2)
        self.horizontalLayout.addLayout(self.gridLayout_2)

        self.retranslateUi(WelcomeScreen)
        QtCore.QMetaObject.connectSlotsByName(WelcomeScreen)

    def retranslateUi(self, WelcomeScreen):
        WelcomeScreen.setWindowTitle(QtWidgets.QApplication.translate("WelcomeScreen", "Form", None, -1))
        self.label.setText(QtWidgets.QApplication.translate("WelcomeScreen", "Start", None, -1))
        __sortingEnabled = self.lstRecentProjects.isSortingEnabled()
        self.lstRecentProjects.setSortingEnabled(False)
        self.lstRecentProjects.item(0).setText(QtWidgets.QApplication.translate("WelcomeScreen", "1", None, -1))
        self.lstRecentProjects.item(1).setText(QtWidgets.QApplication.translate("WelcomeScreen", "2", None, -1))
        self.lstRecentProjects.item(2).setText(QtWidgets.QApplication.translate("WelcomeScreen", "3", None, -1))
        self.lstRecentProjects.item(3).setText(QtWidgets.QApplication.translate("WelcomeScreen", "4", None, -1))
        self.lstRecentProjects.item(4).setText(QtWidgets.QApplication.translate("WelcomeScreen", "5", None, -1))
        self.lstRecentProjects.item(5).setText(QtWidgets.QApplication.translate("WelcomeScreen", "6", None, -1))
        self.lstRecentProjects.item(6).setText(QtWidgets.QApplication.translate("WelcomeScreen", "7", None, -1))
        self.lstRecentProjects.item(7).setText(QtWidgets.QApplication.translate("WelcomeScreen", "8", None, -1))
        self.lstRecentProjects.item(8).setText(QtWidgets.QApplication.translate("WelcomeScreen", "9", None, -1))
        self.lstRecentProjects.item(9).setText(QtWidgets.QApplication.translate("WelcomeScreen", "10", None, -1))
        self.lstRecentProjects.setSortingEnabled(__sortingEnabled)
        self.label_4.setText(QtWidgets.QApplication.translate("WelcomeScreen", "Recent Projects", None, -1))
        self.btClearRecentProjects.setToolTip(QtWidgets.QApplication.translate("WelcomeScreen", "Clear the recent projects list", None, -1))
        self.btClearRecentProjects.setStatusTip(QtWidgets.QApplication.translate("WelcomeScreen", "Clear the recent projects list", None, -1))
        self.btClearRecentProjects.setText(QtWidgets.QApplication.translate("WelcomeScreen", "Clear", None, -1))
        self.btImportData.setToolTip(QtWidgets.QApplication.translate("WelcomeScreen", "Import a spectra list and compute scores", None, -1))
        self.btImportData.setStatusTip(QtWidgets.QApplication.translate("WelcomeScreen", "Import a spectra list and compute scores", None, -1))
        self.btImportData.setText(QtWidgets.QApplication.translate("WelcomeScreen", "Import Data", None, -1))
        self.btOpenProject.setToolTip(QtWidgets.QApplication.translate("WelcomeScreen", "Load a previously saved project file", None, -1))
        self.btOpenProject.setStatusTip(QtWidgets.QApplication.translate("WelcomeScreen", "Load a previously saved project file", None, -1))
        self.btOpenProject.setText(QtWidgets.QApplication.translate("WelcomeScreen", "Open Project", None, -1))
        self.label_17.setStatusTip(QtWidgets.QApplication.translate("WelcomeScreen", "https://dx.doi.org/10.1021/acs.analchem.9b02802", None, -1))
        self.label_17.setText(QtWidgets.QApplication.translate("WelcomeScreen", "<a href=\"https://dx.doi.org/10.1021/acs.analchem.9b02802\" style=\"text-decoration: underline; color: palette(midlight);\">Anal. Chem. 2019, 91, 18, 11489-11492</a>", None, -1))
        self.label_7.setStatusTip(QtWidgets.QApplication.translate("WelcomeScreen", "https://github.com/metgem/metgem", None, -1))
        self.label_7.setText(QtWidgets.QApplication.translate("WelcomeScreen", "<a href=\"https://github.com/metgem/metgem\" style=\"text-decoration: underline; color: palette(midlight);\">Source Code</a>", None, -1))
        self.label_5.setStatusTip(QtWidgets.QApplication.translate("WelcomeScreen", "https://metgem.readthedocs.io", None, -1))
        self.label_5.setText(QtWidgets.QApplication.translate("WelcomeScreen", "<a href=\"https://metgem.readthedocs.io\" style=\"text-decoration: underline; color: palette(midlight);\">User Manual</a>", None, -1))
        self.label_6.setStatusTip(QtWidgets.QApplication.translate("WelcomeScreen", "https://metgem.readthedocs.io/getting_started.html", None, -1))
        self.label_6.setText(QtWidgets.QApplication.translate("WelcomeScreen", "<a href=\"https://metgem.readthedocs.io/getting_started.html\" style=\"text-decoration: underline; color: palette(midlight);\">Getting Started</a>", None, -1))
        self.label_8.setStatusTip(QtWidgets.QApplication.translate("WelcomeScreen", "https://metgem.github.io", None, -1))
        self.label_8.setText(QtWidgets.QApplication.translate("WelcomeScreen", "<a href=\"https://metgem.github.io\" style=\"text-decoration: underline; color: palette(midlight);\">MetGem Website</a>", None, -1))
        self.label_15.setStatusTip(QtWidgets.QApplication.translate("WelcomeScreen", "https://dx.doi.org/10.1021/acs.analchem.8b03099", None, -1))
        self.label_15.setText(QtWidgets.QApplication.translate("WelcomeScreen", "<a href=\"https://dx.doi.org/10.1021/acs.analchem.8b03099\"style=\"text-decoration: underline; color: palette(midlight);\">Anal. Chem. 2018, 90, 23, 13900-13908</a>", None, -1))
        self.label_2.setText(QtWidgets.QApplication.translate("WelcomeScreen", "Community", None, -1))
        self.label_18.setText(QtWidgets.QApplication.translate("WelcomeScreen", "Publications", None, -1))
        self.label_13.setText(QtWidgets.QApplication.translate("WelcomeScreen", "If you use MetGem for your research, please cite", None, -1))
        self.chkEnableNews.setToolTip(QtWidgets.QApplication.translate("WelcomeScreen", "Show news about MetGem: this needs internet to retrieve information from MetGem\'s website", None, -1))
        self.chkEnableNews.setStatusTip(QtWidgets.QApplication.translate("WelcomeScreen", "Show news about MetGem: this needs internet to retrieve information from MetGem\'s website", None, -1))
        self.chkEnableNews.setText(QtWidgets.QApplication.translate("WelcomeScreen", "Enabled", None, -1))
        self.lblNews.setText(QtWidgets.QApplication.translate("WelcomeScreen", "News", None, -1))

import ui_rc
