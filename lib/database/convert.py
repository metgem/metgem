import os

import numpy as np
from sqlalchemy.exc import OperationalError

from pyteomics import mgf

from ..utils import grouper
from .session import create_session
from .models import Spectrum, Organism, Submitter, DataCollector, Instrument, Bank, Investigator


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

        fname = f'{name}.sqlite' if not name.endswith('.sqlite') else name
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
            first_spec = self.session.query(Spectrum).first()
            last_spec = self.session.query(Spectrum).order_by(Spectrum.id.desc()).first()
            if first_spec is not None and last_spec is not None:
                self._used_pkeys = (first_spec.id, last_spec.id)
        else:
            self.session = create_session(fname, echo=self.echo, drop_all=True)

        # Create a generator for spectrum primary key to make sure we don't use an already used primary key.
        # We don't use auto-increment because, otherwise, primary keys will increase on each update
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
        self.session.close()
        self.session.bind.dispose()

        # Try to clean up unused data in database to free space (vacuum)
        try:
            isolation_level = self.session.connection().connection.isolation_level
            self.session.connection().connection.isolation_level = None
            self.session.execute('vacuum')
            self.session.connection().connection.isolation_level = isolation_level
            self.session.close()
        except OperationalError:
            pass

    def add_bank(self, mgf_path):
        bank = os.path.splitext(os.path.basename(mgf_path))[0]
        if bank in self._uniques['bank']:
            q = self.session.query(Spectrum).filter(Spectrum.bank_id == self._uniques['bank'][bank])
            if q.count() > 0:
                self._free_pkeys.append((q.first().id, q.order_by(Spectrum.id.desc()).first().id))
                q.delete()
                self.session.flush()
        else:
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
