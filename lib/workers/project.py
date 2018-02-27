import numpy as np

from .base_worker import BaseWorker
from ..save import MnzFile, savez
from ..utils import Network, AttrDict
from ..workers import Spectrum
from ..graphml import GraphMLParser, GraphMLWriter
from ..errors import UnsupportedVersionError


class LoadProjectWorker(BaseWorker):
    """Load project from a previously saved file"""

    def __init__(self, filename):
        super().__init__()

        self.filename = filename

    def run(self):
        try:
            with MnzFile(self.filename) as fid:
                try:
                    version = int(fid['version'])
                except ValueError:
                    version = 1

                if version == 1:
                    network = Network()
                    network.scores = fid['network/scores']
                    network.infos = fid['network/infos']

                    spec_infos = fid['network/spectra/index.json']
                    network.spectra = [Spectrum(s['id'], s['mz_parent'], fid[f'network/spectra/{s["id"]}']) for
                                       s in spec_infos]

                    # Load options
                    options = AttrDict(fid['options.json'])
                    for k, v in options.items():
                        options[k] = AttrDict(v)

                    # Load graph
                    gxl = fid['graph.gxl']
                    parser = GraphMLParser()
                    graph = parser.fromstring(gxl)

                    graph.network_layout = fid['network_layout']
                    graph.tsne_layout = fid['tsne_layout']

                    self._result = graph, network, options
                else:
                    raise UnsupportedVersionError(f"Unrecognized file format version (version={version}).")
        except (FileNotFoundError, UnsupportedVersionError) as e:
            self.error.emit(e)
            self._result = None, None, None
        else:
            self.finished.emit()


class SaveProjectWorker(BaseWorker):
    """Save current project to a file for future access"""

    def __init__(self, filename, graph, network, options):
        super().__init__()

        self.filename = filename
        self.graph = graph
        self.network = network
        self.options = options

    def run(self):
        # Export graph to GraphML format
        writer = GraphMLWriter()
        gxl = writer.tostring(self.graph).decode()

        # Convert list of Spectrum objects to something that be saved
        spectra = getattr(self.network, 'spectra', [])
        spec_infos = [{'id': s.id, 'mz_parent': s.mz_parent} for s in spectra]
        spec_data = {'network/spectra/{}'.format(s.id): s.data for s in spectra}

        # Create dict for saving
        d = {'network/scores': getattr(self.network, 'scores', np.array([])),
             'network/spectra/index.json': spec_infos,
             'network/infos': getattr(self.network, 'infos', np.array([])),
             'graph.gxl': gxl,
             'network_layout': getattr(self.graph, 'network_layout', np.array([])),
             'tsne_layout': getattr(self.graph, 'tsne_layout', np.array([])),
             'options.json': self.options}
        d.update(spec_data)

        try:
            savez(self.filename, version=1, **d)
        except PermissionError as e:
            self.error.emit(e)
        else:
            self.finished.emit()