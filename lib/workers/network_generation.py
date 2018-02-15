import operator
import itertools
import time
from ctypes import c_float
from functools import partial

import numpy as np
import multiprocessing as mp

from tqdm import tqdm    
from pyteomics import mgf

from .base_worker import BaseWorker

PARENT_FILTER_TOLERANCE = 17 # Da
PAIRS_MIN_COSINE = 0.65 # Minimum cosine score for network generation
MZ_TOLERANCE = 0.02 # Da
MIN_MATCHED_PEAKS = 4 # Minimum number of common peaks between two spectra
TOPK = 10 # Maximum numbers of edges for each nodes in the network
MIN_INTENSITY = 0 # relative minimum intensity in percentage
MIN_MATCHED_PEAKS_SEARCH = 6 # Window rank filter's parameters: for each peak in the spectrum, it is kept only if it is in top MIN_MATCHED_PEAKS_SEARCH in the +/-MATCHED_PEAKS_WINDOW window
MATCHED_PEAKS_WINDOW = 50 # Da


# Helper functions
def pretty_time_delta(seconds):
    '''Format time in a human readable way'''
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if days > 0:
        return '{:.0f}d{:.0f}h{:.0f}m{:.1f}s'.format(days, hours, minutes, seconds)
    elif hours > 0:
        return '{:.0f}h{:.0f}m{:.1f}s'.format(hours, minutes, seconds)
    elif minutes > 0:
        return '{:.0f}m{:.1f}s'.format(minutes, seconds)
    else:
        return '{:.1f}s'.format(seconds,)
        

def read_mgf(filename, use_multiprocessing=False):
    '''Read a file in Mascot Generic Format an return Spectrum objects'''
    for id, entry in enumerate(mgf.read(filename, convert_arrays=1, read_charges=False, dtype=np.float32)):
        mz_parent = entry['params']['pepmass']
        mz_parent = mz_parent[0] if type(mz_parent) is tuple else mz_parent #Parent ion mass is read as a tuple
        data = np.column_stack((entry['m/z array'], entry['intensity array']))
        yield Spectrum(id, mz_parent, data, min_intensity=MIN_INTENSITY, use_multiprocessing=use_multiprocessing)

        
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

    
class Spectrum:
    '''Object representing a MS/MS spectrum.
    
    Attributes:
        data (np.array): 2D-array of floats with 2 columns holding m/z values and intensities, respectively.
        mz_parent (float): m/z ratio of parent ion.
    '''
    # Indexes for array
    MZ = 0
    INTENSITY = 1
    
    def __init__(self, id, mz_parent, data, min_intensity=5, use_multiprocessing=False):
        self.id = id
        self.mz_parent = mz_parent
        
        # Filter low mass peaks
        data = data[data[:,Spectrum.MZ]>=50]
        
        # Filter peaks close to the parent ion's m/z
        data = data[np.logical_or(data[:,Spectrum.MZ]<=mz_parent-PARENT_FILTER_TOLERANCE, data[:,Spectrum.MZ]>=mz_parent+PARENT_FILTER_TOLERANCE)]
        
        # Keep only peaks higher than threshold
        data = data[data[:,Spectrum.INTENSITY] >= min_intensity * data[:,Spectrum.INTENSITY].max() / 100]
        
        # Window rank filter
        data = data[np.argsort(data[:,Spectrum.INTENSITY])]
        mz_ratios = data[:,Spectrum.MZ]
        mask = np.logical_and(mz_ratios>=mz_ratios[:,None]-MATCHED_PEAKS_WINDOW, mz_ratios<=mz_ratios[:,None]+MATCHED_PEAKS_WINDOW)
        data = data[np.array([mz_ratios[i] in mz_ratios[mask[i]][-MIN_MATCHED_PEAKS_SEARCH:] for i in range(mask.shape[0])])]
        
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

    
def cosine_score(spectrum1, spectrum2, tolerance):
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
            
    if numMatchedPeaks < MIN_MATCHED_PEAKS:
        return 0.
        
    return score
    
    
class ComputeScoresWorker(BaseWorker):
    '''Generate a network from a MGF file.
    '''
    
    def __init__(self, spectra, use_multiprocessing):
        super().__init__()
        self._spectra = spectra
        self.use_multiprocessing = use_multiprocessing


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
            compute = partial(batch_cosine_scores, tolerance=MZ_TOLERANCE)
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
                    
                score = cosine_score(spectrum1, spectrum2, MZ_TOLERANCE)
                    
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
        

        self._result = scores_matrix
        self.finished.emit()
    
    
def generate_network(scores_matrix, spectra, use_self_loops=True):
    interactions = []
    
    num_spectra = len(spectra)
    
    np.fill_diagonal(scores_matrix, 0)
    triu = np.triu(scores_matrix)
    triu[triu<=PAIRS_MIN_COSINE] = 0
    for i in range(num_spectra):
        # indexes = np.argpartition(triu[i,], -TOPK)[-TOPK:] # Should be faster and give the same results
        indexes = np.argsort(triu[i,])[-TOPK:]
        indexes = indexes[triu[i, indexes] > 0]
            
        for index in indexes:
            interactions.append((i, index,
                spectra[i].mz_parent-spectra[index].mz_parent, triu[i, index]))
    
    interactions = np.array(interactions, dtype=[('Source', int), ('Target', int), ('Delta MZ', np.float32), ('Cosine', np.float32)])
    interactions = interactions[np.argsort(interactions, order='Cosine')[::-1]]

    # Top K algorithm, keep only edges between two nodes if and only if each of the node appeared in each other’s respective top k most similar nodes
    mask = np.zeros(interactions.shape[0], dtype=bool)
    for i, (x, y, _, _) in enumerate(interactions):
        x_ind = np.where(np.logical_or(interactions['Source']==x, interactions['Target']==x))[0][:TOPK]
        y_ind = np.where(np.logical_or(interactions['Source']==y, interactions['Target']==y))[0][:TOPK]
        if (x in interactions[y_ind]['Source'] or x in interactions[y_ind]['Target']) \
          and (y in interactions[x_ind]['Source'] or y in interactions[x_ind]['Target']):
            mask[i] = True
    interactions = interactions[mask]
    
    # Add selfloops for individual nodes without neighbors
    if use_self_loops:
        unique = set(itertools.chain.from_iterable((x['Source'], x['Target']) for x in interactions))
        selfloops = set(range(0, triu.shape[0])) - unique
        size = interactions.shape[0]
        interactions.resize((size + len(selfloops)))
        interactions[size:] = [(i, i, 0., 1.) for i in selfloops]

    return interactions