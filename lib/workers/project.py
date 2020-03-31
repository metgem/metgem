import os
import zipfile

import numpy as np
from PyQt5.QtGui import QColor

from .base import BaseWorker
from ..config import FILE_EXTENSION
from ..errors import UnsupportedVersionError
from ..graphml import GraphMLParser, GraphMLWriter
from ..save import MnzFile, savez
from ..ui.size_mapping_dialog import SizeMappingFunc, MODE_LINEAR
from ..utils import AttrDict
from ..utils.network import Network
from ..workers import (NetworkVisualizationOptions, TSNEVisualizationOptions,
                       MDSVisualizationOptions,
                       CosineComputationOptions, UMAPVisualizationOptions)
from ..workers.databases import StandardsResult

CURRENT_FORMAT_VERSION = 4


class SpectraList(list):

    def __init__(self, filename):
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
                        network.interactions = fid['0/interactions']
                    except KeyError:
                        network.interactions = None

                    if self.isStopped():
                        self.canceled.emit()
                        return

                    # Load infos
                    network.infos = fid['0/infos']

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
                            ids, colors = columns_mappings.get('pies', (None, None))
                        except TypeError:
                            pass
                        else:
                            if ids is not None and colors is not None:
                                colors = [QColor(color) for color in colors]
                                columns_mappings['pies'] = (ids, colors)

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

                        network.columns_mappings = columns_mappings

                    # Load table of spectra
                    network.spectra = SpectraList(self.filename)
                    network.mzs = []
                    for s in fid['0/spectra/index.json']:
                        network.mzs.append(s['mz_parent'])

                    if self.isStopped():
                        self.canceled.emit()
                        return

                    # Load options
                    network.options = AttrDict(fid['0/options.json'])
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
                    gxl = fid['0/graph.graphml']
                    parser = GraphMLParser()
                    graph = parser.fromstring(gxl)
                    network.graph = graph

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
                        names = fid['0/layouts.json']
                        for name in names:
                            key = '0/layouts/{name}'.format(name=name)
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

                    return network, layouts
                else:
                    raise UnsupportedVersionError(f"Unrecognized file format version (version={version}).")
        except (FileNotFoundError, KeyError, zipfile.BadZipFile, UnsupportedVersionError) as e:
            self.error.emit(e)
            return


class SaveProjectWorker(BaseWorker):
    """Save current project to a file for future access"""

    def __init__(self, filename, graph, network, infos, options, layouts, original_fname=None):
        super().__init__()

        if not filename.endswith(FILE_EXTENSION):
            filename += FILE_EXTENSION

        self.filename = filename
        self.original_fname = original_fname
        path, fname = os.path.split(filename)
        self.tmp_filename = os.path.join(path, f".tmp-{fname}")
        self.graph = graph
        self.network = network
        self.infos = infos if infos is not None else np.array([])
        self.layouts = layouts
        self.options = options
        self.layouts = layouts
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
            key = '0/layouts/{name}'.format(name=name)
            for k, v in layout.items():
                d['{key}/{k}'.format(key=key, k=k)] = v

        db_results = getattr(self.network, 'db_results', None)
        if db_results is not None:
            d['0/db_results.json'] = db_results

        mappings = getattr(self.network, 'mappings', None)
        if mappings is not None:
            d['0/mappings.json'] = mappings

        columns_mappings = getattr(self.network, 'columns_mappings', None)
        if columns_mappings:
            try:
                ids, colors = columns_mappings.get('pies', (None, None))
            except TypeError:
                pass
            else:
                if colors is not None:
                    colors = [color.name() if isinstance(color, QColor) else color for color in colors]
                    columns_mappings['pies'] = (ids, colors)

            try:
                id_, mapping = columns_mappings.get('colors', (None, None))
            except TypeError:
                pass
            else:
                if mapping is not None:
                    if isinstance(mapping, tuple):
                        try:
                            bins, colors = mapping
                        except TypeError:
                            pass
                        else:
                            colors = [color.name() if isinstance(color, QColor) else color for color in colors]
                            columns_mappings['colors'] = (id_, (bins, colors))
                    elif isinstance(mapping, dict):
                        columns_mappings['colors'] = (id_, {k: v.name() for k, v in mapping.items()})

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
            mzs = getattr(self.network, 'mzs', [])
            spectra = getattr(self.network, 'spectra', [])
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
            except OSError as e:
                self.error.emit(e)
            else:
                return True
