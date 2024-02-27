from PySide6.QtWidgets import QGroupBox, QWidget

from metgem.workers.options import (ForceDirectedVisualizationOptions,
                                    TSNEVisualizationOptions,
                                    UMAPVisualizationOptions,
                                    MDSVisualizationOptions,
                                    IsomapVisualizationOptions,
                                    PHATEVisualizationOptions,
                                    CosineComputationOptions,
                                    QueryDatabasesOptions,
                                    )

from metgem.ui.widgets.force_directed_options_widget_ui import Ui_ForceDirectedOptionsWidget
from metgem.ui.widgets.tsne_options_widget_ui import Ui_TSNEOptionsWidget
from metgem.ui.widgets.umap_options_widget_ui import Ui_UMAPOptionsWidget
from metgem.ui.widgets.mds_options_widget_ui import Ui_MDSOptionsWidget
from metgem.ui.widgets.isomap_options_widget_ui import Ui_IsomapOptionsWidget
from metgem.ui.widgets.phate_options_widget_ui import Ui_PHATEOptionsWidget
from metgem.ui.widgets.cosine_options_widget_ui import Ui_gbCosineOptions
from metgem.ui.widgets.databases_options_widget_ui import Ui_gbDatabaseOptions


class OptionsWidgetMixin:
    options_class = None

    def __init__(self):
        super().__init__()
        self.setupUi(self)

    def getValues(self):
        return self.options_class()

    def setValues(self, options):
        pass


class VisualizationOptionsWidget(OptionsWidgetMixin, QWidget):
    def getValues(self):
        options = super().getValues()
        options.title = self.editTitle.text() if self.editTitle.text() else None
        return options

    def setValues(self, options):
        super().setValues(options)
        self.editTitle.setText(options.title)


class OptionsGroupBox(OptionsWidgetMixin, QGroupBox):
    pass


class ForceDirectedOptionsWidget(VisualizationOptionsWidget, Ui_ForceDirectedOptionsWidget):
    """Create a widget containing Force Directed visualization options"""

    options_class = ForceDirectedVisualizationOptions

    def getValues(self):
        options = super().getValues()
        options.top_k = self.spinForceDirectedMaxNeighbor.value()
        options.pairs_min_cosine = self.spinForceDirectedMinScore.value()
        options.max_connected_nodes = self.spinForceDirectedMaxConnectedComponentSize.value()
        options.scale = self.spinForceDirectedScale.value()
        options.gravity = self.spinForceDirectedGravity.value()
        return options

    def setValues(self, options):
        """Modify Force Directed visualization options

        Args: 
            options (ForceDirectedVisualizationOptions): Modifies the Widget's
            spinBoxes to match the Force Directed visualization options.
        """

        super().setValues(options)
        self.spinForceDirectedMaxNeighbor.setValue(options.top_k)
        self.spinForceDirectedMinScore.setValue(options.pairs_min_cosine)
        self.spinForceDirectedMaxConnectedComponentSize.setValue(options.max_connected_nodes)
        self.spinForceDirectedScale.setValue(options.scale)
        self.spinForceDirectedGravity.setValue(options.gravity)


class TSNEOptionsWidget(VisualizationOptionsWidget, Ui_TSNEOptionsWidget):
    """Create a widget containing t-SNE visualization options"""

    options_class = TSNEVisualizationOptions

    def getValues(self):
        """Return t-SNE options"""

        options = super().getValues()
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

        super().setValues(options)
        self.spinMinScore.setValue(options.min_score)
        self.spinMinScoresAboveThreshold.setValue(options.min_scores_above_threshold)
        self.spinNumIterations.setValue(options.n_iter)
        self.spinTSNEPerplexity.setValue(options.perplexity)
        self.spinTSNELearningRate.setValue(options.learning_rate)
        self.spinTSNEEarlyExaggeration.setValue(options.early_exaggeration)
        self.gbBarnesHut.setChecked(options.barnes_hut)
        self.spinAngle.setValue(options.angle)
        self.chkRandomState.setChecked(options.random)


class UMAPOptionsWidget(VisualizationOptionsWidget, Ui_UMAPOptionsWidget):
    """Create a widget containing UMAP visualization options"""

    options_class = UMAPVisualizationOptions

    def __init__(self):
        super().__init__()
        self.cbNumIterations.stateChanged.connect(self.spinNumIterations.setEnabled)

    def getValues(self):
        """Return UMAP options"""

        options = super().getValues()
        options.min_score = self.spinMinScore.value()
        options.min_scores_above_threshold = self.spinMinScoresAboveThreshold.value()
        options.n_epochs = self.spinNumIterations.value() if self.cbNumIterations.isChecked() else None
        options.min_dist = self.spinMinDist.value()
        options.random = self.chkRandomState.isChecked()

        return options

    def setValues(self, options):
        super().setValues(options)
        self.spinMinScore.setValue(options.min_score)
        self.spinMinScoresAboveThreshold.setValue(options.min_scores_above_threshold)
        if options.n_epochs is not None:
            self.spinNumIterations.setValue(options.n_epochs)
            self.cbNumIterations.setChecked(True)
            self.spinNumIterations.setEnabled(True)
        else:
            self.cbNumIterations.setChecked(False)
            self.spinNumIterations.setEnabled(False)
        self.spinMinDist.setValue(options.min_dist)
        self.chkRandomState.setChecked(options.random)


class MDSOptionsWidget(VisualizationOptionsWidget, Ui_MDSOptionsWidget):
    """Create a widget containing MDS visualization options"""

    options_class = MDSVisualizationOptions

    def getValues(self):
        options = super().getValues()
        options.min_score = self.spinMinScore.value()
        options.min_scores_above_threshold = self.spinMinScoresAboveThreshold.value()
        options.max_iter = self.spinNumIterations.value()
        options.random = self.chkRandomState.isChecked()

        return options

    def setValues(self, options):
        super().setValues(options)
        self.spinMinScore.setValue(options.min_score)
        self.spinMinScoresAboveThreshold.setValue(options.min_scores_above_threshold)
        self.spinNumIterations.setValue(options.max_iter)
        self.chkRandomState.setChecked(options.random)


class IsomapOptionsWidget(VisualizationOptionsWidget, Ui_IsomapOptionsWidget):
    """Create a widget containing Isomap visualization options"""

    options_class = IsomapVisualizationOptions

    def getValues(self):
        options = super().getValues()
        options.min_score = self.spinMinScore.value()
        options.min_scores_above_threshold = self.spinMinScoresAboveThreshold.value()
        options.max_iter = self.spinNumIterations.value()
        options.n_neighbors = self.spinNumNeighbors.value()

        return options

    def setValues(self, options):
        super().setValues(options)
        self.spinMinScore.setValue(options.min_score)
        self.spinMinScoresAboveThreshold.setValue(options.min_scores_above_threshold)
        self.spinNumIterations.setValue(options.max_iter)
        self.spinNumNeighbors.setValue(options.n_neighbors)


class PHATEOptionsWidget(VisualizationOptionsWidget, Ui_PHATEOptionsWidget):
    """Create a widget containing PHATE visualization options"""

    options_class = PHATEVisualizationOptions

    def getValues(self):
        """Return PHATE options"""

        options = super().getValues()
        options.min_score = self.spinMinScore.value()
        options.min_scores_above_threshold = self.spinMinScoresAboveThreshold.value()
        options.knn = self.spinKnn.value()
        options.decay = self.spinDecay.value()
        options.gamma = self.spinGamma.value()
        options.random = self.chkRandomState.isChecked()

        return options

    def setValues(self, options):
        super().setValues(options)
        self.spinMinScore.setValue(options.min_score)
        self.spinMinScoresAboveThreshold.setValue(options.min_scores_above_threshold)
        self.spinKnn.setValue(options.knn)
        self.spinDecay.setValue(options.decay)
        self.spinGamma.setValue(options.gamma)
        self.chkRandomState.setChecked(options.random)


class CosineOptionsWidget(OptionsGroupBox, Ui_gbCosineOptions):
    """Create a widget containing Cosine computations options"""

    options_class = CosineComputationOptions

    def __init__(self):
        super().__init__()

        self.chkUseMinMZ.stateChanged.connect(self.spinMinMZ.setEnabled)
        self.chkUseParentFiltering.stateChanged.connect(self.spinParentFilterTolerance.setEnabled)
        self.chkUseMinIntensityFiltering.stateChanged.connect(self.spinMinIntensity.setEnabled)
        self.chkUseWindowRankFiltering.stateChanged.connect(self.spinMinMatchedPeaksSearch.setEnabled)
        self.chkUseWindowRankFiltering.stateChanged.connect(self.spinMatchedPeaksWindow.setEnabled)

    def getValues(self):
        options = super().getValues()
        options.mz_tolerance = self.spinMZTolerance.value()
        options.min_matched_peaks = self.spinMinMatchedPeaks.value()
        options.min_mz = self.spinMinMZ.value()
        options.parent_filter_tolerance = self.spinParentFilterTolerance.value()
        options.min_intensity = self.spinMinIntensity.value()
        options.min_matched_peaks_search = self.spinMinMatchedPeaksSearch.value()
        options.matched_peaks_window = self.spinMatchedPeaksWindow.value()
        options.is_ms1_data = self.chkMS1Data.isChecked()
        options.dense_output = not self.chkSparse.isChecked()
        options.use_filtering = self.gbFiltering.isChecked()
        options.use_min_mz_filter = self.chkUseMinMZ.isChecked()
        options.use_min_intensity_filter = self.chkUseMinIntensityFiltering.isChecked()
        options.use_parent_filter = self.chkUseParentFiltering.isChecked()
        options.use_window_rank_filter = self.chkUseWindowRankFiltering.isChecked()

        return options

    def setValues(self, options):
        super().setValues(options)
        self.spinMZTolerance.setValue(options.mz_tolerance)
        self.spinMinMatchedPeaks.setValue(options.min_matched_peaks)
        self.spinMinMZ.setValue(options.min_mz)
        self.spinParentFilterTolerance.setValue(options.parent_filter_tolerance)
        self.spinMinIntensity.setValue(options.min_intensity)
        self.spinMinMatchedPeaksSearch.setValue(options.min_matched_peaks_search)
        self.spinMatchedPeaksWindow.setValue(options.matched_peaks_window)
        self.chkMS1Data.setChecked(options.is_ms1_data)
        self.chkSparse.setChecked(not options.dense_output)
        self.gbFiltering.setChecked(options.use_filtering)
        self.chkUseMinMZ.setChecked(options.use_min_mz_filter)
        self.chkUseMinIntensityFiltering.setChecked(options.use_min_intensity_filter)
        self.chkUseParentFiltering.setChecked(options.use_parent_filter)
        self.chkUseWindowRankFiltering.setChecked(options.use_window_rank_filter)


class QueryDatabasesOptionsWidget(OptionsGroupBox, Ui_gbDatabaseOptions):
    """Create a widget containing Database query options"""

    options_class = QueryDatabasesOptions

    def __init__(self):
        super().__init__()

        # Populate polarity combobox
        self.cbPolarity.addItems(['Positive', 'Negative'])
        self.cbPolarity.setCurrentIndex(0)

    def getValues(self):
        options = super().getValues()
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
        super().setValues(options)
        self.spinMZTolerance.setValue(options.mz_tolerance)
        self.spinMinIntensity.setValue(options.min_intensity)
        self.spinParentFilterTolerance.setValue(options.parent_filter_tolerance)
        self.spinMinMatchedPeaks.setValue(options.min_matched_peaks)
        self.spinMinScore.setValue(options.min_cosine)
        self.gbAnalogs.setChecked(options.analog_search)
        self.spinAnalogTolerance.setValue(options.analog_mz_tolerance)
        self.cbPolarity.setCurrentIndex(0 if options.positive_polarity else 1)
