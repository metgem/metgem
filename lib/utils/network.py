from PyQt5.QtCore import QObject, pyqtSignal


class Network(QObject):
    __slots__ = 'mzs', 'spectra', 'scores', 'graph', 'options', '_infos', '_interactions', \
                'db_results', 'mappings', 'lazyloaded'

    infosAboutToChange = pyqtSignal()
    infosChanged = pyqtSignal()
    interactionsAboutToChange = pyqtSignal()
    interactionsChanged = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._interactions = None
        self._infos = None
        self.db_results = {}
        self.lazyloaded = False

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
        return self._interactions

    @interactions.setter
    def interactions(self, data):
        if data is not None:
            self.interactionsAboutToChange.emit()
        self._interactions = data
        if data is not None:
            self.interactionsChanged.emit()
