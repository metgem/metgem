import os
import zipfile

import numpy as np
import pandas as pd
import igraph as ig

from ....utils.network import Network
from ....utils.qt import QColor

from ...base import BaseWorker

from .graphml import GraphMLWriter
from .mnz import savez
from .version import CURRENT_FORMAT_VERSION
from .spectra_list import SpectraList


class SaveProjectWorker(BaseWorker):
    """Save current project to a file for future access"""

    def __init__(self, filename: str, network: Network, infos: pd.DataFrame,
                 options: dict, layouts: dict, graphs: {}, annotations=None, original_fname=None):
        super().__init__()

        self.filename = filename
        self.original_fname = original_fname
        path, fname = os.path.split(filename)
        self.tmp_filename = os.path.join(path, f".tmp-{fname}")
        self.network = network
        self.infos = infos if infos is not None else pd.DataFrame()
        self.layouts = layouts
        self.graphs = graphs
        self.options = options
        self.layouts = layouts
        self.annotations = annotations
        self.max = 0
        self.desc = 'Saving project...'

    def run(self):
        # Create dict for saving
        d = {'0/scores': getattr(self.network, 'scores', np.array([])),
             '0/infos': self.infos,
             '0/options.json': self.options,
             '0/layouts.json': list(self.layouts.keys())}

        for name, layout in self.layouts.items():
            key = f'0/layouts/{name}'
            for k, v in layout.items():
                d['{key}/{k}'.format(key=key, k=k)] = v

        # Export graph to GraphML format
        writer = GraphMLWriter()
        for name, g in self.graphs.items():
            graph = g.get('graph', ig.Graph())
            d[f'0/graphs/{name}.graphml'] = writer.tostring(graph).decode()
            d[f'0/graphs/{name}'] = g.get('interactions', pd.DataFrame())

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
