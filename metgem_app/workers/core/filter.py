from typing import List, Tuple

import numpy as np
from libmetgem import MZ

from metgem_app.workers.base import BaseWorker

FRAGMENTS = 0
NEUTRAL_LOSSES = 1
MZ_PARENT = 2

ALL_CONDITIONS = 0
AT_LEAST_ONE_CONDITION = 1


class FilterWorker(BaseWorker):
    def __init__(self, mzs: List[float], spectra: List[np.ndarray],
                 values: List[Tuple[int, float, float]], condition_criterium: int = ALL_CONDITIONS):
        super().__init__()
        self.mzs = mzs
        self.spectra = spectra
        self.values = values
        self.condition_criterium = condition_criterium
        self.max = len(self.spectra)
        self.desc = 'Filtering nodes...'

    def run(self):
        nodes = set()
        num_criteria = len(self.values)
        for i in range(len(self.spectra)):
            mz_parent = self.mzs[i]
            spec = self.spectra[self.mzs.index[i]]
            criteria_matched = 0
            for type_, value, tol, unit in self.values:
                if type_ == MZ_PARENT:
                    arr = mz_parent
                elif type_ == NEUTRAL_LOSSES:
                    arr = mz_parent-spec[:, MZ]
                else:
                    arr = spec[:, MZ]
                kwargs = dict(atol=tol*1e-3, rtol=0.) if unit == "mDa" else dict(rtol=tol*1e-6, atol=0.)
                if np.any(np.isclose(arr, value, **kwargs)):
                    if self.condition_criterium == AT_LEAST_ONE_CONDITION:
                        nodes.add(i)
                        break
                    else:
                        criteria_matched += 1
            if self.condition_criterium == ALL_CONDITIONS and criteria_matched == num_criteria:
                nodes.add(i)

            self.updated.emit(i)

        if not self.isStopped():
            return list(nodes)
        else:
            self.canceled.emit()
