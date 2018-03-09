from PyQt5.QtWidgets import QDialog, QGridLayout, QDialogButtonBox, QSpinBox, QAbstractSpinBox
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
            for child in w.findChildren(QAbstractSpinBox):
                child.setReadOnly(True)
                child.setButtonSymbols(QSpinBox.NoButtons)
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
