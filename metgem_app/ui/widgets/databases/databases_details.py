from ....database import Spectrum
from .databases_details_ui import Ui_DownloadDatabaseDialog

from qtpy.QtWidgets import  QWidget


class SpectrumDetailsWidget(QWidget, Ui_DownloadDatabaseDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setupUi(self)

        self._model = None

        self.widgetFragmentsList.spectra_widget = self.widgetSpectrum
        self.widgetSpectrum.dataLoaded.connect(self.widgetFragmentsList.populate_fragments_list)
        self.widgetSpectrum.dataCleared.connect(self.widgetFragmentsList.clear_fragments_list)

    def model(self):
        return self._model

    def setModel(self, model):
        self._model = model

    def getData(self, row, section):
        return self._model.data(self._model.index(row, self._model.column_index(section)))

    def setCurrentIndex(self, index: int):
        if self._model is not None:
            def to_text(data):
                return str(data) if data is not None else ""

            self.lblName.setText(to_text(self.getData(index, Spectrum.name)))
            self.lblInChI.setText(to_text(self.getData(index, Spectrum.inchi)))
            self.lblSmiles.setText(to_text(self.getData(index, Spectrum.smiles)))
            self.lblPubMed.setText(to_text(self.getData(index, Spectrum.pubmed)))
            self.lblPepmass.setText(to_text(self.getData(index, Spectrum.pepmass)))
            self.lblPolarity.setText(to_text(self.getData(index, Spectrum.positive)))
            self.lblCharge.setText(to_text(self.getData(index, Spectrum.charge)))
            self.lblMSLevel.setText(to_text(self.getData(index, Spectrum.mslevel)))
            self.lblQuality.setText(to_text(self.getData(index, Spectrum.libraryquality)))
            self.lblLibraryId.setText(to_text(self.getData(index, Spectrum.spectrumid)))
            self.lblSourceInstrument.setText(to_text(self.getData(index, Spectrum.source_instrument_id)))
            self.lblPi.setText(to_text(self.getData(index, Spectrum.pi_id)))
            self.lblOrganism.setText(to_text(self.getData(index, Spectrum.organism_id)))
            self.lblDataCollector.setText(to_text(self.getData(index, Spectrum.datacollector_id)))
            self.lblSubmitUser.setText(to_text(self.getData(index, Spectrum.submituser_id)))
            self.widgetSpectrum.canvas.spectrum1_parent = self.getData(index, Spectrum.pepmass)
            self.widgetSpectrum.canvas.spectrum1 = self.getData(index, Spectrum.peaks)
            self.widgetStructure.setInchi(self.getData(index, Spectrum.inchi))
            self.widgetStructure.setSmiles(self.getData(index, Spectrum.smiles))
