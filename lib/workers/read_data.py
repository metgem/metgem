from .base import BaseWorker

from libmetgem.mgf import read as read_mgf
from libmetgem.msp import read as read_msp
from libmetgem.filter import filter_data_multi

import os


class ReadDataWorker(BaseWorker):

    def __init__(self, filename, options):
        super().__init__()
        self.filename = filename
        self.ext = os.path.splitext(filename)[1].lower()
        self.options = options
        self.max = 0
        self.iterative_update = True
        self.desc = 'Reading data file...'

    def run(self):
        mzs = []
        spectra = []

        min_intensity = self.options.min_intensity
        parent_filter_tolerance = self.options.parent_filter_tolerance
        matched_peaks_window = self.options.matched_peaks_window
        min_matched_peaks_search = self.options.min_matched_peaks_search
        is_ms1_data = self.options.is_ms1_data

        if self.ext == '.mgf':
            read = read_mgf
            mz_keys = ['pepmass']
        elif self.ext == '.msp':
            read = read_msp
            mz_keys = ['precursormz', 'exactmass']
        else:
            self.error.emit(NotImplementedError())
            return

        for params, data in read(self.filename, ignore_unknown=True):
            if self.isStopped():
                self.canceled.emit()
                return

            if not is_ms1_data:
                for key in mz_keys:
                    try:
                        mz_parent = params[key]
                    except KeyError as e:
                        pass
                mzs.append(mz_parent)
            else:
                mzs.append(0)

            try:
                self.error.emit(e)
                return
            except UnboundLocalError:
                pass

            spectra.append(data)

        spectra = filter_data_multi(mzs, spectra, min_intensity, parent_filter_tolerance,
                                    matched_peaks_window, min_matched_peaks_search)

        if is_ms1_data:
            return [], spectra
        else:
            return mzs, spectra
