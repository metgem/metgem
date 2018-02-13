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
         

"""class TSNEOptions:
    min_score = None

class NetworkOptions:
    min_matching_peaks = None
    min_score = None
    mz_tolerance = None
    noise_reduction = None
    perform_library_search = False"""
    
            
class OpenFileDialog(OpenFileDialogBase, OpenFileDialogUI):
    """Create and open a dialog to process a new .mgf file.

    Creates a dialog containing 4 widgets:
        -file opening widget: to select a .mgf file to process and a .txt meta data file
        -CosineComputationOptions containing widget: to modify the cosine computation parameters
        -NetworkVisualizationOptions containing widget: to modify the Network visualization parameters
        -TSNEVisualizationOptions containing widget: to modify the TSNE visualization parameters

    If validated:   - the entered parameters are selected as default values for the next actions.
                    - the cosine score computing is started
                    - upon cosine score computation validation, Network and TSNE vilsualizations are created

    """

    def __init__(self, *args, folder=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.setupUi(self)
        
        # Add options widgets
        self.tsne_widget = tsneOptionWidget()
        self.network_widget = networkOptionWidget()
        hGrid = QHBoxLayout()
        hGrid.addWidget(self.network_widget)
        hGrid.addWidget(self.tsne_widget)

        tsne_options = self.parent().tsne_visual_options
        self.tsne_widget.setValue(tsne_options)

        network_options = self.parent().network_visual_options
        self.network_widget.setValue(network_options)

        self.advancedOptionsFrame.setLayout(hGrid)   

        self.display_advanced_options = False
        self.toggle_advanced_options()

        # Connect events
        self.btBrowseProcessFile.clicked.connect(lambda: self.browse('process'))
        self.btBrowseMetadataFile.clicked.connect(lambda: self.browse('metadata'))        
        self.btToggleAdvancedOptions.clicked.connect(self.toggle_advanced_options)

    
    def toggle_advanced_options(self):
        """Toggle the Network and TSNE parameters widgets"""
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
        """Open a dialog to file either .mgf or metadata.txt file"""
        dialog = QFileDialog(self)
        dialog.setOption(QFileDialog.ShowDirsOnly)
        if dialog.exec_() == QDialog.Accepted:
            filename = dialog.selectedFiles()[0]
            if type == 'process':
                self.editProcessFile.setText(filename)
            else:
                self.editMetadataFile.setText(filename)
        
        
    def getValues(self):
        """Returns Cosine Computation parameters and files to process"""
        cosine_computation_options = self.getComputeOptions()
        return (self.editProcessFile.text(), self.editMetadataFile.text(), cosine_computation_options)
        

    def getComputeOptions(self):
        """Returns cosine computation options values from the widget"""
        mz_tolerance = self.spinMZTolerance.value()
        min_intensity = self.spinMinIntensity.value()
        parent_filter_tolerance = self.spinParentFilterTolerance.value()
        min_matched_peaks = self.spinMinMatchedPeaks.value()
        return (mz_tolerance, min_intensity, parent_filter_tolerance, min_matched_peaks)
            
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    dialog = OpenFileDialog(folder=os.path.realpath(os.path.dirname(__file__)))
    
    if dialog.exec_() == QtWidgets.QDialog.Accepted:
        print('You chose these files:', dialog.getValues())
        