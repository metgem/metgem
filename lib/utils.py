class AttrDict(dict):
    """A dictionnary where item can be accessed as attributes"""
    
    def __getattr__(self, item):
        try:
            return self.__getitem__(item)
        except KeyError:
            raise AttributeError
    
    def __setattr__(self, item, value):
        return self.__setitem__(item, value)
    
    def __setitem__(self, item, value):
        # if len(self) > 0 and not item in self:
        #     raise AttributeError("'{}' object has no attribute '{}'".format(self.__class__.__name__, item))
        super().__setitem__(item, value)
        
    def update(self, data, **kwargs):
        data = {k: v for k, v in data.items() if k in self}
        super().update(data)
        
    def __dir__(self):
        return super().__dir__() + [str(k) for k in self.keys()]

    def copy(self):
        return AttrDict(self)
