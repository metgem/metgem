from PyQt5.QtWidgets import QDialog, QVBoxLayout, QDialogButtonBox
from PyQt5.QtCore import Qt

if __name__ == '__main__':
    from widgets import TSNEOptionsWidget, NetworkOptionsWidget
else:
    from .widgets import TSNEOptionsWidget, NetworkOptionsWidget
         

class EditOptionsDialogBase(QDialog):
    def __init__(self, *args, options=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.setWindowTitle('Options')
        self.setWindowFlags(Qt.Tool | Qt.CustomizeWindowHint | Qt.WindowCloseButtonHint)
        
        layout = QVBoxLayout()   
        
        if self.__class__.__name__.startswith('EditTSNE'):
            self.option_widget = TSNEOptionsWidget()
            layout.addWidget(self.option_widget)

            # Set options values
            if options:
                self.option_widget.setValues(options.tsne)
                
        elif self.__class__.__name__.startswith('EditNetwork'):
            self.option_widget = NetworkOptionsWidget()
            layout.addWidget(self.option_widget)

            # Set options values
            if options:
                self.option_widget.setValues(options.network)
                
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(self.buttonBox)
        self.setLayout(layout) 
        self.resize(self.option_widget.sizeHint())
        
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

    def getValues(self):
        return self.option_widget.getValues()

            
class EditTSNEOptionsDialog(EditOptionsDialogBase):
    """Dialog to modify the t-SNE options"""
    
    pass


class EditNetworkOptionsDialog(EditOptionsDialogBase):
    """Dialog to modify the Network options"""
    
    pass
        
            
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    dialog = EditTSNEOptionsDialog()
    
    if dialog.exec_() == QDialog.Accepted:
        print('You chose these files:', dialog.getValues())
