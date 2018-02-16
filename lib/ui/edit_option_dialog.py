import os
import glob

from PyQt5.QtWidgets import QFileDialog, QDialog, QHBoxLayout
from qtpy import uic

from .widgets.options_widgets import tsneOptionWidget, networkOptionWidget

UI_FILE = os.path.join(os.path.dirname(__file__), 'edit_option_dialog.ui')

if __name__ == '__main__':
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    EditOptionDialogUi, EditOptionDialogBase = uic.loadUiType(UI_FILE)
else:
    EditOptionDialogUi, EditOptionDialogBase = uic.loadUiType(UI_FILE, from_imports='lib.ui', import_from='lib.ui')
         

            
class EditTSNEOptionDialog(EditOptionDialogBase, EditOptionDialogUi):
    """Creates a dialog to modify the TSNE options"""
    def __init__(self, *args, folder=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)
        
        # Add options widgets
        self.tsne_widget = tsneOptionWidget()
        hGrid = QHBoxLayout()
        hGrid.addWidget(self.tsne_widget)

        self.frameCentral.setLayout(hGrid) 
        self.resize(self.tsne_widget.sizeHint())

        # Set options values
        options = self.parent().tsne_visual_options
        self.tsne_widget.setValue(options)
        

class EditNetworkOptionDialog(EditOptionDialogBase, EditOptionDialogUi):
    """Creates a dialog to modify the Network options"""
    def __init__(self, *args, folder=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.setupUi(self)

        # Add options widgets
        self.network_widget = networkOptionWidget()
        hGrid = QHBoxLayout()
        hGrid.addWidget(self.network_widget)

        self.frameCentral.setLayout(hGrid)   
        self.resize(self.network_widget.sizeHint()) 

        # Set options values
        options = self.parent().network_visual_options
        self.network_widget.setValue(options)  
        
            
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    dialog = EditTSNEOptionDialog(folder=os.path.realpath(os.path.dirname(__file__)))
    
    if dialog.exec_() == QtWidgets.QDialog.Accepted:
        print('You chose these files:', dialog.getValues())
        