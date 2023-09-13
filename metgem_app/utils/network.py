import uuid

import pandas as pd
from metgem_app.utils.qt import QObject, Signal


def generate_id(type: str):
    return f"{type}_{uuid.uuid4()}"


class Network(QObject):
    infosAboutToChange = Signal()
    infosChanged = Signal()

    def __init__(self):
        super().__init__()
        self._interactions = pd.DataFrame()
        self._infos = None
        self.db_results = {}
        self.columns_mappings = {}
        self.lazyloaded = False

    @property
    def infos(self):
        return self._infos

    @infos.setter
    def infos(self, data):
        self.infosAboutToChange.emit()
        self._infos = data
        self.infosChanged.emit()

