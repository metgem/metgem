import sys

from sklearn.manifold import TSNE

from .base_worker import BaseWorker


class UserRequestedStopError(Exception):
    '''Raised if user request to stop a worker's process'''
    
    
class TSNEWorker(BaseWorker):
    
    def __init__(self, scores):
        super().__init__()
        self._scores = scores


    def run(self):
        sys.stdout = self
        try:
            self._result = TSNE(learning_rate=200, early_exaggeration=12, perplexity=6, verbose=2, random_state=0, metric='precomputed', method='exact').fit_transform(self._scores)
        except UserRequestedStopError:
            self.canceled.emit()
            return False
            
        sys.stdout = sys.__stdout__
        self.finished.emit()
        

    def write(self, s):
        '''Method used to follow progress of processing.'''
        if self._should_stop:
            raise UserRequestedStopError
        elif 'Iteration' in s:
            s = s.split(' Iteration ')[1]
            if ': error =' in s:
                s = s.split(': error =')[0]
            try:
                self.updated.emit(int(s))
            except ValueError:
                pass
                
            
    def flush(self):
        '''Method used to fake a file-like object.'''
        pass