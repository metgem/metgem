import numpy as np

from pyteomics import mgf

from .base_worker import BaseWorker 
from .cosine import Spectrum

    
class ReadMGFWorker(BaseWorker):
    
    def __init__(self, filename, options):
        super().__init__()
        self.filename = filename
        self.options = options


    def run(self):
        spectra = []
        for id, entry in enumerate(mgf.read(self.filename, convert_arrays=1, read_charges=False, dtype=np.float32)):
            if self._should_stop:
                self.canceled.emit()
                return False
            
            mz_parent = entry['params']['pepmass']
            mz_parent = mz_parent[0] if type(mz_parent) is tuple else mz_parent #Parent ion mass is read as a tuple
            data = np.column_stack((entry['m/z array'], entry['intensity array']))
            spectrum = Spectrum(id, mz_parent, data)
            spectrum.filter_data(options=self.options)
            spectra.append(spectrum)
            
            self.updated.emit(1)
            
        self._result = spectra
        self.finished.emit()
