import operator
import itertools
from ctypes import c_float
from functools import partial

import numpy as np
import multiprocessing as mp

from .base_worker import BaseWorker


class Spectrum:
    '''Object representing a MS/MS spectrum.
    
    Attributes:
        data (np.array): 2D-array of floats with 2 columns holding m/z values and intensities, respectively.
        mz_parent (float): m/z ratio of parent ion.
    '''
    # Indexes for array
    MZ = 0
    INTENSITY = 1
    
    def __init__(self, id, mz_parent, data, options, use_multiprocessing=False):
        self.id = id
        self.mz_parent = mz_parent
        
        # Filter low mass peaks
        data = data[data[:,Spectrum.MZ]>=50]
        
        # Filter peaks close to the parent ion's m/z
        data = data[np.logical_or(data[:,Spectrum.MZ]<=mz_parent-options.parent_filter_tolerance, data[:,Spectrum.MZ]>=mz_parent+options.parent_filter_tolerance)]
        
        # Keep only peaks higher than threshold
        data = data[data[:,Spectrum.INTENSITY] >= options.min_intensity * data[:,Spectrum.INTENSITY].max() / 100]
        
        # Window rank filter
        data = data[np.argsort(data[:,Spectrum.INTENSITY])]
        mz_ratios = data[:,Spectrum.MZ]
        mask = np.logical_and(mz_ratios>=mz_ratios[:,None]-options.matched_peaks_window, mz_ratios<=mz_ratios[:,None]+options.matched_peaks_window)
        data = data[np.array([mz_ratios[i] in mz_ratios[mask[i]][-options.min_matched_peaks_search:] for i in range(mask.shape[0])])]
        
        # Use square root of intensities to minimize/maximize effects of high/low intensity peaks
        data[:,Spectrum.INTENSITY] = np.sqrt(data[:,Spectrum.INTENSITY]) * 10
        
        # Normalize data to norm 1
        data[:,Spectrum.INTENSITY] = data[:,Spectrum.INTENSITY] / np.sqrt(data[:,Spectrum.INTENSITY] @ data[:,Spectrum.INTENSITY])
        
        if use_multiprocessing:
            self._data = mp.RawArray(c_float, data.size)
            self.data = np.frombuffer(self._data, dtype=np.float32)
            self.data[:] = data.ravel()
            self.data = self.data.reshape(data.shape)
        else:
            self.data = data
        
        
    def __repr__(self):
        return 'Spectrum({}, {:.2f})'.format(self.id, self.mz_parent)
    

class CosineComputationOptions:
    """Class containing spectra cosine scores options.

    Attributes:
        mz_tolerance (float): in Da. Default value = 0.02
        min_intensity (int): relative minimum intensity in percentage Default value = 0
        parent_filter_tolerance (int): in Da. Default value = 17
        min_matched_peaks (int): Minimum number of common peaks between two spectra. Default value = 4
        min_matched_peaks_search (int): Window rank filter's parameters: for each peak in the spectrum, 
            it is kept only if it is in top `min_matched_peaks_search` in the +/-`matched_peaks_window` window
            Default value = 6
        matched_peaks_window (int): in Da. Default value = 50

    """
    
    __slots__ = ('mz_tolerance', 'min_intensity', 'parent_filter_tolerance',
                'min_matched_peaks', 'min_matched_peaks_search',
                'matched_peaks_window')

    def __init__(self):
        self.mz_tolerance = 0.02
        self.min_intensity = 0
        self.parent_filter_tolerance = 17
        self.min_matched_peaks = 4
        self.min_matched_peaks_search = 6
        self.matched_peaks_window = 50

        
def grouper(iterable, n, fillvalue=None):
    '''Collect data into fixed-length chunks or blocks'''
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return itertools.zip_longest(*args, fillvalue=fillvalue)

    
def init(spectra, num, matrix):
    '''Initialization function for multiprocessing'''
    global spec_list, num_spectra, scores_matrix
    
    spec_list = spectra
    num_spectra = num
    scores_matrix = matrix

        
def batch_cosine_scores(ids, tolerance):
    '''Compute a bach of cosine scores and write them directly into the results matrix.
    
    Args:
        ids (list of int): ids of spectra to process.
        tolerance (float): m/z window allowed to consider two m/z as the same.
        
    Returns:
        int: Number of scores calculated'''
    m = np.frombuffer(scores_matrix, dtype=np.float32)
    m = m.reshape((num_spectra, num_spectra))
    
    counter = 0
    for spec_id, ref_id in ids:
        if spec_id is None or ref_id is None:
            break
        
        m[spec_id, ref_id] = cosine_score(spec_list[spec_id],
                             spec_list[ref_id], tolerance)
        counter += 1
        
    return counter

    
def cosine_score(spectrum1, spectrum2, tolerance, min_matched_peaks):
    '''Compute cosine score from two spectra and a given m/z tolerance.
    
    Args:
        spectrum1 (Spectrum): First spectrum to compare.
        spectrum2 (Spectrum): Second spectrum to compare.
        tolerance (float): m/z window allowed to consider two m/z as the same.
        
    Returns:
        float: Cosine similarity between spectrum1 and spectrum2.'''
    
    dm = spectrum1.mz_parent - spectrum2.mz_parent

    diff_matrix = spectrum2.data[:,Spectrum.MZ] - spectrum1.data[:,Spectrum.MZ][:,None]
    if dm != 0.:
        idxMatched1, idxMatched2 = np.where( \
            np.logical_or(np.abs(diff_matrix) <= tolerance,
                          np.abs(diff_matrix+dm) <= tolerance))
    else:
        idxMatched1, idxMatched2 = np.where(np.abs(diff_matrix) <= tolerance)
    del diff_matrix

    if idxMatched1.size + idxMatched2.size == 0:
        return 0.
    
    peakUsed1 = [False] * spectrum1.data.size
    peakUsed2 = [False] * spectrum2.data.size
    
    peakMatches = []
    for i in range(idxMatched1.size):
        peakMatches.append((idxMatched1[i], idxMatched2[i], spectrum1.data[idxMatched1[i],Spectrum.INTENSITY] * spectrum2.data[idxMatched2[i],Spectrum.INTENSITY]))
    
    peakMatches = sorted(peakMatches, key=operator.itemgetter(2), reverse=True)
    
    score = 0.
    numMatchedPeaks = 0
    for i in range(len(peakMatches)):
        if not peakUsed1[peakMatches[i][0]] and not peakUsed2[peakMatches[i][1]]:
            score += peakMatches[i][2]
            peakUsed1[peakMatches[i][0]] = True
            peakUsed2[peakMatches[i][1]] = True
            numMatchedPeaks += 1
            
    if numMatchedPeaks < min_matched_peaks:
        return 0.
        
    return score
    
    
class ComputeScoresWorker(BaseWorker):
    '''Generate a network from a MGF file.
    '''
    
    def __init__(self, spectra, use_multiprocessing, options):
        super().__init__()
        self._spectra = spectra
        self.use_multiprocessing = use_multiprocessing
        self.options = options


    def run(self):
        num_spectra = len(self._spectra)
        num_scores_to_compute = num_spectra * (num_spectra-1) // 2

        
        # Compute cosine scores            
        if self.use_multiprocessing:
            scores_matrix = mp.RawArray(c_float, num_spectra**2)
            m = np.frombuffer(scores_matrix, dtype=np.float32)
            m[:] = 0
            
            combinations = itertools.combinations(range(num_spectra), 2)
            max_workers = mp.cpu_count()
            pool = mp.Pool(max_workers, initializer=init, initargs=(self._spectra, num_spectra, scores_matrix))
            
            groups = grouper(combinations, 
                            min(10000, num_scores_to_compute//max_workers),
                            fillvalue=(None, None))
            compute = partial(batch_cosine_scores, self.options.mz_tolerance, self.options.min_matched_peaks)
            for result in pool.imap_unordered(compute, groups):
                if self._should_stop:
                    self.canceled.emit()
                    return False
                self.updated.emit(result)
        else:
            scores_matrix = np.zeros((num_spectra, num_spectra), dtype=np.float32)
            
            combinations = itertools.combinations(self._spectra, 2)
            for spectrum1, spectrum2 in combinations:
                if self._should_stop:
                    self.canceled.emit()
                    return False
                    
                score = cosine_score(spectrum1, spectrum2, self.options.mz_tolerance, self.options.min_matched_peaks)
                    
                scores_matrix[spectrum1.id, spectrum2.id] = score
                self.updated.emit(1)

                    
        # Fill matrice with predictable values
        # We compute only the upper triangle of the matrix as the matrix is symmetric
        # We also do not need to compute identity scores as, by definition, it has to be 1
        if self.use_multiprocessing:
            scores_matrix = np.frombuffer(scores_matrix, dtype=np.float32)
            scores_matrix = scores_matrix.reshape((num_spectra, num_spectra))
        
        scores_matrix = scores_matrix + scores_matrix.T
        np.fill_diagonal(scores_matrix, 1)
        scores_matrix[scores_matrix>1] = 1

        self._result = scores_matrix
        self.finished.emit()
