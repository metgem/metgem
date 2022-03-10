from qtpy.QtWidgets import QDialog, QFormLayout, QLineEdit, QSpinBox, QDialogButtonBox


class TextItemInputDialog(QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle("Add/Edit Text Item")

        layout = QFormLayout()
        self.leText = QLineEdit()
        layout.addRow("Text", self.leText)
        self.spinFontSize = QSpinBox()
        self.spinFontSize.setMinimum(8)
        self.spinFontSize.setMaximum(1e6)
        self.spinFontSize.setValue(18)
        layout.addRow("Font Size", self.spinFontSize)

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        layout.addWidget(self.buttonBox)

        self.setLayout(layout)

    def getValues(self):
        return self.leText.text(), self.spinFontSize.value()

    def setValues(self, text, font_size):
        self.leText.setText(text)
        self.spinFontSize.setValue(font_size)
