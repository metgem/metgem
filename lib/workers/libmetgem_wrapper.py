MZ = 0
INTENSITY = 1


def human_readable_data(data):
    data = data.copy()
    data[:, INTENSITY] = data[:, INTENSITY] ** 2
    data[:, INTENSITY] = data[:, INTENSITY] / data[:, INTENSITY].max() * 100
    return data


try:
    from libmetgem.cosine import cosine_score, compute_distance_matrix, compare_spectra_to_reference
    from libmetgem import mgf
    from libmetgem.filter import filter_data, filter_data_multi
    from libmetgem.database import query

    USE_LIBMETGEM = True
except ImportError:
    import time
    import numpy as np
    import operator
    import sqlite3
    from pyteomics import mgf
    from pyteomics.auxiliary import PyteomicsError

    USE_LIBMETGEM = False

    def cosine_score(spectrum1_mz, spectrum1_data, spectrum2_mz, spectrum2_data, mz_tolerance, min_matched_peaks):
        """Compute cosine score from two spectra.

        Returns:
            float: Cosine similarity between spectrum1 and spectrum2."""

        dm = spectrum1_mz - spectrum2_mz

        diff_matrix = spectrum2_data[:, 0] - spectrum1_data[:, 0][:, None]
        if dm != 0.:
            idxMatched1, idxMatched2 = np.where(
                np.logical_or(np.abs(diff_matrix) <= mz_tolerance,
                              np.abs(diff_matrix + dm) <= mz_tolerance))
        else:
            idxMatched1, idxMatched2 = np.where(np.abs(diff_matrix) <= mz_tolerance)
        del diff_matrix

        if idxMatched1.size + idxMatched2.size == 0:
            return 0.

        peakUsed1 = [False] * spectrum1_data.size
        peakUsed2 = [False] * spectrum2_data.size

        peakMatches = []
        for i in range(idxMatched1.size):
            peakMatches.append((idxMatched1[i], idxMatched2[i],
                                spectrum1_data[idxMatched1[i], 1] * spectrum2_data[
                                    idxMatched2[i], 1]))

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

    def compute_distance_matrix(mzs, spectra, mz_tolerance, min_matched_peaks, callback=None):
        size = len(mzs)
        has_callback = callback is not None
        matrix = np.empty((size, size), dtype=np.float32)
        for i in range(size):
            for j in range(i):
                matrix[i, j] = matrix[j, i] = cosine_score(mzs[i], spectra[i], mzs[j], spectra[j],
                                                           mz_tolerance, min_matched_peaks)
                if has_callback:
                    callback(size-1)
        np.fill_diagonal(matrix, 1)
        if has_callback:
            callback(size)
        matrix[matrix > 1] = 1
        return matrix

    def compare_spectra_to_reference(mzs, spectra, mzref, dataref, mz_tolerance, min_matched_peaks, callback=None):
        size = len(mzs)
        has_callback = callback is not None
        result = np.empty((size,), dtype=np.float32)

        for i in range(len(spectra)):
            result[i] = cosine_score(mzs[i], spectra[i], mzref, dataref, mz_tolerance, min_matched_peaks)
            if has_callback and i % 10 == 0:
                callback(10)

        if has_callback and size % 10 != 0:
            callback(size % 10)

        result[result > 1] = 1

        return result

    def filter_data(mz_parent, data, min_intensity, parent_filter_tolerance, matched_peaks_window,
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

    def filter_data_multi(mzvec, datavec, min_intensity, parent_filter_tolerance,
                          matched_peaks_window, min_matched_peaks_search, callback=None):
        size = len(mzvec)
        has_callback = callback is not None
        result = []

        for i in range(size):
            result.append(filter_data(mzvec[i], datavec[i], min_intensity, parent_filter_tolerance,
                                      matched_peaks_window, min_matched_peaks_search))
            if has_callback and i % 10 == 0:
                callback(10)

        if has_callback and size % 10 != 0:
            callback(size % 10)

        return result

    def query(fname: str, indices: list, mzvec: list, datavec: list, databases: list, mz_tolerance: float,
              min_matched_peaks: int, min_intensity: int, parent_filter_tolerance: int, matched_peaks_window: int,
              min_matched_peaks_search: int, min_cosine: float, analog_mz_tolerance: float=0.,
              positive_polarity: bool=True, callback=None):

        size = len(mzvec)

        conn = sqlite3.connect(f'file:{fname}?mode=ro', uri=True)

        # Get min/max mz values in list
        mz_min = min(mzvec)
        mz_max = max(mzvec)

        # Set tolerance
        tol = analog_mz_tolerance if analog_mz_tolerance > 0 else mz_tolerance

        if len(databases) > 0:
            dbs = ','.join([str(x) for x in databases])
            c = conn.execute("SELECT id, pepmass, name, peaks, bank_id FROM spectra WHERE bank_id IN ?4 AND (positive = ?1 OR positive IS NULL) AND PEPMASS BETWEEN ?2 AND ?3",
                             (positive_polarity, mz_min-tol, mz_max+tol, dbs))
        else:
            c = conn.execute("SELECT id, pepmass, name, peaks, bank_id FROM spectra WHERE (positive = ?1 OR positive IS NULL) AND PEPMASS BETWEEN ?2 AND ?3",
                             (positive_polarity, mz_min-tol, mz_max+tol))

        results = c.fetchall()
        max_rows = len(results)

        # Loop on results
        rows = 0
        qr = {}
        t = time.time()
        for row in results:
            pepmass = row[1]
            ids = []
            if analog_mz_tolerance > 0:
                for i in range(size):
                    if mzvec[i] - analog_mz_tolerance <= pepmass <= mzvec[i] + analog_mz_tolerance \
                            and not (mzvec[i] - mz_tolerance <= pepmass <= mzvec[i] + mz_tolerance):
                        ids.append(i)
            else:
                for i in range(size):
                    if mzvec[i] - mz_tolerance <= pepmass <= mzvec[i] + mz_tolerance:
                        ids.append(i)

            if len(ids) > 0:
                peaks = np.frombuffer(row[3], dtype='<f4').reshape(-1, 2)
                if len(peaks) > 0:
                    filtered = filter_data(pepmass, peaks, min_intensity, parent_filter_tolerance,
                                           matched_peaks_window, min_matched_peaks_search)
                    for i in ids:
                        score = cosine_score(pepmass, filtered, mzvec[i], datavec[i],
                                             mz_tolerance, min_matched_peaks)
                        if score > min_cosine:
                            r = {'score': score, 'id': row[0], 'bank_id': row[4], 'name': row[2]}
                            try:
                                qr[indices[i]].append(r)
                            except KeyError:
                                qr[indices[i]] = [r]

            rows += 1
            if callback is not None and time.time() - t > 0.02:
                t = time.time()
                if not callback(rows / max_rows * 100):
                    return

        if callback is not None and rows % size != 0:
            callback(100)

        return qr
