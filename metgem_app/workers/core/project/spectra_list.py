from .mnz import MnzFile


class SpectraList(list):

    def __init__(self, filename):
        super().__init__()
        self.load(filename)

    def __getitem__(self, index):
        data = super().__getitem__(index)
        if isinstance(data, int):
            data = self._file[f'0/spectra/{data}']
            super().__setitem__(index, data)

        return data

    def __del__(self):
        self.close()

    def close(self):
        self._file.close()

    # noinspection PyAttributeOutsideInit
    def load(self, filename):
        self._file = MnzFile(filename, 'r')

        self.clear()
        for s in self._file['0/spectra/index.json']:
            self.append(s['id'])

