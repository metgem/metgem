from PyQt5.QtWidgets import QDialog, QGridLayout, QDialogButtonBox, QSpinBox, QAbstractSpinBox, QAbstractButton, \
    QGroupBox, QWidget, QLayout
from PyQt5.QtCore import Qt

from .widgets import TSNEOptionsWidget, NetworkOptionsWidget, CosineOptionsWidget
         

class CurrentParametersDialog(QDialog):
    def __init__(self, *args, options=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.setWindowTitle('Current Parameters')
        self.setWindowFlags(Qt.Tool | Qt.CustomizeWindowHint | Qt.WindowCloseButtonHint)
        
        layout = QGridLayout()

        for w, opt in ((CosineOptionsWidget(), options.cosine),
                       (NetworkOptionsWidget(), options.network),
                       (TSNEOptionsWidget(), options.tsne)):
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
        btClose = self.buttonBox.button(QDialogButtonBox.Close)
        if btClose is not None:
            btClose.setDefault(True)

        self.buttonBox.rejected.connect(self.reject)
