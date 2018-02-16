import os
import glob

from PyQt5.QtWidgets import QFileDialog, QDialog, QVBoxLayout, QDialogButtonBox
from PyQt5 import uic

if __name__ == '__main__':
    from widgets.options_widgets import TSNEOptionWidget, NetworkOptionWidget
else:
    from .widgets.options_widgets import TSNEOptionWidget, NetworkOptionWidget
         

class BaseOptionDialog(QDialog):
    def __init__(self, *args, options=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.setWindowTitle('Options')
        
        layout = QVBoxLayout()   
        
        if self.__class__.__name__.startswith('EditTSNE'):
            self.option_widget = TSNEOptionWidget()
            layout.addWidget(self.option_widget)

            # Set options values
            if options:
                self.option_widget.setValues(options.tsne)
                
        elif self.__class__.__name__.startswith('EditNetwork'):
            self.option_widget = NetworkOptionWidget()
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
            

            
class EditTSNEOptionDialog(BaseOptionDialog):
    """Dialog to modify the TSNE options"""
    
    pass


class EditNetworkOptionDialog(BaseOptionDialog):
    """Dialog to modify the Network options"""
    
    pass
        
            
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    dialog = EditTSNEOptionDialog()
    
    if dialog.exec_() == QDialog.Accepted:
        print('You chose these files:', dialog.getValues())
        
