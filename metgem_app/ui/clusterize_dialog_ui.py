# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'E:\git\metgem\metgem_app\ui\clusterize_dialog.ui',
# licensing of 'E:\git\metgem\metgem_app\ui\clusterize_dialog.ui' applies.
#
# Created: Sat Mar  5 14:42:50 2022
#      by: pyside2-uic  running on PySide2 5.13.2
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        Dialog.resize(230, 197)
        self.formLayout = QtWidgets.QFormLayout(Dialog)
        self.formLayout.setObjectName("formLayout")
        self.label = QtWidgets.QLabel(Dialog)
        self.label.setObjectName("label")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.label)
        self.btColumnName = QtWidgets.QLineEdit(Dialog)
        self.btColumnName.setObjectName("btColumnName")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.btColumnName)
        self.label_2 = QtWidgets.QLabel(Dialog)
        self.label_2.setObjectName("label_2")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.label_2)
        self.spinMinClusterSize = QtWidgets.QSpinBox(Dialog)
        self.spinMinClusterSize.setMinimum(2)
        self.spinMinClusterSize.setMaximum(1000)
        self.spinMinClusterSize.setProperty("value", 5)
        self.spinMinClusterSize.setObjectName("spinMinClusterSize")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.spinMinClusterSize)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.formLayout.setWidget(6, QtWidgets.QFormLayout.SpanningRole, self.buttonBox)
        self.chkMinSamples = QtWidgets.QCheckBox(Dialog)
        self.chkMinSamples.setObjectName("chkMinSamples")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.chkMinSamples)
        self.spinMinSamples = QtWidgets.QSpinBox(Dialog)
        self.spinMinSamples.setEnabled(False)
        self.spinMinSamples.setMinimum(2)
        self.spinMinSamples.setMaximum(1000)
        self.spinMinSamples.setObjectName("spinMinSamples")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.spinMinSamples)
        self.label_3 = QtWidgets.QLabel(Dialog)
        self.label_3.setObjectName("label_3")
        self.formLayout.setWidget(4, QtWidgets.QFormLayout.LabelRole, self.label_3)
        self.spinEpsilon = QtWidgets.QDoubleSpinBox(Dialog)
        self.spinEpsilon.setDecimals(1)
        self.spinEpsilon.setMaximum(1.0)
        self.spinEpsilon.setSingleStep(0.1)
        self.spinEpsilon.setObjectName("spinEpsilon")
        self.formLayout.setWidget(4, QtWidgets.QFormLayout.FieldRole, self.spinEpsilon)
        self.label_4 = QtWidgets.QLabel(Dialog)
        self.label_4.setObjectName("label_4")
        self.formLayout.setWidget(5, QtWidgets.QFormLayout.LabelRole, self.label_4)
        self.cbMethod = QtWidgets.QComboBox(Dialog)
        self.cbMethod.setObjectName("cbMethod")
        self.formLayout.setWidget(5, QtWidgets.QFormLayout.FieldRole, self.cbMethod)
        self.label_5 = QtWidgets.QLabel(Dialog)
        self.label_5.setObjectName("label_5")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label_5)
        self.cbView = QtWidgets.QComboBox(Dialog)
        self.cbView.setObjectName("cbView")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.cbView)

        self.retranslateUi(Dialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), Dialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QtWidgets.QApplication.translate("Dialog", "Clusterize", None, -1))
        self.label.setText(QtWidgets.QApplication.translate("Dialog", "Column name", None, -1))
        self.btColumnName.setToolTip(QtWidgets.QApplication.translate("Dialog", "Name of data column that will be created", None, -1))
        self.btColumnName.setText(QtWidgets.QApplication.translate("Dialog", "clusters", None, -1))
        self.label_2.setText(QtWidgets.QApplication.translate("Dialog", "Minimum cluster size", None, -1))
        self.spinMinClusterSize.setToolTip(QtWidgets.QApplication.translate("Dialog", "The minimum size of clusters; single linkage splits that contain fewer points than this will be considered points “falling out” of a cluster rather than a cluster splitting into two new clusters.", None, -1))
        self.chkMinSamples.setText(QtWidgets.QApplication.translate("Dialog", "Mininum samples", None, -1))
        self.spinMinSamples.setToolTip(QtWidgets.QApplication.translate("Dialog", "The number of samples in a neighbourhood for a point to be considered a core point.", None, -1))
        self.label_3.setText(QtWidgets.QApplication.translate("Dialog", "Cluster Selection Epsilon", None, -1))
        self.spinEpsilon.setToolTip(QtWidgets.QApplication.translate("Dialog", "A distance threshold. Clusters below this value will be merged.", None, -1))
        self.label_4.setText(QtWidgets.QApplication.translate("Dialog", "Cluster Selection Method", None, -1))
        self.cbMethod.setToolTip(QtWidgets.QApplication.translate("Dialog", "The method used to select clusters from the condensed tree. The standard approach for HDBSCAN* is to use an Excess of Mass algorithm to find the most persistent clusters. Alternatively you can instead select the clusters at the leaves of the tree – this provides the most fine grained and homogeneous clusters.", None, -1))
        self.label_5.setText(QtWidgets.QApplication.translate("Dialog", "Detect communities from", None, -1))

