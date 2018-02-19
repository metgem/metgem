class AttrDict(dict):
    '''A dictionnary where item can be accessed as attributes'''
    
    def __getattr__(self, item):
        return self.__getitem__(item)
    
    def __setattr__(self, item, value):
        return self.__setitem__(item, value)
    
    def __setitem__(self, item, value):
        if not item in self.keys():
            raise AttributeError("'{}' object has no attribute '{}'".format(self.__class__.__name__, item))

    def __dir__(self):
        return super().__dir__() + [str(k) for k in self.keys()]