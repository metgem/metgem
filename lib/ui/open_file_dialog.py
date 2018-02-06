import os
import glob

from PyQt5.QtWidgets import QFileDialog, QDialog, QHBoxLayout
from qtpy import uic

from .widgets.options_widgets import tsneOptionWidget, networkOptionWidget

UI_FILE = os.path.join(os.path.dirname(__file__), 'open_file_dialog.ui')

if __name__ == '__main__':
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    
    OpenFileDialogUI, OpenFileDialogBase = uic.loadUiType(UI_FILE)
else:
    OpenFileDialogUI, OpenFileDialogBase = uic.loadUiType(UI_FILE, from_imports='lib.ui', import_from='lib.ui')
         

class TSNEOptions:
    min_score = None

class NetworkOptions:
    min_matching_peaks = None
    min_score = None
    mz_tolerance = None
    noise_reduction = None
    perform_library_search = False
    
            
class OpenFileDialog(OpenFileDialogBase, OpenFileDialogUI):

    def __init__(self, *args, folder=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.setupUi(self)
        
        # Add options widgets
        tsne_widget = tsneOptionWidget()
        network_widget = networkOptionWidget()
        hGrid = QHBoxLayout()
        hGrid.addWidget(network_widget)
        hGrid.addWidget(tsne_widget)

        self.advancedOptionsFrame.setLayout(hGrid)   

        self.display_advanced_options = False
        self.toggle_advanced_options()

        # Connect events
        self.btBrowseProcessFile.clicked.connect(lambda: self.browse('process'))
        self.btBrowseMetadataFile.clicked.connect(lambda: self.browse('metadata'))        
        self.btToggleAdvancedOptions.clicked.connect(self.toggle_advanced_options)

    
    def toggle_advanced_options(self):
         if self.display_advanced_options == False:
             self.advancedOptionsFrame.hide()
             self.display_advanced_options = True
             self.btToggleAdvancedOptions.setText("Show Advanced Options...")
         else:
             self.advancedOptionsFrame.show()
             self.display_advanced_options = False
             self.btToggleAdvancedOptions.setText("Hide Advanced Options...")
         self.adjustSize()  

        
    def browse(self, type='process'):
        dialog = QFileDialog(self)
        dialog.setOption(QFileDialog.ShowDirsOnly)
        if dialog.exec_() == QDialog.Accepted:
            filename = dialog.selectedFiles()[0]
            if type == 'process':
                self.editProcessFile.setText(filename)
            else:
                self.editMetadataFile.setText(filename)
        
        
    def getValues(self):
        tsne_options = TSNEOptions()
        """tsne_options.min_score = self.spinTSNEMinScore.value()
        
        network_options = NetworkOptions()
        network_options.min_matching_peaks = self.spinNetworkMinMatchingPeaks.value()
        network_options.min_score = self.spinNetworkMinScore.value()
        network_options.mz_tolerance = self.spinNetworkMzTolerance.value()
        network_options.noise_reduction = self.spinNoiseReduction.value()
        network_options.perform_library_search = self.chkLibrarySearch.isChecked()"""
        
        return (self.editProcessFile.text(), self.editMetadataFile.text())
            
            
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    dialog = OpenFileDialog(folder=os.path.realpath(os.path.dirname(__file__)))
    
    if dialog.exec_() == QtWidgets.QDialog.Accepted:
        print('You chose these files:', dialog.getValues())
        