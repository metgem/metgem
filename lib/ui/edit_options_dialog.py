from .widgets import (TSNEOptionsWidget, NetworkOptionsWidget, MDSOptionsWidget,
                      UMAPOptionsWidget, IsomapOptionsWidget)
from ..workers import HAS_UMAP

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QDialogButtonBox
from PyQt5.QtCore import Qt
         

class EditOptionsDialogBase(QDialog):
    options_class = None

    def __init__(self, *args, options=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.setWindowTitle('Options')
        self.setWindowFlags(Qt.Tool | Qt.CustomizeWindowHint | Qt.WindowCloseButtonHint)
        
        layout = QVBoxLayout()   

        if self.options_class is not None:
            self.options_widget = self.options_class()
            layout.addWidget(self.options_widget)

            # Set options values
            if options:
                self.options_widget.setValues(options)
                
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(self.buttonBox)
        self.setLayout(layout) 
        self.resize(self.options_widget.sizeHint())
        
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

    def getValues(self):
        return self.options_widget.getValues()


class EditNetworkOptionsDialog(EditOptionsDialogBase):
    """Dialog to modify the Network options"""
    
    options_class = NetworkOptionsWidget


class EditTSNEOptionsDialog(EditOptionsDialogBase):
    """Dialog to modify the t-SNE options"""

    options_class = TSNEOptionsWidget


class EditMDSOptionsDialog(EditOptionsDialogBase):
    """Dialog to modify the MDS options"""

    options_class = MDSOptionsWidget


if HAS_UMAP:
    class EditUMAPOptionsDialog(EditOptionsDialogBase):
        """Dialog to modify the UMAP options"""

        options_class = UMAPOptionsWidget


class EditIsomapOptionsDialog(EditOptionsDialogBase):
    """Dialog to modify the Isomap options"""

    options_class = IsomapOptionsWidget
