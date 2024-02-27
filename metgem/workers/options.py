class AttrDict(dict):
    """A dictionary where item can be accessed as attributes."""

    name = None

    # noinspection PyUnresolvedReferences
    @classmethod
    def get_subclasses(cls):
        for subclass in cls.__subclasses__():
            if subclass.name is not None:
                yield subclass
            yield from subclass.get_subclasses()

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


class Options(AttrDict):
    pass


class ClusterizeOptions(Options):
    name = 'clusterize'

    def __init__(self):
        super().__init__(column_name='clusters',
                         min_cluster_size=5,
                         min_samples=None,
                         cluster_selection_epsilon=0.,
                         cluster_selection_method='eom')


class NumberizeOptions(Options):
    name = 'numberize'

    def __init__(self):
        super().__init__(column_name='clusters')


class CosineComputationOptions(Options):
    """Class containing spectra cosine scores options.

    Attributes:
        mz_tolerance (float): in Da.
        min_matched_peaks (int): Minimum number of common peaks between two spectra.
        min_mz (int): Minimum m/z to keep in spectra
        parent_filter_tolerance (int): in Da.
        min_intensity (int): relative minimum intensity in percentage.
        min_matched_peaks_search (int): Window rank filter's parameters: for each peak in the spectrum,
            it is kept only if it is in top `min_matched_peaks_search` in the +/-`matched_peaks_window` window.
        matched_peaks_window (int): in Da.
        dense_output (bool): Whether compute a dense or sparse similarity matrix. Default=true

    """

    name = 'cosine'

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
                         use_min_mz_filter=True,
                         min_mz=50,
                         dense_output=True,
                         **kwargs)


class ReadMetadataOptions(Options):

    name = 'metadata'

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

    name = 'query_dbs'

    def __init__(self):
        super().__init__(min_cosine=0.65,
                         analog_search=False,
                         analog_mz_tolerance=100.,
                         positive_polarity=True,
                         databases=[])


class VisualizationOptions(Options):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, title=None)


class ForceDirectedVisualizationOptions(VisualizationOptions):
    """Class containing Force Directed visualization options.

    Attributes:
        top_k (int): Maximum numbers of edges for each node in the network. Default value = 10
        pairs_min_cosine (float): Minimum cosine score for network generation. Default value = 0.65
        max_connected_nodes (int): Maximum size of a Force Directed cluster. Default value = 1000
        scale (float): Control repulsion between nodes. More makes a more sparse graph. Default value = 30.0
        gravity (float):  ==Attracts nodes to the center. Prevents islands from drifting away. Default value = 1.0
    """
    name = 'fd'

    def __init__(self):
        super().__init__(top_k=10,
                         pairs_min_cosine=0.7,
                         max_connected_nodes=1000,
                         scale=30.0,
                         gravity=1.0)


class IsomapVisualizationOptions(VisualizationOptions):
    """Class containing Isomap visualization options.
    """
    name = 'isomap'

    def __init__(self):
        super().__init__(min_score=0.70,
                         min_scores_above_threshold=1,
                         n_neighbors=5,
                         max_iter=300)


class MDSVisualizationOptions(VisualizationOptions):
    """Class containing MDS visualization options.
    """
    name = 'mds'

    def __init__(self):
        super().__init__(min_score=0.70,
                         min_scores_above_threshold=1,
                         max_iter=300,
                         random=False)


class PHATEVisualizationOptions(VisualizationOptions):
    """Class containing PHATE visualization options.
    """
    name = 'phate'

    def __init__(self):
        super().__init__(knn=5,
                         decay=15,
                         gamma=1,
                         min_score=0.70,
                         min_scores_above_threshold=1,
                         random=False)


class TSNEVisualizationOptions(VisualizationOptions):
    """Class containing t-SNE visualization options.
    """
    name = 'tsne'

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


class UMAPVisualizationOptions(VisualizationOptions):
    """Class containing UMAP visualization options.
    """
    name = 'umap'

    def __init__(self):
        super().__init__(n_neighbors=15,
                         min_dist=0.1,
                         min_score=0.70,
                         min_scores_above_threshold=1,
                         n_epochs=None,
                         random=False)


AVAILABLE_OPTIONS = {obj.name: obj for obj in Options.get_subclasses()}
AVAILABLE_NETWORK_OPTIONS = {obj.name: obj for obj in VisualizationOptions.get_subclasses()}
# Keep old name for Force Directed layout
AVAILABLE_NETWORK_OPTIONS['network'] = ForceDirectedVisualizationOptions
