import os
import glob

from PyQt5.QtWidgets import QFileDialog, QDialog, QHBoxLayout
from PyQt5 import uic

if __name__ == '__main__':
    from widgets.options_widgets import TSNEOptionWidget, NetworkOptionWidget
else:
    from .widgets.options_widgets import TSNEOptionWidget, NetworkOptionWidget
         

class BaseOptionDialog(QDialog):
    def __init__(self, folder=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if self.__class__.__name__.startswith('EditTSNE'):
            self.option_widget = TSNEOptionWidget()
            layout = QHBoxLayout()
            layout.addWidget(self.option_widget)

            self.setLayout(layout) 
            self.resize(self.option_widget.sizeHint())

            # Set options values
            if self.parent():
                options = self.parent().tsne_visual_options
                self.option_widget.setValues(options)
                
        elif self.__class__.__name__.startswith('EditNetwork'):
            self.option_widget = TSNEOptionWidget()
            layout = QHBoxLayout()
            layout.addWidget(self.option_widget)

            self.setLayout(layout) 
            self.resize(self.option_widget.sizeHint())

            # Set options values
            if self.parent():
                options = self.parent().tsne_visual_options
                self.option_widget.setValues(options)
            

            
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
    dialog = EditTSNEOptionDialog(folder=os.path.realpath(os.path.dirname(__file__)))
    
    if dialog.exec_() == QDialog.Accepted:
        print('You chose these files:', dialog.getValues())
        
