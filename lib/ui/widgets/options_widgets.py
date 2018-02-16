#!/usr/bin/env python
from PyQt5 import QtWidgets, uic

class tsneOptionWidget(QtWidgets.QWidget):
	"""Create a widget containing TSNE visualization options"""
	def __init__(self):
		QtWidgets.QWidget.__init__(self)
		uic.loadUi('lib/ui/widgets/tsne_option_widget.ui', self)

	def getValues(self):
		"""Return TSNE perplexity and learning rate options as a tulpe"""
		perpexity = self.spinTSNEPerplexity.value()
		learning_rate = self.spinTSNELearningRate.value()
		return (perpexity, learning_rate)

	def setValue(self, tsne_visualization_options):
		"""Modify TSNE perplexity and learning rate options

		Args: 
			tsne_visualization_options (TSNEVisualizationOptions): Modifies the Widget's spinBoxes 
			to match the TSNE visualization options.  
		"""
		option = tsne_visualization_options
		self.spinTSNEPerplexity.setValue(option.PERPLEXITY)
		self.spinTSNELearningRate.setValue(option.LEARNING_RATE)


class networkOptionWidget(QtWidgets.QWidget):
	"""Create a widget containing Network visualization options"""
	def __init__(self):
		QtWidgets.QWidget.__init__(self)
		uic.loadUi('lib/ui/widgets/network_option_widget.ui', self)

	def getValues(self):
		"""Return Network max_neighbor, min_score and max_connected_nodes options as a tulpe"""
		max_neighbor = self.spinNetworkMaxNeighbor.value() # max_neighbor = TOPK
		min_score = self.spinNetworkMinScore.value()
		max_connected_nodes = self.spinNetworkMaxConnectedComponentSize.value()
		return (max_neighbor, min_score, max_connected_nodes)

	def setValue(self, network_visualization_options):
		"""Modify Network visualization options

		Args: 
			network_visualization_options (NetworkVisualizationOptions): Modifies the Widget's 
			spinBoxes to match the Network visualization options.  
		"""
		option = network_visualization_options
		self.spinNetworkMaxNeighbor.setValue(option.TOPK)
		self.spinNetworkMinScore.setValue(option.PAIRS_MIN_COSINE)
		self.spinNetworkMaxConnectedComponentSize.setValue(option.MAXIMUM_CONNECTED_NODES)
		