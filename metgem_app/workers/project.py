import os
import zipfile

import numpy as np
import pandas as pd
import igraph as ig
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

from PyQtNetworkView.node import NodePolygon
from .base import BaseWorker
from ..config import FILE_EXTENSION
from ..errors import UnsupportedVersionError
from ..graphml import GraphMLParser, GraphMLWriter
from ..save import MnzFile, savez
from ..mappings import MODE_LINEAR, SizeMappingFunc
from ..utils import AttrDict
from ..utils.network import Network
from ..workers import (NetworkVisualizationOptions, TSNEVisualizationOptions,
                       MDSVisualizationOptions,
                       CosineComputationOptions, UMAPVisualizationOptions)
from ..workers.databases import StandardsResult

CURRENT_FORMAT_VERSION = 4


class SpectraList(list):

    def __init__(self, filename):
        super().__init__()
        self.load(filename)

    def __getitem__(self, index):
        data = super().__getitem__(index)
        if isinstance(data, int):
            data = self._file[f'0/spectra/{data}']
            super().__setitem__(index, data)

        return data

    def __del__(self):
        self.close()

    def close(self):
        self._file.close()

    # noinspection PyAttributeOutsideInit
    def load(self, filename):
        self._file = MnzFile(filename, 'r')

        self.clear()
        for s in self._file['0/spectra/index.json']:
            self.append(s['id'])


class LoadProjectWorker(BaseWorker):
    """Load project from a previously saved file"""

    def __init__(self, filename):
        super().__init__()

        self.filename = filename
        self.max = 0
        self.desc = 'Loading project...'

    def run(self):
        try:
            with MnzFile(self.filename) as fid:
                try:
                    version = int(fid['version'])
                except ValueError:
                    version = 1

                if version == 1:
                    raise UnsupportedVersionError("This file was saved with a development version of the software.\n"
                                                  + "This file format is not supported anymore.\n"
                                                  + "Please generate networks from raw data again")

                elif version in (2, 3, CURRENT_FORMAT_VERSION):
                    # Create network object
                    network = Network()
                    network.lazyloaded = True

                    # Load scores matrix
                    network.scores = fid['0/scores']

                    if self.isStopped():
                        self.canceled.emit()
                        return

                    # Load interactions
                    try:
                        network.interactions = pd.DataFrame(fid['0/interactions'])
                    except KeyError:
                        network.interactions = pd.DataFrame()

                    if self.isStopped():
                        self.canceled.emit()
                        return

                    # Load infos making sure it is a pandas DataFrame object (and not numpy array)
                    try:
                        network.infos = pd.DataFrame(fid['0/infos'])
                    except KeyError:
                        network.infos = pd.DataFrame()

                    if self.isStopped():
                        self.canceled.emit()
                        return

                    # Load group mappings
                    try:
                        network.mappings = fid['0/mappings.json']
                    except KeyError:
                        network.mappings = {}

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
                                            polygons = [NodePolygon.Circle.value for _ in colors]  # default value
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

                    # Load table of spectra
                    network.spectra = SpectraList(self.filename)
                    mzs = []
                    for s in fid['0/spectra/index.json']:
                        mzs.append(s['mz_parent'])
                    network.mzs = pd.Series(mzs)

                    if self.isStopped():
                        self.canceled.emit()
                        return

                    # Load options
                    try:
                        network.options = AttrDict(fid['0/options.json'])
                    except KeyError:
                        network.options = AttrDict({})
                    for opt, key in ((CosineComputationOptions(), 'cosine'),
                                     (NetworkVisualizationOptions(), 'network'),
                                     (TSNEVisualizationOptions(), 'tsne'),
                                     (MDSVisualizationOptions(), 'mds'),
                                     (UMAPVisualizationOptions(), 'umap')):
                        if key in network.options:
                            opt.update(network.options[key])
                        network.options[key] = opt
                    # Prior to version 3, max_connected_nodes value was set 1000 but ignored
                    # Set it to 0 to keep the same behavior
                    if version < 3:
                        network.options.network.max_connected_nodes = 0

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

                    if self.isStopped():
                        self.canceled.emit()
                        return

                    # Load graph
                    try:
                        gxl = fid['0/graph.graphml']
                        parser = GraphMLParser()
                        graph = parser.fromstring(gxl)
                        network.graph = graph
                    except KeyError:
                        network.graph = ig.Graph()

                    if self.isStopped():
                        self.canceled.emit()
                        return

                    # Load layouts
                    layouts = {}
                    if version <= 3:
                        colors = graph.vs['__color'] if '__color' in graph.vs.attributes() else {}
                        if isinstance(colors, list):
                            colors = {str(i): c for i, c in enumerate(colors) if c is not None}
                        radii = graph.vs['__size'] if '__size' in graph.vs.attributes() else {}

                        layouts['network'] = {
                                              'layout': fid['0/network_layout'],
                                              # Prior to version 4, colors of nodes were stored as graph attributes
                                              'colors': colors,
                                              'radii': radii
                                             }

                        if self.isStopped():
                            self.canceled.emit()
                            return

                        layouts['tsne'] = {'layout': fid['0/tsne_layout'],
                                           'colors': colors,
                                           'radii': radii
                                           }
                        try:
                            layouts['tsne']['isolated_nodes'] = fid['0/tsne_isolated_nodes']
                        except KeyError:
                            pass

                        if self.isStopped():
                            self.canceled.emit()
                            return
                    else:
                        layouts = {}
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

                    # Load annotations
                    annotations = {}
                    try:
                        names = fid['0/annotations.json']
                        for name in names:
                            key = f'0/annotations/{name}'
                            annotations[name] = fid[key]
                    except KeyError:
                        pass

                    return network, layouts, annotations
                else:
                    raise UnsupportedVersionError(f"Unrecognized file format version (version={version}).")
        except (FileNotFoundError, KeyError, zipfile.BadZipFile, UnsupportedVersionError) as e:
            self.error.emit(e)
            return


class SaveProjectWorker(BaseWorker):
    """Save current project to a file for future access"""

    def __init__(self, filename, graph, network, infos, options, layouts, annotations=None, original_fname=None):
        super().__init__()

        if not filename.endswith(FILE_EXTENSION):
            filename += FILE_EXTENSION

        self.filename = filename
        self.original_fname = original_fname
        path, fname = os.path.split(filename)
        self.tmp_filename = os.path.join(path, f".tmp-{fname}")
        self.graph = graph
        self.network = network
        self.infos = infos if infos is not None else pd.DataFrame()
        self.layouts = layouts
        self.options = options
        self.layouts = layouts
        self.annotations = annotations
        self.max = 0
        self.desc = 'Saving project...'

    def run(self):
        # Export graph to GraphML format
        writer = GraphMLWriter()
        gxl = writer.tostring(self.graph).decode()

        # Create dict for saving
        d = {'0/scores': getattr(self.network, 'scores', np.array([])),
             '0/interactions': getattr(self.network, 'interactions', np.array([])),
             '0/infos': self.infos,
             '0/graph.graphml': gxl,
             '0/options.json': self.options,
             '0/layouts.json': list(self.layouts.keys())}

        for name, layout in self.layouts.items():
            key = f'0/layouts/{name}'
            for k, v in layout.items():
                d['{key}/{k}'.format(key=key, k=k)] = v

        if self.annotations is not None:
            d['0/annotations.json'] = list(self.annotations.keys())
            for name, buffer in self.annotations.items():
                key = f'0/annotations/{name}'
                d[key] = buffer

        db_results = getattr(self.network, 'db_results', None)
        if db_results is not None:
            d['0/db_results.json'] = db_results

        mappings = getattr(self.network, 'mappings', None)
        if mappings is not None:
            d['0/mappings.json'] = mappings

        columns_mappings = getattr(self.network, 'columns_mappings', None)
        if columns_mappings:
            try:
                key = columns_mappings.get('label', None)
            except TypeError:
                pass
            else:
                if key is not None:
                    columns_mappings['label'] = key

            try:
                keys, colors = columns_mappings.get('pies', (None, None))
            except TypeError:
                pass
            else:
                if colors is not None:
                    colors = [color.name() if isinstance(color, QColor) else color for color in colors]
                    columns_mappings['pies'] = (keys, colors)

            try:
                key, mapping = columns_mappings.get('colors', (None, None))
            except TypeError:
                pass
            else:
                if mapping is not None:
                    if isinstance(mapping, (tuple, list)):
                        try:
                            bins, colors, polygons, styles = mapping
                        except TypeError:
                            pass
                        else:
                            colors = [color.name() if isinstance(color, QColor) else color for color in colors]
                            columns_mappings['colors'] = (key, (bins, colors, polygons, styles))
                    elif isinstance(mapping, dict):
                        columns_mappings['colors'] = (key,
                                                      {k: (color.name(), polygon, style)
                                                       if isinstance(color, QColor) else (color, polygon, style)
                                                       for k, (color, polygon, style) in mapping.items()})

            try:
                key, type_ = columns_mappings.get('pixmap', None)
            except TypeError:
                pass
            else:
                if key is not None:
                    columns_mappings['pixmap'] = (key, type_)

            d['0/columns_mappings.json'] = columns_mappings

        if self.network.lazyloaded and os.path.exists(self.original_fname):
            self.network.spectra.close()

            # create a temp copy of the archive without filename
            with zipfile.ZipFile(self.original_fname, 'r') as zin:
                with zipfile.ZipFile(self.tmp_filename, 'w') as zout:
                    zout.comment = zin.comment  # preserve the comment
                    for item in zin.infolist():
                        if item.filename.startswith('0/spectra/'):
                            zout.writestr(item, zin.read(item.filename))
        else:
            # Convert lists of parent mass and spectrum data to something that be can be saved
            mzs = getattr(self.network, 'mzs', pd.Series())
            spectra = getattr(self.network, 'spectra', pd.DataFrame())
            d['0/spectra/index.json'] = [{'id': i, 'mz_parent': mz_parent} for i, mz_parent in enumerate(mzs)]
            d.update({'0/spectra/{}'.format(i): data for i, data in enumerate(spectra)})

        try:
            savez(self.tmp_filename, version=CURRENT_FORMAT_VERSION, **d)
        except PermissionError as e:
            try:
                os.remove(self.tmp_filename)
            except OSError:
                pass
            self.error.emit(e)
        else:
            try:
                if os.path.exists(self.filename):
                    os.remove(self.filename)
                os.rename(self.tmp_filename, self.filename)
                if isinstance(getattr(self.network, 'spectra', []), list):
                    self.network.spectra = SpectraList(self.filename)
                else:
                    self.network.spectra.load(self.filename)
                self.network.lazyloaded = True
            except OSError as e:
                self.error.emit(e)
            else:
                return True
