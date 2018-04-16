import numpy as np

from pyteomics import mgf
from pyteomics.auxiliary import PyteomicsError

from .base import BaseWorker
from .cosine import Spectrum

    
class ReadMGFWorker(BaseWorker):
    
    def __init__(self, filename, options):
        super().__init__()
        self.filename = filename
        self.options = options
        self.iterative_update = True
        self.max = 0
        self.desc = 'Reading MGF...'

    def run(self):
        spectra = []
        try:
            for id, entry in enumerate(mgf.read(self.filename, convert_arrays=1, read_charges=False, dtype=np.float32)):
                if self.isStopped():
                    self.canceled.emit()
                    return

                mz_parent = entry['params']['pepmass']
                mz_parent = mz_parent[0] if type(mz_parent) is tuple else mz_parent  # Parent ion mass is read as a tuple
                data = np.column_stack((entry['m/z array'], entry['intensity array']))
                spectrum = Spectrum(id, mz_parent, data)
                spectrum.filter_data(options=self.options)
                spectra.append(spectrum)

                self.updated.emit(1)
        except PyteomicsError as e:
            self.error.emit(e)
            return
            
        return spectra
