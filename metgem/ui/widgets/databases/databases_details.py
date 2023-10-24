from metgem.database import Spectrum
from metgem.ui.widgets.databases.databases_details_ui import Ui_DatabasesDetails

from PySide6.QtWidgets import QWidget
from PySide6QtAds import CDockManager, CDockWidget, CenterDockWidgetArea


class SpectrumDetailsWidget(QWidget, Ui_DatabasesDetails):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setupUi(self)

        self._model = None
        self.dock_manager = CDockManager(self)
        self.docks = []
        dock_area = None

        for _ in range(self.tabWidget.count()):
            w = self.tabWidget.widget(0)
            dock = CDockWidget(self.tabWidget.tabText(0))
            dock.setFeature(CDockWidget.DockWidgetFeature.DockWidgetFloatable, False)
            dock.setFeature(CDockWidget.DockWidgetFeature.DockWidgetClosable, False)
            dock.setIcon(self.tabWidget.tabIcon(0))
            self.docks.append(dock)
            if dock_area is None:
                dock_area = self.dock_manager.addDockWidget(CenterDockWidgetArea, dock)
            else:
                dock_area = self.dock_manager.addDockWidget(CenterDockWidgetArea, dock, dock_area)
            dock.setWidget(w)
        if self.docks:
            self.docks[0].setAsCurrentTab()
            self.layout().removeWidget(self.tabWidget)
            self.tabWidget.setParent(None)
            self.tabWidget.deleteLater()
            self.layout().addWidget(self.dock_manager)
            self.layout().setContentsMargins(0, 0, 0, 0)
            self.widgetSpectrum.canvas.showEvent = lambda _: None  # prevent matplotlib bug

        self.widgetFragmentsList.spectra_widget = self.widgetSpectrum
        self.widgetSpectrum.dataLoaded.connect(self.widgetFragmentsList.populate_fragments_list)
        self.widgetSpectrum.dataCleared.connect(self.widgetFragmentsList.clear_fragments_list)

    def hideEvent(self, event):
        for w in self.dock_manager.floatingWidgets():
            w.close()

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
