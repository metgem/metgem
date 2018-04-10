#!/usr/bin/env python
from PyQt5.QtWidgets import QGroupBox
from PyQt5 import uic

import os

try:
    from ...workers import NetworkVisualizationOptions, TSNEVisualizationOptions, CosineComputationOptions
except ValueError:
    class NetworkVisualizationOptions:
        pass
        
    class TSNEVisualizationOptions:
        pass


class NetworkOptionsWidget(QGroupBox):
    """Create a widget containing Network visualization options"""
    
    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'network_options_widget.ui'), self)

    def getValues(self):
        options = NetworkVisualizationOptions()
        options.top_k = self.spinNetworkMaxNeighbor.value()
        options.pairs_min_cosine = self.spinNetworkMinScore.value()
        options.max_connected_nodes = self.spinNetworkMaxConnectedComponentSize.value()
        return options

    def setValues(self, options):
        """Modify Network visualization options

        Args: 
            network_visualization_options (NetworkVisualizationOptions): Modifies the Widget's 
            spinBoxes to match the Network visualization options.  
        """
        
        self.spinNetworkMaxNeighbor.setValue(options.top_k)
        self.spinNetworkMinScore.setValue(options.pairs_min_cosine)
        self.spinNetworkMaxConnectedComponentSize.setValue(options.max_connected_nodes)


class TSNEOptionsWidget(QGroupBox):
    """Create a widget containing t-SNE visualization options"""
    
    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'tsne_options_widget.ui'), self)

    def getValues(self):
        """Return t-SNE options"""
        
        options = TSNEVisualizationOptions()
        options.min_score = self.spinMinScore.value()
        options.perplexity = self.spinTSNEPerplexity.value()
        options.learning_rate = self.spinTSNELearningRate.value()
        options.early_exaggeration = self.spinTSNEEarlyExaggeration.value()
        options.barnes_hut = self.gbBarnesHut.isChecked()
        options.angle = self.spinAngle.value()
        options.random = self.chkRandomState.isChecked()
        
        return options

    def setValues(self, options):
        """Modify t-SNE perplexity and learning rate options

        Args: 
            t-SNE_visualization_options (TSNEVisualizationOptions): Modifies the Widget's spinBoxes
            to match the t-SNE visualization options.  
        """

        self.spinMinScore.setValue(options.min_score)
        self.spinTSNEPerplexity.setValue(options.perplexity)
        self.spinTSNELearningRate.setValue(options.learning_rate)
        self.spinTSNEEarlyExaggeration.setValue(options.early_exaggeration)
        self.gbBarnesHut.setChecked(options.barnes_hut)
        self.spinAngle.setValue(options.angle)
        self.chkRandomState.setChecked(options.random)


class CosineOptionsWidget(QGroupBox):
    """Create a widget containing Cosine computations options"""

    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'cosine_options_widget.ui'), self)

    def getValues(self):
        options = CosineComputationOptions()
        options.mz_tolerance = self.spinMZTolerance.value()
        options.min_intensity = self.spinMinIntensity.value()
        options.parent_filter_tolerance = self.spinParentFilterTolerance.value()
        options.min_matched_peaks = self.spinMinMatchedPeaks.value()
        
        return options

    def setValues(self, options):
        """Modify Cosine visualization options
        """

        self.spinMZTolerance.setValue(options.mz_tolerance)
        self.spinMinIntensity.setValue(options.min_intensity)
        self.spinParentFilterTolerance.setValue(options.parent_filter_tolerance)
        self.spinMinMatchedPeaks.setValue(options.min_matched_peaks)
