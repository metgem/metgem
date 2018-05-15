from ..workers.network_generation import generate_network

from PyQt5.QtCore import QObject, pyqtSignal


class Network(QObject):
    __slots__ = 'mzs', 'spectra', 'scores', 'graph', 'options', '_infos', '_interactions'

    infosAboutToChange = pyqtSignal()
    infosChanged = pyqtSignal()
    interactionsAboutToChange = pyqtSignal()
    interactionsChanged = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._interactions = None
        self._infos = None

    @property
    def infos(self):
        return self._infos

    @infos.setter
    def infos(self, data):
        self.infosAboutToChange.emit()
        self._infos = data
        self.infosChanged.emit()

    @property
    def interactions(self):
        if self._interactions is None:
            if getattr(self, 'scores', None) is not None and getattr(self, 'spectra', None) is not None:
                self.interactionsAboutToChange.emit()
                self._interactions = generate_network(self.scores, self.mzs, self.options.network)
                self.interactionsChanged.emit()

        return self._interactions

    @interactions.setter
    def interactions(self, data):
        if data is not None:
            self.interactionsAboutToChange.emit()
        self._interactions = data
        if data is not None:
            self.interactionsChanged.emit()
