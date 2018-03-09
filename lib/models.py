from sqlalchemy import (Column, ForeignKey, Integer, Float, String, Boolean, Binary, TypeDecorator)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property

import numpy as np

Base = declarative_base()


class NumpySpectrumArray(TypeDecorator):

    impl = Binary

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
    id = Column(Integer, primary_key=True)
    bank_id = Column(Integer, ForeignKey('banks.id'), nullable=False)
    bank = relationship('Bank', lazy='subquery')
    pepmass = Column(Float, nullable=False, index=True)
    positive = Column(Boolean, nullable=False)
    charge = Column(Integer, nullable=False)
    mslevel = Column(Integer, nullable=False)
    source_instrument_id = Column(Integer, ForeignKey('instruments.id'))
    source_instrument = relationship('Instrument', lazy='subquery')
    organism_id = Column(Integer, ForeignKey('organisms.id'))
    organism = relationship('Organism', lazy='subquery')
    name = Column(String)
    pi_id = Column(Integer, ForeignKey('investigators.id'))
    pi = relationship('Organism', lazy='subquery')
    datacollector_id = Column(Integer, ForeignKey('datacollectors.id'))
    datacollector = relationship('DataCollector', lazy='subquery')
    smiles = Column(String)
    inchi = Column(String)
    inchiaux = Column(String)
    pubmed = Column(String)
    submituser_id = Column(Integer, ForeignKey('submitters.id'))
    submituser = relationship('Submitter', lazy='subquery')
    peaks = Column(NumpySpectrumArray)

    @hybrid_property
    def polarity(self):
        return '+' if self.positive else '-'

    @polarity.setter
    def polarity(self, value):
        self.positive = (value == '+' or value == 'Positive')

    def __init__(self, bank, pepmass, polarity, charge, mslevel, **kwargs):
        self.bank = bank
        self.pepmass = pepmass
        if isinstance(polarity, str):
            self.polarity = polarity
        else:
            self.positive = bool(polarity)
        self.charge = charge
        self.mslevel = mslevel

        for key, value in kwargs.items():
            if key in self.__class__.__dict__:
                setattr(self, key, value)

    def __repr__(self):
        return (f"Spectrum(bank='{self.bank.name}', pemass={self.pepmass}, polarity={repr(self.polarity)}, "
                f"charge={self.charge}, mslevel={self.mslevel})")

    def __getitem__(self, key):
        return self.values.__getitem__(key)
