import zipfile

import pandas as pd
from scipy.sparse import csr_matrix

from metgem.utils.qt import QColor, Qt
from metgem.mappings import SizeMappingFunc, MODE_LINEAR
from metgem.utils.network import Network, generate_id
from metgem.workers.struct import StandardsResult

from metgem.workers.base import BaseWorker
from metgem.workers.options import AttrDict, AVAILABLE_NETWORK_OPTIONS, AVAILABLE_OPTIONS, \
    ForceDirectedVisualizationOptions, TSNEVisualizationOptions

from metgem.workers.core.project.mnz import MnzFile
from metgem.workers.core.project.spectra_list import SpectraList
from metgem.workers.core.project.graphml import GraphMLParser
from metgem.workers.core.project.version import CURRENT_FORMAT_VERSION, UnsupportedVersionError


class LoadProjectWorker(BaseWorker):
    """Load project from a previously saved file"""

    def __init__(self, filename):
        super().__init__()

        self.filename = filename
        self.max = 100
        self.desc = 'Loading project...'
        self.iterative_update = False

    def run(self):
        try:
            with (MnzFile(self.filename) as fid):
                try:
                    version = int(fid['version'])
                except ValueError:
                    version = 1
                self.updated.emit(1)

                if version == 1:
                    raise UnsupportedVersionError("This file was saved with a development version of the software.\n"
                                                  + "This file format is not supported anymore.\n"
                                                  + "Please generate networks from raw data again")

                elif version in (2, 3, 4, 5, 6, CURRENT_FORMAT_VERSION):
                    # Create network object
                    network = Network()
                    network.lazyloaded = True

                    # Load scores matrix
                    # Prior to version, scores must be a dense numpy array
                    # Starting from version 6, scores can be a CSR sparse matrix or a dense numpy array
                    try:
                        network.scores = fid['0/scores']
                    except KeyError:
                        network.scores = csr_matrix((fid['0/scores_data'],
                                                    fid['0/scores_indices'],
                                                    fid['0/scores_indptr']),
                                                    shape=fid['0/scores_shape'])

                    self.updated.emit(10)
                    if self.isStopped():
                        self.canceled.emit()
                        return

                    # Load infos making sure it is a pandas DataFrame object (and not numpy array)
                    try:
                        network.infos = pd.DataFrame(fid['0/infos'])
                    except KeyError:
                        network.infos = pd.DataFrame()

                    self.updated.emit(20)
                    if self.isStopped():
                        self.canceled.emit()
                        return

                    # Load group mappings
                    try:
                        network.mappings = fid['0/mappings.json']
                    except KeyError:
                        network.mappings = {}

                    self.updated.emit(30)
                    if self.isStopped():
                        self.canceled.emit()
                        return

                    # Load columns mappings
                    try:
                        columns_mappings = fid['0/columns_mappings.json']
                    except KeyError:
                        network.columns_mappings = {}
                    else:
                        try:
                            id_ = columns_mappings.get('label', None)
                        except TypeError:
                            pass
                        else:
                            if id_ is not None:
                                columns_mappings['label'] = id_

                        try:
                            ids, colors = columns_mappings.get('pies', (None, None))
                        except TypeError:
                            pass
                        else:
                            if ids is not None and colors is not None:
                                colors = [QColor(color) for color in colors]
                                columns_mappings['pies'] = (ids, colors)

                        try:
                            id_, mapping = columns_mappings.get('colors', (None, None))
                        except TypeError:
                            pass
                        else:
                            if id_ is not None and mapping is not None:
                                if isinstance(mapping, (tuple, list)):
                                    try:
                                        if len(mapping) == 2:
                                            bins, colors = mapping
                                            polygons = [0 for _ in colors]  # default value
                                            styles = [Qt.NodeBrush for _ in colors]
                                        elif len(mapping) == 3:
                                            bins, colors, polygons = mapping
                                            styles = [Qt.NoBrush for _ in colors]
                                        else:
                                            bins, colors, polygons, styles = mapping
                                    except TypeError:
                                        pass
                                    else:
                                        colors = [QColor(color) for color in colors]
                                        mapping = (bins, colors, polygons, styles)
                                elif isinstance(mapping, dict):
                                    mapping = {k: (QColor(color), polygon, style)
                                               for k, (color, polygon, style) in mapping.items()}
                                columns_mappings['colors'] = (id_, mapping)

                        try:
                            id_, func = columns_mappings.get('size', (None, None))
                        except TypeError:
                            pass
                        else:
                            if id_ is not None and func is not None:
                                func = SizeMappingFunc(func.get('xs', []),
                                                       func.get('ys', []),
                                                       func.get('ymin', 0),
                                                       func.get('ymax', 100),
                                                       func.get('mode', MODE_LINEAR))
                                columns_mappings['size'] = (id_, func)

                        try:
                            id_, type_ = columns_mappings.get('pixmap', None)
                        except TypeError:
                            pass
                        else:
                            if id_ is not None and type_ is not None:
                                columns_mappings['pixmap'] = (id_, type_)

                        network.columns_mappings = columns_mappings

                    self.updated.emit(40)
                    if self.isStopped():
                        self.canceled.emit()
                        return

                    # Load table of spectra
                    network.spectra = SpectraList(self.filename)
                    mzs = []
                    for s in fid['0/spectra/index.json']:
                        mzs.append(s['mz_parent'])
                    network.mzs = pd.Series(mzs)

                    self.updated.emit(50)
                    if self.isStopped():
                        self.canceled.emit()
                        return

                    # Load options
                    names_to_ids = {}
                    try:
                        network.options = AttrDict(fid['0/options.json'])
                    except KeyError:
                        network.options = AttrDict({})

                    # Prior to version 5, network views options was unique for each view
                    # Generate an id for those views
                    if version < 5:
                        for key in AVAILABLE_NETWORK_OPTIONS.keys():
                            if key in network.options:
                                # Prior to version 7, Force Directed layout was just named 'network'
                                new_key = ForceDirectedVisualizationOptions.name if key == 'network' else key
                                id_ = generate_id(new_key)
                                network.options[id_] = network.options[key]
                                del network.options[key]
                                names_to_ids[new_key] = names_to_ids[key] = id_

                    # Make sure that network view options does not miss some values
                    # If values are missing, fill with default
                    for key in network.options:
                        if '_' in key:  # Network views options
                            name = key.split('_')[0]
                            options_class = AVAILABLE_NETWORK_OPTIONS.get(name, None)
                            if options_class is not None:
                                opt = options_class()
                                opt.update(network.options[key])
                                network.options[key] = opt
                            # Prior to version 3, max_connected_nodes value was set 1000 but ignored
                            # Set it to 0 to keep the same behavior
                            if version < 3 and name == ForceDirectedVisualizationOptions.name:
                                network.options[key].max_connected_nodes = 0
                        elif key in AVAILABLE_OPTIONS:
                            options_class = AVAILABLE_OPTIONS.get(key, None)
                            if options_class is not None:
                                opt = options_class()
                                opt.update(network.options[key])
                                network.options[key] = opt

                    self.updated.emit(60)
                    if self.isStopped():
                        self.canceled.emit()
                        return

                    # Load Databases results
                    try:
                        results = fid['0/db_results.json']

                        for k, v in results.items():
                            if 'standards' in v:
                                results[k]['standards'] = [StandardsResult(*r) for r in v['standards']]
                            if 'analogs' in v:
                                results[k]['analogs'] = [StandardsResult(*r) for r in v['analogs']]
                        network.db_results = {int(k): v for k, v in results.items()}  # Convert string keys to integer
                    except KeyError:
                        network.db_results = {}

                    self.updated.emit(70)
                    if self.isStopped():
                        self.canceled.emit()
                        return

                    # Load graphs/interactions
                    graphs = {}
                    parser = GraphMLParser()
                    if version < 5:
                        try:
                            gxl = fid['0/graph.graphml']
                            interactions = pd.DataFrame(fid['0/interactions'])
                            graphs[ForceDirectedVisualizationOptions.name] = {'graph': parser.fromstring(gxl),
                                                                              'interactions': interactions}
                        except KeyError:
                            pass
                    else:
                        names = fid['0/layouts.json']
                        for name in names:
                            try:
                                gxl = fid[f'0/graphs/{name}.graphml']
                                interactions = fid[f'0/graphs/{name}']
                                graphs[name] = {'graph': parser.fromstring(gxl),
                                                'interactions': interactions}
                            except KeyError:
                                pass

                    self.updated.emit(80)
                    if self.isStopped():
                        self.canceled.emit()
                        return

                    # Load layouts
                    layouts = {}
                    if version <= 3:
                        graph = graphs[ForceDirectedVisualizationOptions.name]['graph']
                        colors = graph.vs['__color'] if '__color' in graph.vs.attributes() else {}
                        if isinstance(colors, list):
                            colors = {str(i): c for i, c in enumerate(colors) if c is not None}
                        radii = graph.vs['__size'] if '__size' in graph.vs.attributes() else {}

                        layouts[ForceDirectedVisualizationOptions.name] = {
                            'layout': fid['0/network_layout'],
                            # Prior to version 4, colors of nodes were stored as graph attributes
                            'colors': colors,
                            'radii': radii
                        }

                        layouts[TSNEVisualizationOptions.name] = {
                            'layout': fid['0/tsne_layout'],
                            'colors': colors,
                            'radii': radii
                        }
                        try:
                            layouts[TSNEVisualizationOptions.name]['isolated_nodes'] = fid['0/tsne_isolated_nodes']
                        except KeyError:
                            pass
                    else:
                        try:
                            names = fid['0/layouts.json']
                            for name in names:
                                key = f'0/layouts/{name}'
                                layout = {}
                                for k in fid.keys():
                                    if k.startswith(key):
                                        x = k[len(key)+1:]
                                        if x.startswith('colors'):
                                            layout[x] = {k: QColor(v) for k, v in fid[k].items()}
                                        elif x.startswith('radii'):
                                            layout[x] = fid[k].tolist()
                                        else:
                                            layout[x] = fid[k]
                                layouts[name] = layout
                        except KeyError:
                            pass

                    self.updated.emit(90)
                    if self.isStopped():
                        self.canceled.emit()
                        return

                    # Load annotations
                    annotations = {}
                    try:
                        names = fid['0/annotations.json']
                        for name in names:
                            key = f'0/annotations/{name}'
                            annotations[name] = fid[key]
                    except KeyError:
                        pass

                    self.updated.emit(99)
                    if self.isStopped():
                        self.canceled.emit()
                        return

                    # For version < 5, network views were unique for each type
                    # When loading options, new ids were generated and a mapping was created
                    # Rename these keys in graphs and layouts dicts
                    if version < 5:
                        for name, id_ in names_to_ids.items():
                            if name in graphs:
                                graphs[id_] = graphs[name]
                                del graphs[name]
                            if name in layouts:
                                layouts[id_] = layouts[name]
                                del layouts[name]

                    self.updated.emit(100)
                    if self.isStopped():
                        self.canceled.emit()
                        return

                    return network, layouts, graphs, annotations
                else:
                    raise UnsupportedVersionError(f"Unrecognized file format version (version={version}).")
        except (FileNotFoundError, KeyError, zipfile.BadZipFile, UnsupportedVersionError) as e:
            self.error.emit(e)
            return
