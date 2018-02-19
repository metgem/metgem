#!/usr/bin/env python
from PyQt5.QtWidgets import QGroupBox
from PyQt5 import uic

import os

try:
    from ...workers import NetworkVisualizationOptions, TSNEVisualizationOptions
except ValueError:
    class NetworkVisualizationOptions:
        pass
        
    class TSNEVisualizationOptions:
        pass


class NetworkOptionWidget(QGroupBox):
    """Create a widget containing Network visualization options"""
    
    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'network_option_widget.ui'), self)
        

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

        
class TSNEOptionWidget(QGroupBox):
    """Create a widget containing TSNE visualization options"""
    
    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'tsne_option_widget.ui'), self)


    def getValues(self):
        """Return TSNE perplexity and learning rate options as a tulpe"""
        options = TSNEVisualizationOptions()
        options.perplexity = self.spinTSNEPerplexity.value()
        options.learning_rate = self.spinTSNELearningRate.value()
        return options


    def setValues(self, options):
        """Modify TSNE perplexity and learning rate options

        Args: 
            tsne_visualization_options (TSNEVisualizationOptions): Modifies the Widget's spinBoxes 
            to match the TSNE visualization options.  
        """
        
        self.spinTSNEPerplexity.setValue(options.perplexity)
        self.spinTSNELearningRate.setValue(options.learning_rate)