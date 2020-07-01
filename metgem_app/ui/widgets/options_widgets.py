import os

from PyQt5 import uic
from PyQt5.QtWidgets import QGroupBox

from ...workers.cosine import CosineComputationOptions
from ...workers.databases.query import QueryDatabasesOptions
from ...workers.embedding.isomap import IsomapVisualizationOptions
from ...workers.embedding.mds import MDSVisualizationOptions
from ...workers.embedding.phate import PHATEVisualizationOptions
from ...workers.embedding.tsne import TSNEVisualizationOptions
from ...workers.embedding.umap import UMAPVisualizationOptions
from ...workers.network_generation import NetworkVisualizationOptions


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
            options (NetworkVisualizationOptions): Modifies the Widget's
            spinBoxes to match the Network visualization options.  
        """
        
        self.spinNetworkMaxNeighbor.setValue(options.top_k)
        self.spinNetworkMinScore.setValue(options.pairs_min_cosine)
        self.spinNetworkMaxConnectedComponentSize.setValue(options.max_connected_nodes)


class CosineOptionsWidget(QGroupBox):
    """Create a widget containing Cosine computations options"""

    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'cosine_options_widget.ui'), self)
        self.chkUseParentFiltering.stateChanged.connect(self.spinParentFilterTolerance.setEnabled)
        self.chkUseMinIntensityFiltering.stateChanged.connect(self.spinMinIntensity.setEnabled)
        self.chkUseWindowRankFiltering.stateChanged.connect(self.spinMinMatchedPeaksSearch.setEnabled)
        self.chkUseWindowRankFiltering.stateChanged.connect(self.spinMatchedPeaksWindow.setEnabled)

    def getValues(self):
        options = CosineComputationOptions()
        options.mz_tolerance = self.spinMZTolerance.value()
        options.min_matched_peaks = self.spinMinMatchedPeaks.value()
        options.parent_filter_tolerance = self.spinParentFilterTolerance.value()
        options.min_intensity = self.spinMinIntensity.value()
        options.min_matched_peaks_search = self.spinMinMatchedPeaksSearch.value()
        options.matched_peaks_window = self.spinMatchedPeaksWindow.value()
        options.is_ms1_data = self.chkMS1Data.isChecked()
        options.use_filtering = self.gbFiltering.isChecked()
        options.use_min_intensity_filter = self.chkUseMinIntensityFiltering.isChecked()
        options.use_parent_filter = self.chkUseParentFiltering.isChecked()
        options.use_window_rank_filter = self.chkUseWindowRankFiltering.isChecked()
        
        return options

    def setValues(self, options):
        self.spinMZTolerance.setValue(options.mz_tolerance)
        self.spinMinMatchedPeaks.setValue(options.min_matched_peaks)
        self.spinParentFilterTolerance.setValue(options.parent_filter_tolerance)
        self.spinMinIntensity.setValue(options.min_intensity)
        self.spinMinMatchedPeaksSearch.setValue(options.min_matched_peaks_search)
        self.spinMatchedPeaksWindow.setValue(options.matched_peaks_window)
        self.chkMS1Data.setChecked(options.is_ms1_data)
        self.gbFiltering.setChecked(options.use_filtering)
        self.chkUseMinIntensityFiltering.setChecked(options.use_min_intensity_filter)
        self.chkUseParentFiltering.setChecked(options.use_parent_filter)
        self.chkUseWindowRankFiltering.setChecked(options.use_window_rank_filter)


class TSNEOptionsWidget(QGroupBox):
    """Create a widget containing t-SNE visualization options"""

    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'tsne_options_widget.ui'), self)

    def getValues(self):
        """Return t-SNE options"""

        options = TSNEVisualizationOptions()
        options.min_score = self.spinMinScore.value()
        options.min_scores_above_threshold = self.spinMinScoresAboveThreshold.value()
        options.n_iter = self.spinNumIterations.value()
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
        self.spinMinScoresAboveThreshold.setValue(options.min_scores_above_threshold)
        self.spinNumIterations.setValue(options.n_iter)
        self.spinTSNEPerplexity.setValue(options.perplexity)
        self.spinTSNELearningRate.setValue(options.learning_rate)
        self.spinTSNEEarlyExaggeration.setValue(options.early_exaggeration)
        self.gbBarnesHut.setChecked(options.barnes_hut)
        self.spinAngle.setValue(options.angle)
        self.chkRandomState.setChecked(options.random)


class UMAPOptionsWidget(QGroupBox):
    """Create a widget containing UMAP visualization options"""

    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'umap_options_widget.ui'), self)
        self.cbNumIterations.stateChanged.connect(self.spinNumIterations.setEnabled)

    def getValues(self):
        """Return UMAP options"""

        options = UMAPVisualizationOptions()
        options.min_score = self.spinMinScore.value()
        options.min_scores_above_threshold = self.spinMinScoresAboveThreshold.value()
        options.n_epochs = self.spinNumIterations.value() if self.cbNumIterations.isChecked() else None
        options.min_dist = self.spinMinDist.value()
        options.random = self.chkRandomState.isChecked()

        return options

    def setValues(self, options):
        self.spinMinScore.setValue(options.min_score)
        self.spinMinScoresAboveThreshold.setValue(options.min_scores_above_threshold)
        if options.n_epochs is not None:
            self.spinNumIterations.setValue(options.n_epochs)
            self.cbNumbIterations.setChecked(True)
            self.spinNumIterations.setEnabled(True)
        else:
            self.cbNumIterations.setChecked(False)
            self.spinNumIterations.setEnabled(False)
        self.spinMinDist.setValue(options.min_dist)
        self.chkRandomState.setChecked(options.random)


class MDSOptionsWidget(QGroupBox):
    """Create a widget containing MDS visualization options"""

    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'mds_options_widget.ui'), self)

    def getValues(self):
        options = MDSVisualizationOptions()
        options.min_score = self.spinMinScore.value()
        options.min_scores_above_threshold = self.spinMinScoresAboveThreshold.value()
        options.max_iter = self.spinNumIterations.value()
        options.random = self.chkRandomState.isChecked()

        return options

    def setValues(self, options):
        self.spinMinScore.setValue(options.min_score)
        self.spinMinScoresAboveThreshold.setValue(options.min_scores_above_threshold)
        self.spinNumIterations.setValue(options.max_iter)
        self.chkRandomState.setChecked(options.random)


class IsomapOptionsWidget(QGroupBox):
    """Create a widget containing Isomap visualization options"""

    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'isomap_options_widget.ui'), self)

    def getValues(self):
        options = IsomapVisualizationOptions()
        options.min_score = self.spinMinScore.value()
        options.min_scores_above_threshold = self.spinMinScoresAboveThreshold.value()
        options.max_iter = self.spinNumIterations.value()
        options.n_neighbors = self.spinNumNeighbors.value()

        return options

    def setValues(self, options):
        self.spinMinScore.setValue(options.min_score)
        self.spinMinScoresAboveThreshold.setValue(options.min_scores_above_threshold)
        self.spinNumIterations.setValue(options.max_iter)
        self.spinNumNeighbors.setValue(options.n_neighbors)


class PHATEOptionsWidget(QGroupBox):
    """Create a widget containing PHATE visualization options"""

    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'phate_options_widget.ui'), self)

    def getValues(self):
        """Return PHATE options"""

        options = PHATEVisualizationOptions()
        options.min_score = self.spinMinScore.value()
        options.min_scores_above_threshold = self.spinMinScoresAboveThreshold.value()
        options.knn = self.spinKnn.value()
        options.decay = self.spinDecay.value()
        options.gamma = self.spinGamma.value()
        options.random = self.chkRandomState.isChecked()

        return options

    def setValues(self, options):
        self.spinMinScore.setValue(options.min_score)
        self.spinMinScoresAboveThreshold.setValue(options.min_scores_above_threshold)
        self.spinKnn.setValue(options.knn)
        self.spinDecay.setValue(options.decay)
        self.spinGamma.setValue(options.gamma)
        self.chkRandomState.setChecked(options.random)


class QueryDatabasesOptionsWidget(QGroupBox):
    """Create a widget containing Database query options"""

    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'databases_options_widget.ui'), self)

        # Populate polarity combobox
        self.cbPolarity.addItems(['Positive', 'Negative'])
        self.cbPolarity.setCurrentIndex(0)

    def getValues(self):
        options = QueryDatabasesOptions()
        options.mz_tolerance = self.spinMZTolerance.value()
        options.min_intensity = self.spinMinIntensity.value()
        options.parent_filter_tolerance = self.spinParentFilterTolerance.value()
        options.min_matched_peaks = self.spinMinMatchedPeaks.value()
        options.min_cosine = self.spinMinScore.value()
        options.analog_search = self.gbAnalogs.isChecked()
        options.analog_mz_tolerance = self.spinAnalogTolerance.value()
        options.positive_polarity = (self.cbPolarity.currentIndex() == 0)

        return options

    def setValues(self, options):
        self.spinMZTolerance.setValue(options.mz_tolerance)
        self.spinMinIntensity.setValue(options.min_intensity)
        self.spinParentFilterTolerance.setValue(options.parent_filter_tolerance)
        self.spinMinMatchedPeaks.setValue(options.min_matched_peaks)
        self.spinMinScore.setValue(options.min_cosine)
        self.gbAnalogs.setChecked(options.analog_search)
        self.spinAnalogTolerance.setValue(options.analog_mz_tolerance)
        self.cbPolarity.setCurrentIndex(0 if options.positive_polarity else 1)
