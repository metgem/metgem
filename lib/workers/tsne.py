import sys
import io

from sklearn.manifold import TSNE

from .base_worker import BaseWorker
from ..utils import AttrDict
from ..errors import UserRequestedStopError

class TSNEVisualizationOptions(AttrDict):
    """Class containing TSNE visualization options.

    Attributes:
        perplexity (int): See TSNE documentation. Default value = 6 
        learning_rate (int): See TSNE documentation. Default value = 200

    """
    
    def __init__(self):
        super().__init__(perplexity=6,
                         learning_rate=200)

    
class ProgressStringIO(io.StringIO):

    def __init__(self, parent, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent = parent

    def write(self, s):
        '''Method used to follow progress of processing.'''
        if self.parent._should_stop:
            raise UserRequestedStopError()
        elif 'Iteration' in s:
            s = s.split(' Iteration ')[1]
            if ': error =' in s:
                s = s.split(': error =')[0]
            try:
                self.parent.updated.emit(int(s))
            except ValueError:
                pass

    
class TSNEWorker(BaseWorker):
    
    def __init__(self, scores, options):
        super().__init__()
        self._scores = scores
        self.options = options


    def run(self):
        sys.stdout = ProgressStringIO(self)
        try:
            self._result = TSNE(learning_rate=self.options.learning_rate, early_exaggeration=12, perplexity=self.options.perplexity, verbose=2, random_state=0, metric='precomputed', method='exact').fit_transform(self._scores)
        except UserRequestedStopError:
            sys.stdout = sys.__stdout__
            self.canceled.emit()
            return False
            
        sys.stdout = sys.__stdout__
        self.finished.emit()
