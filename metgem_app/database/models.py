import numpy as np
from sqlalchemy import (Column, ForeignKey, Integer, Float, String, Boolean, LargeBinary, TypeDecorator)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

Base = declarative_base()


# noinspection PyAbstractClass
class NumpySpectrumArray(TypeDecorator):

    impl = LargeBinary

    def process_bind_param(self, value, dialect):
        return value.tobytes(order='C')

    def process_result_value(self, value, dialect):
        return np.frombuffer(value, dtype='<f4').reshape(-1, 2)


class Organism(Base):
    __tablename__ = 'organisms'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)


class Investigator(Base):
    __tablename__ = 'investigators'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)


class Submitter(Base):
    __tablename__ = 'submitters'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)


class DataCollector(Base):
    __tablename__ = 'datacollectors'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)


class Instrument(Base):
    __tablename__ = 'instruments'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)


class Bank(Base):
    __tablename__ = 'banks'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)


class Spectrum(Base):
    __tablename__ = 'spectra'
    id = Column(Integer, primary_key=True, autoincrement=False)
    bank_id = Column(Integer, ForeignKey('banks.id'), nullable=False, comment="Source")
    bank = relationship('Bank')
    pepmass = Column(Float, nullable=False, index=True, comment="m/z parent")
    positive = Column(Boolean, nullable=True, comment="Polarity")
    charge = Column(Integer, nullable=False, comment="Charge")
    mslevel = Column(Integer, nullable=False, comment="MS Level")
    source_instrument_id = Column(Integer, ForeignKey('instruments.id'), comment="Source Instrument")
    source_instrument = relationship('Instrument')
    organism_id = Column(Integer, ForeignKey('organisms.id'), comment="Organism")
    organism = relationship('Organism')
    name = Column(String, comment="Name")
    pi_id = Column(Integer, ForeignKey('investigators.id'), comment="Princ. Investigator")
    pi = relationship('Investigator')
    datacollector_id = Column(Integer, ForeignKey('datacollectors.id'), comment="Data Collector")
    datacollector = relationship('DataCollector')
    smiles = Column(String, comment="SMILES")
    inchi = Column(String, comment="InChI")
    inchiaux = Column(String, comment="InChi aux.")
    pubmed = Column(String, comment="Pubmed id")
    submituser_id = Column(Integer, ForeignKey('submitters.id'), comment="Submit User")
    submituser = relationship('Submitter')
    libraryquality = Column(Integer, comment="Library Quality")
    spectrumid = Column(String, comment="Id")
    peaks = Column(NumpySpectrumArray, comment="Spectrum peaks")

    @hybrid_property
    def polarity(self):
        if self.positive is None:
            return 'N/A'
        elif self.positive:
            return 'Positive'
        else:
            return 'Negative'

    @polarity.setter
    def polarity(self, value):
        if value.strip() in ('+', 'Positive', 'positive'):
            self.positive = True
        elif value.strip() in ('-', 'Negative', 'negative'):
            self.positive = False
        else:
            self.positive = None

    def __init__(self, bank, pepmass, polarity, charge, mslevel, **kwargs):
        self.bank = bank
        self.pepmass = pepmass
        if isinstance(polarity, str):
            self.polarity = polarity
        else:
            self.positive = polarity
        self.charge = charge
        self.mslevel = mslevel

        for key, value in kwargs.items():
            if key in self.__class__.__dict__:
                setattr(self, key, value)

    def __repr__(self):
        # noinspection PyPropertyAccess
        return (f"Spectrum(bank='{self.bank.name}', pepmass={self.pepmass}, polarity={repr(self.polarity)}, "
                f"charge={self.charge}, mslevel={self.mslevel})")

    def __getitem__(self, key):
        return self.values.__getitem__(key)
