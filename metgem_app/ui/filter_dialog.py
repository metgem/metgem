from PySide6.QtWidgets import (QFileDialog, QDialog,
                            QComboBox, QDoubleSpinBox, QMessageBox)
from PySide6.QtCore import Qt, QSettings

import pandas as pd

from .filter_dialog_ui import Ui_FilterDialog
from ..workers.core.filter import (FRAGMENTS, NEUTRAL_LOSSES, MZ_PARENT,
                                   ALL_CONDITIONS, AT_LEAST_ONE_CONDITION)

ALL_CONDITIONS_TEXT = "# Match all conditions"
AT_LEAST_ONE_CONDITION_TEXT = "# Match at least one condition"


class TypeComboBox(QComboBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.addItem("Fragment", FRAGMENTS)
        self.addItem("Neutral Loss", NEUTRAL_LOSSES)
        self.addItem("m/z parent", MZ_PARENT)


class ValueDoubleSpinBox(QDoubleSpinBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setDecimals(QSettings().value('Metadata/float_precision', 4, type=int))
        self.setMinimum(0)
        self.setMaximum(1000000)
        self.setValue(0.)


class ToleranceDoubleSpinBox(QDoubleSpinBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setDecimals(1)
        self.setMinimum(0)
        self.setMaximum(1000)
        self.setValue(5)


class UnitComboBox(QComboBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.addItem("ppm", "ppm")
        self.addItem("mDa", "mDa")


class FilterDialog(QDialog, Ui_FilterDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setupUi(self)
        self.setWindowFlags(Qt.Tool | Qt.CustomizeWindowHint | Qt.WindowCloseButtonHint)

        self.btAdd.clicked.connect(self.on_add)
        self.btRemove.clicked.connect(self.on_remove)
        self.btLoad.clicked.connect(self.on_load)
        self.btSave.clicked.connect(self.on_save)

        self.on_add()

    def on_add(self):
        self.tvValues.insertRow(self.tvValues.rowCount())
        type_combo = TypeComboBox()
        self.tvValues.setCellWidget(self.tvValues.rowCount()-1, 0, type_combo)
        self.tvValues.setCellWidget(self.tvValues.rowCount()-1, 1, ValueDoubleSpinBox())
        tolerance_spinbox = ToleranceDoubleSpinBox()
        self.tvValues.setCellWidget(self.tvValues.rowCount()-1, 2, tolerance_spinbox)
        unit_combo = UnitComboBox()
        self.tvValues.setCellWidget(self.tvValues.rowCount()-1, 3, unit_combo)

        def on_type_combo_current_index_changed(index):
            if index == FRAGMENTS:
                tolerance_spinbox.setValue(5.)
                unit_combo.setCurrentText("ppm")
            else:
                tolerance_spinbox.setValue(20.)
                unit_combo.setCurrentText("mDa")
        type_combo.currentIndexChanged.connect(on_type_combo_current_index_changed)

    def on_remove(self):
        selected_rows = {index.row() for index in self.tvValues.selectedIndexes()}
        for row in sorted(selected_rows)[::-1]:
            self.tvValues.removeRow(row)

    def on_load(self):
        filter_ = ["m/z Filter list (*.csv)"]
        filename, filter_ = QFileDialog.getOpenFileName(self, "Load m/z filter list",
                                                        filter=";;".join(filter_))
        if filename:
            self.tvValues.clearContents()
            try:
                condition_criterium = ALL_CONDITIONS
                with open(filename, 'r') as f:
                    first_line = f.readline().strip('\n')
                    if first_line == AT_LEAST_ONE_CONDITION_TEXT:
                        condition_criterium = AT_LEAST_ONE_CONDITION

                df = pd.read_csv(filename, comment='#')
                if condition_criterium == AT_LEAST_ONE_CONDITION:
                    self.radioAtLeastOneCondition.setChecked(True)
                else:
                    self.radioAllConditions.setChecked(True)
                self.tvValues.setRowCount(df.shape[0])

                for i, row in df.iterrows():
                    w = TypeComboBox()
                    w.setCurrentIndex(row[0])
                    self.tvValues.setCellWidget(i, 0, w)
                    w = ValueDoubleSpinBox()
                    w.setValue(row[1])
                    self.tvValues.setCellWidget(i, 1, w)
                    w = ToleranceDoubleSpinBox()
                    w.setValue(row[2])
                    self.tvValues.setCellWidget(i, 2, w)
                    w = UnitComboBox()
                    w.setCurrentText(row[3])
                    self.tvValues.setCellWidget(i, 3, w)
            except FileNotFoundError:
                QMessageBox.warning(self, None, "Selected file does not exists.")
            except IOError:
                QMessageBox.warning(self, None, "Load failed (I/O Error).")
            except IndexError:
                self.tvValues.clearContents()
                self.tvValues.setRowCount(0)
                QMessageBox.warning(self, None, "Unknown file format.")

    def on_save(self):
        filter_ = ["m/z Filter list (*.csv)"]
        filename, filter_ = QFileDialog.getSaveFileName(self, "Save m/z filter list",
                                                        filter=";;".join(filter_))
        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write(AT_LEAST_ONE_CONDITION_TEXT + "\n" if self.radioAtLeastOneCondition.isChecked()
                            else ALL_CONDITIONS_TEXT + "\n")
                    f.write(f"type,value,tolerance,unit\n")
                    for row in range(self.tvValues.rowCount()):
                        f.write(",".join([str(_) for _ in self.export_row(row)]) + "\n")
            except FileNotFoundError:
                QMessageBox.warning(self, None, "Selected file does not exists.")
            except IOError:
                QMessageBox.warning(self, None, "Save failed (I/O Error).")

    def export_row(self, row):
        return self.tvValues.cellWidget(row, 0).currentData(), \
               self.tvValues.cellWidget(row, 1).value(), \
               self.tvValues.cellWidget(row, 2).value(), \
               self.tvValues.cellWidget(row, 3).currentData()

    def getValues(self):
        return [self.export_row(row) for row in range(self.tvValues.rowCount())], \
               AT_LEAST_ONE_CONDITION if self.radioAtLeastOneCondition.isChecked() else ALL_CONDITIONS

