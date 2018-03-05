import os
from collections import OrderedDict
import h5py

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

        self.session = None
        self.hf = None

        keys = ('bank', 'organism', 'pi', 'submituser', 'datacollector', 'source_instrument', 'spectrum')
        self._uniques = {k: OrderedDict() for k in keys if k != 'spectrum'}
        self._indexes = {k: 1 for k in keys}

        self.session = create_session(f'{self.name}.sqlite', echo=self.echo, drop_all=True)
        self.hf = h5py.File(f'{self.name}.h5', 'w')

    def __enter__(self):
        return self

    def __exit__(self, type_, value, traceback):
        self.close()

    def close(self):
        self.session.execute(Bank.__table__.insert(),
                             [{'name': k} for k in self._uniques['bank']])
        self.session.execute(Organism.__table__.insert(),
                             [{'name': k} for k in self._uniques['organism']])
        self.session.execute(Investigator.__table__.insert(),
                             [{'name': k} for k in self._uniques['pi']])
        self.session.execute(Instrument.__table__.insert(),
                             [{'name': k} for k in self._uniques['source_instrument']])
        self.session.execute(DataCollector.__table__.insert(),
                             [{'name': k} for k in self._uniques['datacollector']])
        self.session.execute(Submitter.__table__.insert(),
                             [{'name': k} for k in self._uniques['submituser']])
        self.session.commit()
        self.session.execute('vacuum')
        self.session.close()
        self.session.bind.dispose()

        self.hf.close()

    def add_bank(self, mgf_path):
        bank = os.path.splitext(os.path.basename(mgf_path))[0]
        self._uniques['bank'][bank] = self._indexes['bank']
        group = self.hf.create_group(bank)

        for batch in chunk_read_mgf(mgf_path, 1000):  # Read mgf file by batch of 1000 spectra
            spectra = []

            for entry in batch:
                # If entry is None, we are in a non-complete batch (end of file), just break
                if entry is None:
                    break

                params = entry['params']

                # Set-up a dictionnary with all the values needed to build a Spectrum object
                spectrum = {
                            'bank_id': self._indexes['bank'],
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
                    group.create_dataset(str(self._indexes['spectrum']), data=peaks)

                spectra.append(spectrum)
                self._indexes['spectrum'] += 1

            # Add spectra and peaks
            # We can't use ORM because we have a lot of insertions to do
            # See http://docs.sqlalchemy.org/en/latest/faq/performance.html#i-m-inserting-400-000-rows-with-the-orm-and-it-s-really-slow
            self.session.execute(Spectrum.__table__.insert(), spectra)
            # self.session.execute(Peak.__table__.insert(), batch_peaks)
            self.session.flush()

        self.session.commit()
        self._indexes['bank'] += 1


class Library:

    def __init__(self, database, echo=False):
        self.database = database
        self.echo = echo
        self._session = None

    def __enter__(self):
        return self

    def __exit__(self, type_, value, traceback):
        if self._session is not None:
            self._session.close()
            self._session.bind.dispose()
            self._session = None

    @property
    def session(self):
        if self._session is None:
            self._session = create_session(self.database, echo=self.echo)
        return self._session


if __name__ == "__main__":
    import time
    import glob

    t00 = time.time()
    with DataBaseBuilder('spectra') as db:
        for path in glob.glob(r'C:\Users\elie\Desktop\ML\databases\*.mgf'):
            if not path.endswith('ALL_GNPS.mgf'):
                filename = os.path.basename(path)
                print(f'Processing {filename}...')
                t0 = time.time()
                db.add_bank(path)
                print(f'{filename} processed in {time.time()-t0:.2f}s.')
            # if path.endswith('GNPS-EMBL-MCF.mgf'):
            #     break
    print(f'Total time: {time.time()-t00:.2f}s.')

    # with Library('spectra', echo=True) as l:
    #     query = l.session.query(Spectrum)
    #     for obj in query:
    #         spectrum = l.spectrum_array(obj.id, cache=True)
