from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QVBoxLayout, QDialogButtonBox

from metgem.ui.widgets import (TSNEOptionsWidget, ForceDirectedOptionsWidget, MDSOptionsWidget,
                               UMAPOptionsWidget, IsomapOptionsWidget, PHATEOptionsWidget)


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
                
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        layout.addWidget(self.buttonBox)
        self.setLayout(layout) 
        self.resize(self.options_widget.sizeHint())
        
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

    def getValues(self):
        return self.options_widget.getValues()


class EditForceDirectedOptionsDialog(EditOptionsDialogBase):
    """Dialog to modify the Force Directed options"""
    
    options_class = ForceDirectedOptionsWidget


class EditTSNEOptionsDialog(EditOptionsDialogBase):
    """Dialog to modify the t-SNE options"""

    options_class = TSNEOptionsWidget


class EditMDSOptionsDialog(EditOptionsDialogBase):
    """Dialog to modify the MDS options"""

    options_class = MDSOptionsWidget


class EditUMAPOptionsDialog(EditOptionsDialogBase):
    """Dialog to modify the UMAP options"""

    options_class = UMAPOptionsWidget


class EditIsomapOptionsDialog(EditOptionsDialogBase):
    """Dialog to modify the Isomap options"""

    options_class = IsomapOptionsWidget


class EditPHATEOptionsDialog(EditOptionsDialogBase):
    """Dialog to modify the PHATE options"""

    options_class = PHATEOptionsWidget
