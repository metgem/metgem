from PyQt5.QtCore import QThread, pyqtSignal, QObject

class BaseWorker(QObject):
    
    finished = pyqtSignal()
    canceled = pyqtSignal()
    error = pyqtSignal(Exception)
    
    def __init__(self):
        super().__init__()
        
        self._should_stop = False
        self._result = None
        
        self._thread = QThread()
        
        
    def start(self):
        self.moveToThread(self._thread)
        self._thread.started.connect(self.run)
        self._thread.start()
        
        
    def run(self):
        pass
    
    
    def stop(self):
        self._should_stop = True
        
        
    def result(self):
        return self._result