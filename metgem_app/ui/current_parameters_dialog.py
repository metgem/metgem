from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QGridLayout, QDialogButtonBox, QSpinBox, QAbstractSpinBox, QAbstractButton, \
    QGroupBox

from metgem_app.ui.widgets import CosineOptionsWidget


class CurrentParametersDialog(QDialog):
    def __init__(self, *args, options=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.setWindowTitle('Current Parameters')
        self.setWindowFlags(Qt.Tool | Qt.CustomizeWindowHint | Qt.WindowCloseButtonHint)
        
        layout = QGridLayout()

        w = CosineOptionsWidget()
        opt = options.cosine

        # Set spin boxes readonly
        for child in w.findChildren(QAbstractSpinBox):
            child.setReadOnly(True)
            child.setButtonSymbols(QSpinBox.NoButtons)

        # Set buttons and checkboxes readonly
        for child in w.findChildren(QAbstractButton) + w.findChildren(QGroupBox):
            child.setAttribute(Qt.WA_TransparentForMouseEvents)
            child.setFocusPolicy(Qt.NoFocus)

        layout.addWidget(w)
        w.setValues(opt)
                
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Close)
        layout.addWidget(self.buttonBox)

        self.setLayout(layout)

        # Set Close button as default
        bt_close = self.buttonBox.button(QDialogButtonBox.Close)
        if bt_close is not None:
            bt_close.setDefault(True)

        self.buttonBox.rejected.connect(self.reject)
