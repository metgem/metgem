#!/usr/bin/env python
from PyQt5.QtWidgets import QGroupBox
from PyQt5 import uic

import os

class TSNEOptionWidget(QGroupBox):
    """Create a widget containing TSNE visualization options"""
    
    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'tsne_option_widget.ui'), self)


    def getValues(self):
        """Return TSNE perplexity and learning rate options as a tulpe"""
        perplexity = self.spinTSNEPerplexity.value()
        learning_rate = self.spinTSNELearningRate.value()
        return perplexity, learning_rate


    def setValues(self, options):
        """Modify TSNE perplexity and learning rate options

        Args: 
            tsne_visualization_options (TSNEVisualizationOptions): Modifies the Widget's spinBoxes 
            to match the TSNE visualization options.  
        """
        
        self.spinTSNEPerplexity.setValue(options.perplexity)
        self.spinTSNELearningRate.setValue(options.learning_rate)


class NetworkOptionWidget(QGroupBox):
    """Create a widget containing Network visualization options"""
    
    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'network_option_widget.ui'), self)
        

    def getValues(self):
        """Return Network max_neighbor, min_score and max_connected_nodes options as a tulpe"""
        max_neighbor = self.spinNetworkMaxNeighbor.value() # max_neighbor = top_k
        min_score = self.spinNetworkMinScore.value()
        max_connected_nodes = self.spinNetworkMaxConnectedComponentSize.value()
        return max_neighbor, min_score, max_connected_nodes
    

    def setValues(self, options):
        """Modify Network visualization options

        Args: 
            network_visualization_options (NetworkVisualizationOptions): Modifies the Widget's 
            spinBoxes to match the Network visualization options.  
        """
        
        self.spinNetworkMaxNeighbor.setValue(options.top_k)
        self.spinNetworkMinScore.setValue(options.pairs_min_cosine)
        self.spinNetworkMaxConnectedComponentSize.setValue(options.max_connected_nodes)
