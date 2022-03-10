# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'E:\git\metgem\metgem_app\ui\settings_dialog.ui',
# licensing of 'E:\git\metgem\metgem_app\ui\settings_dialog.ui' applies.
#
# Created: Sat Mar  5 14:42:58 2022
#      by: pyside2-uic  running on PySide2 5.13.2
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_SettingsDialog(object):
    def setupUi(self, SettingsDialog):
        SettingsDialog.setObjectName("SettingsDialog")
        SettingsDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        SettingsDialog.resize(599, 434)
        SettingsDialog.setModal(True)
        self.gridLayout = QtWidgets.QGridLayout(SettingsDialog)
        self.gridLayout.setObjectName("gridLayout")
        self.tabWidget = QtWidgets.QTabWidget(SettingsDialog)
        self.tabWidget.setObjectName("tabWidget")
        self.theme = QtWidgets.QWidget()
        self.theme.setObjectName("theme")
        self.gridLayout_3 = QtWidgets.QGridLayout(self.theme)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.lstStyles = QtWidgets.QListWidget(self.theme)
        self.lstStyles.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.lstStyles.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.lstStyles.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.lstStyles.setObjectName("lstStyles")
        self.gridLayout_3.addWidget(self.lstStyles, 0, 1, 1, 3)
        self.chkOverrideFontSize = QtWidgets.QCheckBox(self.theme)
        self.chkOverrideFontSize.setObjectName("chkOverrideFontSize")
        self.gridLayout_3.addWidget(self.chkOverrideFontSize, 1, 1, 1, 2)
        self.spinFontSize = QtWidgets.QSpinBox(self.theme)
        self.spinFontSize.setEnabled(False)
        self.spinFontSize.setMinimum(1)
        self.spinFontSize.setMaximum(100)
        self.spinFontSize.setProperty("value", 12)
        self.spinFontSize.setObjectName("spinFontSize")
        self.gridLayout_3.addWidget(self.spinFontSize, 1, 3, 1, 1)
        self.gvStylePreview = NetworkView(self.theme)
        self.gvStylePreview.setMinimumSize(QtCore.QSize(200, 200))
        self.gvStylePreview.setObjectName("gvStylePreview")
        self.gridLayout_3.addWidget(self.gvStylePreview, 0, 0, 2, 1)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icons/images/main.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.tabWidget.addTab(self.theme, icon, "")
        self.metadata = QtWidgets.QWidget()
        self.metadata.setObjectName("metadata")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.metadata)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.spinFloatPrecision = QtWidgets.QSpinBox(self.metadata)
        self.spinFloatPrecision.setMaximum(10)
        self.spinFloatPrecision.setProperty("value", 4)
        self.spinFloatPrecision.setObjectName("spinFloatPrecision")
        self.gridLayout_2.addWidget(self.spinFloatPrecision, 0, 2, 1, 1)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout_2.addItem(spacerItem, 2, 0, 1, 1)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout_2.addItem(spacerItem1, 0, 3, 1, 1)
        self.label = QtWidgets.QLabel(self.metadata)
        self.label.setObjectName("label")
        self.gridLayout_2.addWidget(self.label, 1, 0, 1, 1)
        self.spinNeutralTolerance = QtWidgets.QSpinBox(self.metadata)
        self.spinNeutralTolerance.setMinimum(1)
        self.spinNeutralTolerance.setMaximum(500)
        self.spinNeutralTolerance.setProperty("value", 50)
        self.spinNeutralTolerance.setObjectName("spinNeutralTolerance")
        self.gridLayout_2.addWidget(self.spinNeutralTolerance, 1, 2, 1, 1)
        self.label_2 = QtWidgets.QLabel(self.metadata)
        self.label_2.setObjectName("label_2")
        self.gridLayout_2.addWidget(self.label_2, 0, 0, 1, 1)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/icons/images/metadata.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.tabWidget.addTab(self.metadata, icon1, "")
        self.gridLayout.addWidget(self.tabWidget, 0, 0, 1, 1)
        self.buttonBox = QtWidgets.QDialogButtonBox(SettingsDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 1, 0, 1, 2)

        self.retranslateUi(SettingsDialog)
        self.tabWidget.setCurrentIndex(1)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), SettingsDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), SettingsDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(SettingsDialog)

    def retranslateUi(self, SettingsDialog):
        SettingsDialog.setWindowTitle(QtWidgets.QApplication.translate("SettingsDialog", "Settings", None, -1))
        self.chkOverrideFontSize.setToolTip(QtWidgets.QApplication.translate("SettingsDialog", "Override the selected theme\'s font size", None, -1))
        self.chkOverrideFontSize.setText(QtWidgets.QApplication.translate("SettingsDialog", "Override font size", None, -1))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.theme), QtWidgets.QApplication.translate("SettingsDialog", "&Theme", None, -1))
        self.spinFloatPrecision.setToolTip(QtWidgets.QApplication.translate("SettingsDialog", "Maximum number of decimals for float in metadata (this setting may need a restart to be fully applied)", None, -1))
        self.label.setText(QtWidgets.QApplication.translate("SettingsDialog", "Neutral losses assignment tolerance:", None, -1))
        self.spinNeutralTolerance.setToolTip(QtWidgets.QApplication.translate("SettingsDialog", "Tolerance (in ppm) for assignment of possible structure of neutral losses in edges table", None, -1))
        self.spinNeutralTolerance.setSuffix(QtWidgets.QApplication.translate("SettingsDialog", " ppm", None, -1))
        self.label_2.setText(QtWidgets.QApplication.translate("SettingsDialog", "Float precision", None, -1))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.metadata), QtWidgets.QApplication.translate("SettingsDialog", "&Metadata", None, -1))

from PySide2MolecularNetwork import NetworkView
import ui_rc
