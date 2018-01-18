from PyQt5.QtCore import QObject, pyqtSignal

class BaseWorker(QObject):
    
    finished = pyqtSignal()
    canceled = pyqtSignal()
    updated = pyqtSignal(int)
    error = pyqtSignal(Exception)
    
    def __init__(self):
        super().__init__()
        
        self._should_stop = False
        self._result = None
        
    
    def run(self):
        pass
    
    
    def stop(self):
        self._should_stop = True
        
        
    def result(self):
        return self._result