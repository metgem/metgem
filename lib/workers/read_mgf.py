import numpy as np

from .base import BaseWorker
from .libmetgem_wrapper import mgf, filter_data_multi, USE_LIBMETGEM
if not USE_LIBMETGEM:
    from .libmetgem_wrapper import PyteomicsError


class ReadMGFWorker(BaseWorker):
    
    def __init__(self, filename, options):
        super().__init__()
        self.filename = filename
        self.options = options
        self.iterative_update = True
        self.max = 0
        self.desc = 'Reading MGF...'

    def run(self):
        mzs = []
        spectra = []

        min_intensity = self.options.min_intensity
        parent_filter_tolerance = self.options.parent_filter_tolerance
        matched_peaks_window = self.options.matched_peaks_window
        min_matched_peaks_search = self.options.min_matched_peaks_search

        if USE_LIBMETGEM:
            for params, data in mgf.read(self.filename, ignore_unknown=True):
                if self.isStopped():
                    self.canceled.emit()
                    return

                try:
                    mz_parent = params['pepmass']
                except KeyError as e:
                    self.error.emit(e)
                    return

                spectra.append(data)
                mzs.append(mz_parent)
        else:
            try:
                for entry in mgf.read(self.filename, convert_arrays=1, read_charges=False, dtype=np.float32):
                    if self.isStopped():
                        self.canceled.emit()
                        return

                    try:
                        mz_parent = entry['params']['pepmass']
                    except KeyError as e:
                        self.error.emit(e)
                    mz_parent = mz_parent[0] if type(
                        mz_parent) is tuple else mz_parent  # Parent ion mass is read as a tuple

                    data = np.column_stack((entry['m/z array'], entry['intensity array']))
                    spectra.append(data)
                    mzs.append(mz_parent)
            except PyteomicsError as e:
                self.error.emit(e)
                return

        spectra = filter_data_multi(mzs, spectra, min_intensity, parent_filter_tolerance,
                                    matched_peaks_window, min_matched_peaks_search,)
            
        return mzs, spectra
