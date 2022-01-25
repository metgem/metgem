class AttrDict(dict):
    """A dictionary where item can be accessed as attributes."""

    def __getattr__(self, item):
        try:
            return self.__getitem__(item)
        except KeyError as e:
            raise AttributeError(e)

    def __setattr__(self, item, value):
        return self.__setitem__(item, value)

    def __getstate__(self):
        return dict(self)

    def __setstate__(self, state):
        super().update(state)

    def __reduce__(self):
        return self.__class__, (), self.__getstate__()

    def __dir__(self):
        return super().__dir__() + [str(k) for k in self.keys()]

    def update(self, data, **kwargs):
        data = {k: v for k, v in data.items() if k in self}
        super().update(data)

    def copy(self):
        return AttrDict(self)


class ClusterizeOptions(AttrDict):

    def __init__(self):
        super().__init__(column_name='clusters',
                         min_cluster_size=5,
                         min_samples=None,
                         cluster_selection_epsilon=0.,
                         cluster_selection_method='eom')


class CosineComputationOptions(AttrDict):
    """Class containing spectra cosine scores options.

    Attributes:
        mz_tolerance (float): in Da.
        min_intensity (int): relative minimum intensity in percentage.
        parent_filter_tolerance (int): in Da.
        min_matched_peaks (int): Minimum number of common peaks between two spectra.
        min_matched_peaks_search (int): Window rank filter's parameters: for each peak in the spectrum,
            it is kept only if it is in top `min_matched_peaks_search` in the +/-`matched_peaks_window` window.
        matched_peaks_window (int): in Da.

    """

    def __init__(self, **kwargs):
        super().__init__(mz_tolerance=0.02,
                         min_intensity=0,
                         parent_filter_tolerance=17,
                         min_matched_peaks=4,
                         min_matched_peaks_search=6,
                         matched_peaks_window=50,
                         is_ms1_data=False,
                         use_filtering=True,
                         use_min_intensity_filter=False,
                         use_parent_filter=True,
                         use_window_rank_filter=True,
                         **kwargs)


class NetworkVisualizationOptions(AttrDict):
    """Class containing Network visualization options.

    Attributes:
        top_k (int): Maximum numbers of edges for each nodes in the network. Default value = 10
        pairs_min_cosine (float): Minimum cosine score for network generation. Default value = 0.65
        max_connected_nodes (int): Maximum size of a Network cluster. Default value = 1000

    """

    def __init__(self):
        super().__init__(top_k=10,
                         pairs_min_cosine=0.7,
                         max_connected_nodes=1000)


class ReadMetadataOptions(AttrDict):

    def __init__(self):
        super().__init__(sep=None,
                         skiprows=None,
                         nrows=None,
                         dtype=None,
                         header='infer',
                         usecols=None,
                         index_col=None,
                         comment=None)



class QueryDatabasesOptions(CosineComputationOptions):
    """Class containing spectra cosine scores options.

    Attributes:
        See `CosineComputationOptions`.
        min_cosine (float): Minimum cosine score for database query.
        analog_search (bool): Look for analogs (different m/z parent) instead or standards (same m/z parent).
        analog_mz_tolerance (float): m/z tolerance used for analog search, in Da.
        positive_polarity (bool): True for positive polarity, False for negative polarity.
        databases (list of int): Indexes of databases to query in. If empty, search in all available databases.
    """

    def __init__(self):
        super().__init__(min_cosine=0.65,
                         analog_search=False,
                         analog_mz_tolerance=100.,
                         positive_polarity=True,
                         databases=[])


class IsomapVisualizationOptions(AttrDict):
    """Class containing Isomap visualization options.
    """

    def __init__(self):
        super().__init__(min_score=0.70,
                         min_scores_above_threshold=1,
                         n_neighbors=5,
                         max_iter=300)


class MDSVisualizationOptions(AttrDict):
    """Class containing MDS visualization options.
    """

    def __init__(self):
        super().__init__(min_score=0.70,
                         min_scores_above_threshold=1,
                         max_iter=300,
                         random=False)


class PHATEVisualizationOptions(AttrDict):
    """Class containing PHATE visualization options.
    """

    def __init__(self):
        super().__init__(knn=5,
                         decay=15,
                         gamma=1,
                         min_score=0.70,
                         min_scores_above_threshold=1,
                         random=False)


class TSNEVisualizationOptions(AttrDict):
    """Class containing t-SNE visualization options.
    """

    def __init__(self):
        super().__init__(perplexity=6,
                         learning_rate=200,
                         min_score=0.70,
                         min_scores_above_threshold=1,
                         early_exaggeration=12,
                         barnes_hut=True,
                         angle=0.5,
                         n_iter=1000,
                         random=False)


class UMAPVisualizationOptions(AttrDict):
    """Class containing UMAP visualization options.
    """

    def __init__(self):
        super().__init__(n_neighbors=15,
                         min_dist=0.1,
                         min_score=0.70,
                         min_scores_above_threshold=1,
                         n_epochs=None,
                         random=False)
