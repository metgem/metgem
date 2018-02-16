import os
import glob

from PyQt5.QtWidgets import QFileDialog, QDialog
from qtpy import uic

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
        
        # Connect events
        self.btBrowseProcessFile.clicked.connect(lambda: self.browse('process'))
        self.btBrowseMetadataFile.clicked.connect(lambda: self.browse('metadata'))        
        
        
    def browse(self, type='process'):
        dialog = QFileDialog(self)
        #dialog.setOption(QFileDialog.ShowDirsOnly)
        if type == 'process':
            dialog.setNameFilters(["MGF Files (*.mgf)", "All files (*.*)"])
        if dialog.exec_() == QDialog.Accepted:
            filename = dialog.selectedFiles()[0]
            if type == 'process':
                self.editProcessFile.setText(filename)
            else:
                self.editMetadataFile.setText(filename)
        
        
    def getValues(self):
        tsne_options = TSNEOptions()
        tsne_options.min_score = self.spinTSNEMinScore.value()
        
        network_options = NetworkOptions()
        network_options.min_matching_peaks = self.spinNetworkMinMatchingPeaks.value()
        network_options.min_score = self.spinNetworkMinScore.value()
        network_options.mz_tolerance = self.spinNetworkMzTolerance.value()
        network_options.noise_reduction = self.spinNoiseReduction.value()
        network_options.perform_library_search = self.chkLibrarySearch.isChecked()
        
        return (self.editProcessFile.text(), self.editMetadataFile.text(),
                tsne_options, network_options)
            
            
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    dialog = OpenFileDialog(folder=os.path.realpath(os.path.dirname(__file__)))
    
    if dialog.exec_() == QtWidgets.QDialog.Accepted:
        print('You chose these files:', dialog.getValues())
        
