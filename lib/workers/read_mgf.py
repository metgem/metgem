import numpy as np

from .base import BaseWorker

try:
    from cosinelib import mgf
    from cosinelib.filter import filter_data
    USE_COSINELIB = True
except ImportError:
    from pyteomics import mgf
    from pyteomics.auxiliary import PyteomicsError
    from .cosine import MZ, INTENSITY
    USE_COSINELIB = False

    def filter_data(data, mz_parent, min_intensity, parent_filter_tolerance, matched_peaks_window,
                    min_matched_peaks_search):

        # Filter low mass peaks
        data = data[data[:, MZ] >= 50]

        # Filter peaks close to the parent ion's m/z
        data = data[np.logical_or(data[:, MZ] <= mz_parent - parent_filter_tolerance,
                                  data[:, MZ] >= mz_parent + parent_filter_tolerance)]

        if data.size > 0:
            # Keep only peaks higher than threshold
            data = data[data[:, INTENSITY] >= min_intensity * data[:, INTENSITY].max() / 100]

        if data.size > 0:
            # Window rank filter
            data = data[np.argsort(data[:, INTENSITY])]

            if data.size > 0:
                mz_ratios = data[:, MZ]
                mask = np.logical_and(mz_ratios >= mz_ratios[:, None] - matched_peaks_window,
                                      mz_ratios <= mz_ratios[:, None] + matched_peaks_window)
                data = data[np.array([mz_ratios[i] in mz_ratios[mask[i]][-min_matched_peaks_search:]
                                      for i in range(mask.shape[0])])]
                del mask

                if data.size > 0:
                    # Use square root of intensities to minimize/maximize effects of high/low intensity peaks
                    data[:, INTENSITY] = np.sqrt(data[:, INTENSITY]) * 10

                    # Normalize data to norm 1
                    data[:, INTENSITY] = data[:, INTENSITY] / np.sqrt(data[:, INTENSITY] @ data[:, INTENSITY])

        return data

    
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
        if USE_COSINELIB:
            for params, data in mgf.read(self.filename, ignore_unknown=True):
                if self.isStopped():
                    self.canceled.emit()
                    return

                mz_parent = params['pepmass']
                data = filter_data(data, mz_parent, self.options.min_intensity,
                                   self.options.parent_filter_tolerance,
                                   self.options.matched_peaks_window,
                                   self.options.min_matched_peaks_search)
                if data.size > 0:
                    spectra.append(data)
                    mzs.append(mz_parent)
                self.updated.emit(1)
        else:
            try:
                for entry in mgf.read(self.filename, convert_arrays=1, read_charges=False, dtype=np.float32):
                    if self.isStopped():
                        self.canceled.emit()
                        return

                    mz_parent = entry['params']['pepmass']
                    mz_parent = mz_parent[0] if type(
                        mz_parent) is tuple else mz_parent  # Parent ion mass is read as a tuple

                    data = np.column_stack((entry['m/z array'], entry['intensity array']))
                    data = filter_data(data, mz_parent, self.options.min_intensity,
                                       self.options.parent_filter_tolerance,
                                       self.options.matched_peaks_window,
                                       self.options.min_matched_peaks_search)
                    if data.size > 0:
                        spectra.append(data)
                        mzs.append(mz_parent)

                    self.updated.emit(1)
            except PyteomicsError as e:
                self.error.emit(e)
                return
            
        return mzs, spectra
