import os
import glob

from PyQt5.QtWidgets import QFileDialog, QDialog, QVBoxLayout, QDialogButtonBox
from PyQt5 import uic

UI_FILE = os.path.join(os.path.dirname(__file__), 'open_file_dialog.ui')

if __name__ == '__main__':
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    
    OpenFileDialogUI, OpenFileDialogBase = uic.loadUiType(UI_FILE)
    from widgets.options_widgets import TSNEOptionWidget, NetworkOptionWidget
else:
    OpenFileDialogUI, OpenFileDialogBase = uic.loadUiType(UI_FILE, from_imports='lib.ui', import_from='lib.ui')
    from .widgets.options_widgets import TSNEOptionWidget, NetworkOptionWidget
    
            
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

    def __init__(self, *args, folder=None, options=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.setupUi(self)
        
        # Add advanced option button
        self.btMore = self.buttonBox.addButton("&More", QDialogButtonBox.ActionRole)
        
        # Add options widgets
        self.tsne_widget = TSNEOptionWidget()
        self.network_widget = NetworkOptionWidget()
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.network_widget)
        layout.addWidget(self.tsne_widget)

        if options:
            self.tsne_widget.setValues(options.tsne)
            self.network_widget.setValues(options.network)

        self.wgAdvancedOptions.setLayout(layout)

        # Connect events
        self.btBrowseProcessFile.clicked.connect(lambda: self.browse('process'))
        self.btBrowseMetadataFile.clicked.connect(lambda: self.browse('metadata'))        
        self.btMore.clicked.connect(self.toggle_advanced_options)
        
        
    def showEvent(self, event):
        self.wgAdvancedOptions.hide()
        self.adjustSize()

    
    def toggle_advanced_options(self):
        """Toggle the Network and TSNE parameters widgets"""
        
        if self.wgAdvancedOptions.isVisible():
             self.wgAdvancedOptions.hide()
             self.btMore.setText("&More")
        else:
             self.wgAdvancedOptions.show()
             self.btMore.setText("&Less")
             
        self.adjustSize()  

        
    def browse(self, type='process'):
        """Open a dialog to file either .mgf or metadata.txt file"""
        
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
        """Returns files to process and options"""
        
        cosine_computation_options = self.getComputeOptions()
        return self.editProcessFile.text(), self.editMetadataFile.text(), \
                cosine_computation_options, self.tsne_widget.getValues(), \
                self.network_widget.getValues()
        

    def getComputeOptions(self):
        """Returns cosine computation options values from the widget"""
        
        mz_tolerance = self.spinMZTolerance.value()
        min_intensity = self.spinMinIntensity.value()
        parent_filter_tolerance = self.spinParentFilterTolerance.value()
        min_matched_peaks = self.spinMinMatchedPeaks.value()
        return mz_tolerance, min_intensity, parent_filter_tolerance, min_matched_peaks
            
            
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    dialog = OpenFileDialog(folder=os.path.realpath(os.path.dirname(__file__)))
    
    if dialog.exec_() == QDialog.Accepted:
        print('You chose these files:', dialog.getValues())
        
