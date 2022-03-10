# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'E:\git\metgem\metgem_app\ui\widgets\network.ui',
# licensing of 'E:\git\metgem\metgem_app\ui\widgets\network.ui' applies.
#
# Created: Sat Mar  5 14:43:03 2022
#      by: pyside2-uic  running on PySide2 5.13.2
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_NetworkFrame(object):
    def setupUi(self, NetworkFrame):
        NetworkFrame.setObjectName("NetworkFrame")
        NetworkFrame.resize(423, 411)
        NetworkFrame.setWindowTitle("")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(NetworkFrame)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.btOptions = QtWidgets.QToolButton(NetworkFrame)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icons/images/preferences-system.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btOptions.setIcon(icon)
        self.btOptions.setObjectName("btOptions")
        self.verticalLayout.addWidget(self.btOptions)
        self.btRuler = QtWidgets.QToolButton(NetworkFrame)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/icons/images/ruler.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btRuler.setIcon(icon1)
        self.btRuler.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self.btRuler.setObjectName("btRuler")
        self.verticalLayout.addWidget(self.btRuler)
        self.btLock = QtWidgets.QToolButton(NetworkFrame)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/icons/images/lock.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btLock.setIcon(icon2)
        self.btLock.setCheckable(True)
        self.btLock.setChecked(True)
        self.btLock.setObjectName("btLock")
        self.verticalLayout.addWidget(self.btLock)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.horizontalLayout_2.addLayout(self.verticalLayout)
        self.gvNetwork = AnnotationsNetworkView(NetworkFrame)
        self.gvNetwork.setObjectName("gvNetwork")
        self.horizontalLayout_2.addWidget(self.gvNetwork)
        self.sliderScale = Slider(NetworkFrame)
        self.sliderScale.setMinimumSize(QtCore.QSize(200, 0))
        self.sliderScale.setMinimum(1)
        self.sliderScale.setMaximum(100)
        self.sliderScale.setSingleStep(1)
        self.sliderScale.setProperty("value", 11)
        self.sliderScale.setOrientation(QtCore.Qt.Horizontal)
        self.sliderScale.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.sliderScale.setTickInterval(5)
        self.sliderScale.setObjectName("sliderScale")
        self.horizontalLayout_2.addWidget(self.sliderScale)

        self.retranslateUi(NetworkFrame)
        QtCore.QMetaObject.connectSlotsByName(NetworkFrame)

    def retranslateUi(self, NetworkFrame):
        self.btOptions.setToolTip(QtWidgets.QApplication.translate("NetworkFrame", "Change Network Options", None, -1))
        self.btOptions.setStatusTip(QtWidgets.QApplication.translate("NetworkFrame", "Change Network Options", None, -1))
        self.btOptions.setText(QtWidgets.QApplication.translate("NetworkFrame", "...", None, -1))
        self.btRuler.setToolTip(QtWidgets.QApplication.translate("NetworkFrame", "Change Network Scale", None, -1))
        self.btRuler.setStatusTip(QtWidgets.QApplication.translate("NetworkFrame", "Change Network Scale", None, -1))
        self.btRuler.setText(QtWidgets.QApplication.translate("NetworkFrame", "...", None, -1))
        self.btLock.setToolTip(QtWidgets.QApplication.translate("NetworkFrame", "Prevent the movement of nodes in this view", None, -1))
        self.btLock.setStatusTip(QtWidgets.QApplication.translate("NetworkFrame", "Prevent the movement of nodes in this view", None, -1))
        self.btLock.setText(QtWidgets.QApplication.translate("NetworkFrame", "...", None, -1))
        self.sliderScale.setToolTip(QtWidgets.QApplication.translate("NetworkFrame", "Change scale of network graph", None, -1))
        self.sliderScale.setStatusTip(QtWidgets.QApplication.translate("NetworkFrame", "Change scale of network graph", None, -1))

from metgem_app.ui.widgets.slider import Slider
from metgem_app.ui.widgets.annotations.view import AnnotationsNetworkView
import ui_rc
