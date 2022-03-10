# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'E:\git\metgem\metgem_app\ui\widgets\spectrum\fragments_list.ui',
# licensing of 'E:\git\metgem\metgem_app\ui\widgets\spectrum\fragments_list.ui' applies.
#
# Created: Sat Mar  5 14:43:10 2022
#      by: pyside2-uic  running on PySide2 5.13.2
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(400, 300)
        self.verticalLayout = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtWidgets.QLabel(Form)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.twFragments = QtWidgets.QTableWidget(Form)
        self.twFragments.setAlternatingRowColors(True)
        self.twFragments.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.twFragments.setColumnCount(3)
        self.twFragments.setObjectName("twFragments")
        self.twFragments.setColumnCount(3)
        self.twFragments.setRowCount(0)
        self.twFragments.horizontalHeader().setVisible(False)
        self.twFragments.verticalHeader().setVisible(False)
        self.verticalLayout.addWidget(self.twFragments)
        self.label_2 = QtWidgets.QLabel(Form)
        self.label_2.setObjectName("label_2")
        self.verticalLayout.addWidget(self.label_2)
        self.twNeutralLosses = QtWidgets.QTableWidget(Form)
        self.twNeutralLosses.setAlternatingRowColors(True)
        self.twNeutralLosses.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.twNeutralLosses.setColumnCount(3)
        self.twNeutralLosses.setObjectName("twNeutralLosses")
        self.twNeutralLosses.setColumnCount(3)
        self.twNeutralLosses.setRowCount(0)
        self.twNeutralLosses.horizontalHeader().setVisible(False)
        self.twNeutralLosses.verticalHeader().setVisible(False)
        self.verticalLayout.addWidget(self.twNeutralLosses)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(QtWidgets.QApplication.translate("Form", "Form", None, -1))
        self.label.setText(QtWidgets.QApplication.translate("Form", "Matching fragments", None, -1))
        self.twFragments.setSortingEnabled(True)
        self.label_2.setText(QtWidgets.QApplication.translate("Form", "Matching neutral losses", None, -1))
        self.twNeutralLosses.setSortingEnabled(True)

