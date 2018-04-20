import os

import numpy as np

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from pyteomics import mgf

try:
    from .utils import grouper
    from .models import Base, Spectrum, Organism, Submitter, DataCollector, Instrument, Bank, Investigator
except ImportError:
    from utils import grouper
    from models import Base, Spectrum, Organism, Submitter, DataCollector, Instrument, Bank, Investigator


def create_session(filename=None, echo=False, drop_all=False):
    engine = create_engine(f'sqlite:///{filename}', echo=echo)
    Base.metadata.bind = engine

    if drop_all:
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)

    DBSession = sessionmaker(bind=engine)

    return DBSession()


def clean_string(string):
    if string is None:
        return None

    string = string.strip('"').strip("'")
    if string.lower().startswith('data deposited by '):
        string = string[18:]
    elif string.lower().startswith('data from'):
        string = string[9:]
    if string.lower() in ('n/a', 'na', 'no data', 'n/a-n/a', r'n\a') or not string:
        return None
    return string


def chunk_read_mgf(filename, chunk_size=1000):
    yield from grouper(mgf.read(filename, convert_arrays=1, read_charges=True, dtype=np.float32), n=chunk_size)


class DataBaseBuilder:
    def __init__(self, name, echo=False):
        self.name = name
        self.echo = echo

        fname = f'{self.name}.sqlite'
        self.bases = {'bank': Bank, 'organism': Organism, 'pi': Investigator,
                      'submituser': Submitter, 'datacollector': DataCollector,
                      'source_instrument': Instrument}

        self._uniques = {k: {} for k in self.bases.keys()}
        self._indexes = {k: 1 for k in self.bases.keys()}
        self._used_pkeys = None
        self._free_pkeys = []

        if os.path.exists(fname) and os.path.isfile(fname) and os.path.getsize(fname) > 0:
            self.session = create_session(fname, echo=self.echo)
            for k, v in self.bases.items():
                records = self.session.query(v).all()
                self._uniques[k] = {x.name: x.id for x in records}
                self._indexes[k] = records[-1].id + 1
            self._used_pkeys = (self.session.query(Spectrum).first().id,
                                self.session.query(Spectrum).order_by(Spectrum.id.desc()).first().id)
        else:
            self.session = create_session(fname, echo=self.echo, drop_all=True)

        # Create a generator for spectrum primary to make sure we don't use an already use primary key
        # We don't use auto-increment because, otherwise, primary keys will increase for each update
        # (and can quickly overflow)
        def gen_pkey():
            key = 1
            while True:
                if self._used_pkeys is not None and self._used_pkeys[0] <= key <= self._used_pkeys[1]:
                    use_key = False
                    for start, stop in self._free_pkeys:
                        if start <= key <= stop:
                            use_key = True
                            break
                    if use_key:
                        yield key
                    key += 1
                else:
                    yield key
                    key += 1
        self.spectrum_pkey = gen_pkey()

    def __enter__(self):
        return self

    def __exit__(self, type_, value, traceback):
        self.close()

    def close(self):
        for key, base in self.bases.items():
            self.session.query(base).delete()
            self.session.execute(base.__table__.insert(),
                                 [{'id': v, 'name': k} for k, v in self._uniques[key].items()])

        self.session.commit()
        self.session.execute('vacuum')
        self.session.close()
        self.session.bind.dispose()

    def add_bank(self, mgf_path):
        bank = os.path.splitext(os.path.basename(mgf_path))[0]
        if bank in self._uniques['bank']:
            print(bank, self._uniques['bank'][bank])
            q = self.session.query(Spectrum).filter(Spectrum.bank_id == self._uniques['bank'][bank])
            if q.count() > 0:
                self._free_pkeys.append((q.first().id, q.order_by(Spectrum.id.desc()).first().id))
                q.delete()
                self.session.flush()
        else:
            print('new bank', bank, self._indexes['bank'])
            self._uniques['bank'][bank] = self._indexes['bank']

        for batch in chunk_read_mgf(mgf_path, 1000):  # Read mgf file by batch of 1000 spectra
            spectra = []

            for entry in batch:
                # If entry is None, we are in a non-complete batch (end of file), just break
                if entry is None:
                    break

                params = entry['params']

                # Set-up a dictionary with all the values needed to build a Spectrum object
                spectrum = {
                            'id': next(self.spectrum_pkey),
                            'bank_id': self._uniques['bank'][bank],
                            'pepmass': float(params.get('pepmass', [-1])[0]),
                            'mslevel': int(params.get('mslevel', 0)),
                            'positive': params.get('ionmode', 'Positive').lower() == 'positive',
                            'charge': params.get('charge', [1])[0],
                            'name': params.get('name', None),
                            'inchi': clean_string(params.get('inchi', None)),
                            'inchiaux': clean_string(params.get('inchiaux', None)),
                            'smiles': clean_string(params.get('smiles', None)),
                            'pubmed': clean_string(params.get('pubmed', None)),
                            'submituser': clean_string(params.get('inchi', None)),
                            'libraryquality': int(params.get('libraryquality', 0)),
                            'spectrumid': clean_string(params.get('spectrumid', None))
                           }

                # Add foreign keys
                for key in ('organism', 'pi', 'submituser', 'datacollector', 'source_instrument'):
                    value = clean_string(params.get(key, None))
                    if value is not None:
                        if value not in self._uniques[key]:
                            self._uniques[key][value] = self._indexes[key]
                            self._indexes[key] += 1
                        spectrum[f'{key}_id'] = self._uniques[key][value]
                    else:
                        spectrum[f'{key}_id'] = None

                # build a list of dictionnaries representing peaks
                mz = entry.get('m/z array', None)
                intensity = entry.get('intensity array', None)
                if mz is not None and intensity is not None and mz.size > 0 and intensity.size > 0:
                    intensity = intensity / intensity.max() * 100
                    peaks = np.column_stack((mz, intensity))
                    spectrum['peaks'] = peaks
                else:
                    spectrum['peaks'] = np.array([], dtype=np.float32)

                spectra.append(spectrum)

            # Add spectra and peaks
            # We can't use ORM because we have a lot of insertions to do
            # See http://docs.sqlalchemy.org/en/latest/faq/performance.html#i-m-inserting-400-000-rows-with-the-orm-and-it-s-really-slow
            self.session.execute(Spectrum.__table__.insert(), spectra)
            self.session.flush()

        self.session.commit()
        self._indexes['bank'] += 1


class SpectraLibrary:

    def __init__(self, database, echo=False):
        self.database = database
        self.echo = echo
        self._session = None

    def __enter__(self):
        return self

    def __exit__(self, type_, value, traceback):
        self.close()

    def close(self):
        if self._session is not None:
            self._session.close()
            self._session.bind.dispose()
            self._session = None

    @property
    def session(self):
        if self._session is None:
            self._session = create_session(f'{self.database}.sqlite', echo=self.echo)
        return self._session


if __name__ == "__main__":
    import time
    import glob
    import sys

    if sys.platform.startswith('win'):
        DATABASES_PATH = os.path.expandvars(r'%APPDATA%\tsne-network\databases')
    elif sys.platform.startswith('darwin'):
        DATABASES_PATH = os.path.expanduser(r'~/Library/tsne-network/databases')
    elif sys.platform.startswith('linux'):
        DATABASES_PATH = os.path.expanduser(r'~/.config/tsne-network/databases')
    else:
        DATABASES_PATH = 'databases'

    t00 = time.time()
    with DataBaseBuilder(os.path.join(DATABASES_PATH, 'spectra'), echo=False) as db:
        for path in glob.glob(os.path.join(DATABASES_PATH, '*.mgf')):
            if not path.endswith('ALL_GNPS.mgf'):
                filename = os.path.basename(path)
                print(f'Processing {filename}...')
                t0 = time.time()
                db.add_bank(path)
                print(f'{filename} processed in {time.time()-t0:.2f}s.')
            # if path.endswith('GNPS-EMBL-MCF.mgf'):
            #     break
    print(f'Total time: {time.time()-t00:.2f}s.')
