import numpy as np

from .base import BaseWorker
from ..save import MnzFile, savez
from ..utils import AttrDict
from ..utils.network import Network
from ..workers import NetworkVisualizationOptions, TSNEVisualizationOptions, CosineComputationOptions
from ..graphml import GraphMLParser, GraphMLWriter
from ..errors import UnsupportedVersionError

CURRENT_FORMAT_VERSION = 2

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

                if version == CURRENT_FORMAT_VERSION:
                    if self.isStopped():
                        self.canceled.emit()
                        return

                    # Create network object
                    network = Network()

                    # Load scores matrix
                    network.scores = fid['0/scores']

                    if self.isStopped():
                        self.canceled.emit()
                        return

                    # Load infos
                    network.infos = fid['0/infos']

                    if self.isStopped():
                        self.canceled.emit()
                        return

                    # Load table of spectra
                    spec_infos = fid['0/spectra/index.json']
                    network.mzs = []
                    network.spectra = []
                    for s in spec_infos:
                        if self.isStopped():
                            self.canceled.emit()
                            return

                        network.mzs.append(s['mz_parent'])
                        network.spectra.append(fid[f'0/spectra/{s["id"]}'])

                    if self.isStopped():
                        self.canceled.emit()
                        return

                    # Load options
                    network.options = AttrDict(fid['0/options.json'])
                    for opt, key in ((CosineComputationOptions(), 'cosine'),
                                     (NetworkVisualizationOptions(), 'network'),
                                     (TSNEVisualizationOptions(), 'tsne')):
                        if key in network.options:
                            opt.update(network.options[key])
                        network.options[key] = opt

                    if self.isStopped():
                        self.canceled.emit()
                        return

                    # Load graph
                    gxl = fid['0/graph.graphml']
                    parser = GraphMLParser()
                    network.graph = parser.fromstring(gxl)

                    if self.isStopped():
                        self.canceled.emit()
                        return

                    # Load network layout
                    network.graph.network_layout = fid['0/network_layout']

                    if self.isStopped():
                        self.canceled.emit()
                        return

                    # Load t-SNE layout
                    network.graph.tsne_layout = fid['0/tsne_layout']

                    if self.isStopped():
                        self.canceled.emit()
                        return

                    return network
                else:
                    raise UnsupportedVersionError(f"Unrecognized file format version (version={version}).")
        except (FileNotFoundError, KeyError, UnsupportedVersionError) as e:
            self.error.emit(e)
            return


class SaveProjectWorker(BaseWorker):
    """Save current project to a file for future access"""

    def __init__(self, filename, graph, network, options):
        super().__init__()

        self.filename = filename
        self.graph = graph
        self.network = network
        self.options = options
        self.max = 0
        self.desc = 'Saving project...'

    def run(self):
        # Export graph to GraphML format
        writer = GraphMLWriter()
        gxl = writer.tostring(self.graph).decode()

        # Convert lists of parent mass and spectrum data to something that be can be saved
        mzs = getattr(self.network, 'mzs', [])
        spectra = getattr(self.network, 'spectra', [])
        spec_infos = [{'id': i, 'mz_parent': mz_parent} for i, mz_parent in enumerate(spectra)]
        spec_data = {'0/spectra/{}'.format(i): data for i, data in enumerate(spectra)}

        # Create dict for saving
        d = {'0/scores': getattr(self.network, 'scores', np.array([])),
             '0/spectra/index.json': spec_infos,
             '0/infos': getattr(self.network, 'infos', np.array([])),
             '0/graph.graphml': gxl,
             '0/network_layout': getattr(self.graph, 'network_layout', np.array([])),
             '0/tsne_layout': getattr(self.graph, 'tsne_layout', np.array([])),
             '0/options.json': self.options}
        d.update(spec_data)

        try:
            savez(self.filename, version=CURRENT_FORMAT_VERSION, **d)
        except PermissionError as e:
            self.error.emit(e)
        else:
            self.finished.emit()
