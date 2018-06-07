from ..spectrum import SpectrumWidget
from ....database import Spectrum
from ..delegates import StarRating

import os

from PyQt5.QtWidgets import QDataWidgetMapper, QLabel, QWidget
from PyQt5 import uic
from PyQt5.QtGui import QPainter

UI_FILE = os.path.join(os.path.dirname(__file__), 'databases_details.ui')


class HTMLLabel(QLabel):
    LINK = '{}'

    def setProperty(self, name, value):
        if name == b'text':
            value = self.LINK.format(value)

        super().setProperty(name, value)

    def setText(self, value):
        self.setProperty(b'text', value)


class PubMedLabel(HTMLLabel):
    LINK = "<a href='http://www.ncbi.nlm.nih.gov/pubmed/?term={0}'>{0}</a>"


class SpectrumIdLabel(HTMLLabel):
    LINK = "<a href='https://gnps.ucsd.edu/ProteoSAFe/gnpslibraryspectrum.jsp?SpectrumID={0}'>{0}</a>"


class SubmitUserLabel(HTMLLabel):
    LINK = "<a href='https://gnps.ucsd.edu/ProteoSAFe/user/summary.jsp?user={0}'>{0}</a>"


class QualityLabel(QLabel):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._star_rating = StarRating()

    def paintEvent(self, event):
        try:
            rating = int(self.text())
        except (ValueError, TypeError):
            super().paintEvent(event)
        else:
            painter = QPainter(self)
            self._star_rating.paint(painter, self.rect(), rating)

    def sizeHint(self):
        return self._star_rating.sizeHint()

    def minimumSize(self):
        return self.sizeHint()


class SpectrumDataWidgetMapper(QDataWidgetMapper):

    def addMapping(self, widget, section, property_name=None):
        if isinstance(widget, QLabel):
            property_name = b'text'
        elif section == Spectrum.peaks:
            property_name = b'spectrum1'
            if isinstance(widget, SpectrumWidget):
                widget = widget.canvas
        elif section == Spectrum.inchi:
            property_name = b'inchi'
        elif section == Spectrum.smiles:
            widget = widget.second_mapping
            property_name = b'smiles'

        model = self.model()
        if model is not None and not isinstance(section, int):
            section = model.column_index(section)

        if property_name is None:
            super().addMapping(widget, section)
        else:
            super().addMapping(widget, section, property_name)


class SpectrumDetailsWidget(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        uic.loadUi(os.path.join(os.path.dirname(__file__), UI_FILE), self)

        self._mapper = None

    def model(self):
        return self._mapper.model()

    def setModel(self, model):
        self._mapper = SpectrumDataWidgetMapper()
        self._mapper.setModel(model)
        self._mapper.addMapping(self.lblName, Spectrum.name)
        self._mapper.addMapping(self.lblInChI, Spectrum.inchi)
        self._mapper.addMapping(self.lblSmiles, Spectrum.smiles)
        self._mapper.addMapping(self.lblPubMed, Spectrum.pubmed)
        self._mapper.addMapping(self.lblPepmass, Spectrum.pepmass)
        self._mapper.addMapping(self.lblPolarity, Spectrum.positive)
        self._mapper.addMapping(self.lblCharge, Spectrum.charge)
        self._mapper.addMapping(self.lblMSLevel, Spectrum.mslevel)
        self._mapper.addMapping(self.lblQuality, Spectrum.libraryquality)
        self._mapper.addMapping(self.lblLibraryId, Spectrum.spectrumid)
        self._mapper.addMapping(self.lblSourceInstrument, Spectrum.source_instrument_id)
        self._mapper.addMapping(self.lblPi, Spectrum.pi_id)
        self._mapper.addMapping(self.lblOrganism, Spectrum.organism_id)
        self._mapper.addMapping(self.lblDataCollector, Spectrum.datacollector_id)
        self._mapper.addMapping(self.lblSubmitUser, Spectrum.submituser_id)
        self._mapper.addMapping(self.widgetSpectrum, Spectrum.peaks)
        self._mapper.addMapping(self.widgetStructure, Spectrum.inchi)
        self._mapper.addMapping(self.widgetStructure, Spectrum.smiles)

    def setCurrentIndex(self, index: int):
        if self._mapper is not None:
            self._mapper.setCurrentIndex(index)
