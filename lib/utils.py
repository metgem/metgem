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
        if not item in self:
            raise AttributeError("'{}' object has no attribute '{}'".format(self.__class__.__name__, item))
        super().__setitem__(item, value)

    def __getstate__(self):
        return dict(self)

    def __setstate__(self, state):
        super().update(state)

    def __reduce__(self):
        return self.__class__, (), self.__getstate__()
        
    def __dir__(self):
        return super().__dir__() + [str(k) for k in self.keys()]

    def update(self, data, **kwargs):
        data = {k: v for k, v in data.items() if k in self}
        super().update(data)

    def copy(self):
        return AttrDict(self)
