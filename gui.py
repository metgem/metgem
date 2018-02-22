#!/usr/bin/env python

import sys
import os
import traceback
import json

import numpy as np
import igraph as ig

from PyQt5.QtWidgets import (QDialog, QFileDialog,
                             QMessageBox, QWidget, QGraphicsRectItem,
                             QMenu, QToolButton, QActionGroup,
                             QAction, QDockWidget)
from PyQt5.QtCore import QThread, QSettings, Qt, QPointF
from PyQt5.QtGui import QPainter, QImage
from PyQt5 import uic

from lib import ui, config, utils, save, graphml, workers
from lib.workers.network_generation import generate_network  # TODO

MAIN_UI_FILE = os.path.join('lib', 'ui', 'main_window.ui')
DEBUG = os.getenv('DEBUG_MODE', 'false').lower() in ('true', '1')
EMBED_JUPYTER = os.getenv('EMBED_JUPYTER', 'false').lower() in ('true', '1')

if sys.platform == 'win32':
    LOG_PATH = os.path.expandvars(r'%APPDATA%\tsne-network\log')
else:
    LOG_PATH = 'log'  # TODO: find better place for linux and os x

MainWindowUI, MainWindowBase = uic.loadUiType(MAIN_UI_FILE, from_imports='lib.ui', import_from='lib.ui')


class WorkerDict(dict):
    """A dict that manages itself visibility of it's parent's progressbar"""

    def __init__(self, parent, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent = parent

    def __setitem__(self, key, item):
        if not self:  # dict is empty, so we are going to create the first entry. Show the progress bar
            self.parent.statusBar().addPermanentWidget(self.parent.widgetProgress)
            self.parent.widgetProgress.setVisible(True)
        super().__setitem__(key, item)

    def __delitem__(self, key):
        super().__delitem__(key)
        if not self:  # dict is now empty, hide the progress bar
            self.parent.widgetProgress.setVisible(False)
            self.parent.statusBar().removeWidget(self.parent.widgetProgress)


class Network:
    __slots__ = 'spectra', 'scores', 'infos'


class MainWindow(MainWindowBase, MainWindowUI):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Keep track of unsaved changes
        self._has_unsaved_changes = False

        # Opened file
        self.fname = None

        # Workers' references
        self._workers = WorkerDict(self)

        # Create graph
        self.graph = ig.Graph()

        # Setup User interface
        self.setupUi(self)

        # Assigning cosine computation and visualization default options
        self.options = utils.AttrDict({'cosine': workers.CosineComputationOptions(),
                                       'network': workers.NetworkVisualizationOptions(),
                                       'tsne': workers.TSNEVisualizationOptions()})

        # Create an object to store all computed objects
        self.network = Network()

        # Add model to table views
        for table, Model, name in ((self.tvNodes, ui.widgets.NodesModel, "Nodes"),
                                   (self.tvEdges, ui.widgets.EdgesModel, "Edges")):
            table.setSortingEnabled(True)
            model = Model(self)
            proxy = ui.widgets.ProxyModel()
            proxy.setSourceModel(model)
            table.setModel(proxy)

        # Move search layout to search toolbar
        w = QWidget()
        self.layoutSearch.setParent(None)
        w.setLayout(self.layoutSearch)
        self.tbSearch.addWidget(w)

        # Move progressbar to the statusbar
        self.widgetProgress = QWidget()
        self.layoutProgress.setParent(None)
        self.layoutProgress.setContentsMargins(0, 0, 0, 0)
        self.widgetProgress.setLayout(self.layoutProgress)
        self.widgetProgress.setVisible(False)

        # Add a Jupyter widget
        if EMBED_JUPYTER:
            from qtconsole.rich_jupyter_widget import RichJupyterWidget
            from qtconsole.inprocess import QtInProcessKernelManager

            kernel_manager = QtInProcessKernelManager()
            kernel_manager.start_kernel()

            kernel_client = kernel_manager.client()
            kernel_client.start_channels()

            self.jupyter_widget = RichJupyterWidget()
            self.jupyter_widget.kernel_manager = kernel_manager
            self.jupyter_widget.kernel_client = kernel_client

            def stop():
                kernel_client.stop_channels()
                kernel_manager.shutdown_kernel()

            self.jupyter_widget.exit_requested.connect(stop)
            app.aboutToQuit.connect(stop)

            dock_widget = QDockWidget()
            dock_widget.setObjectName('jupyter')
            dock_widget.setWindowTitle('Jupyter Console')
            dock_widget.setWidget(self.jupyter_widget)

            self.addDockWidget(Qt.BottomDockWidgetArea, dock_widget)
            kernel_manager.kernel.shell.push({'app': app, 'win': self})

        # Connect events
        self.gvNetwork.scene().selectionChanged.connect(self.onSelectionChanged)
        self.gvTSNE.scene().selectionChanged.connect(self.onSelectionChanged)
        self.actionQuit.triggered.connect(self.close)
        self.actionAbout.triggered.connect(self.showAbout)
        self.actionAboutQt.triggered.connect(self.showAboutQt)
        self.actionProcessFile.triggered.connect(self.showOpenFileDialog)
        self.actionZoomIn.triggered.connect(lambda: self.currentView.scaleView(1.2))
        self.actionZoomOut.triggered.connect(lambda: self.currentView.scaleView(1 / 1.2))
        self.actionZoomToFit.triggered.connect(self.currentView.zoomToFit)
        self.actionZoomSelectedRegion.triggered.connect(
            lambda: self.currentView.fitInView(self.currentView.scene().selectionArea().boundingRect(),
                                               Qt.KeepAspectRatio))
        self.leSearch.textChanged.connect(self.doSearch)
        self.actionOpen.triggered.connect(self.openProject)
        self.actionSave.triggered.connect(self.saveProject)
        self.actionSaveAs.triggered.connect(self.saveProjectAs)

        self.actionFullScreen.triggered.connect(self.switchFullScreen)
        self.actionHideSelected.triggered.connect(lambda: self.hideItems(self.currentView.scene().selectedItems()))
        self.actionShowAll.triggered.connect(lambda: self.showItems(self.currentView.scene().items()))
        self.actionNeighbors.triggered.connect(
            lambda: self.selectFirstNeighbors(self.currentView.scene().selectedItems()))
        self.actionExportToCytoscape.triggered.connect(self.exportToCytoscape)
        self.actionExportAsImage.triggered.connect(self.exportAsImage)

        self.btNetworkOptions.clicked.connect(self.openVisualizationDialog)
        self.btTSNEOptions.clicked.connect(self.openVisualizationDialog)

        # Add a menu to show/hide toolbars
        popup_menu = self.createPopupMenu()
        popup_menu.setTitle("Toolbars")
        self.menuView.addMenu(popup_menu)

        # Build research bar
        self.updateSearchBar()

    @property
    def window_title(self):
        if self.fname is not None:
            if self.has_unsaved_changes:
                return QCoreApplication.applicationName() + ' - ' + self.fname + '*'
            else:
                return QCoreApplication.applicationName() + ' - ' + self.fname
        else:
            return QCoreApplication.applicationName()

    @property
    def has_unsaved_changes(self):
        return self._has_unsaved_changes

    @has_unsaved_changes.setter
    def has_unsaved_changes(self, value):
        if value:
            self.setWindowTitle(self.window_title)
            self.actionSave.setEnabled(True)
        else:
            self.setWindowTitle(self.window_title)
            self.actionSave.setEnabled(False)

        self._has_unsaved_changes = value

    @property
    def currentView(self):
        for view in (self.gvNetwork, self.gvTSNE):
            if view.hasFocus():
                return view
        return self.gvNetwork

    def keyPressEvent(self, event):
        key = event.key()

        if key == Qt.Key_M:  # Show/hide minimap
            view = self.currentView
            view.minimap.setVisible(not view.minimap.isVisible())
        elif key == Qt.Key_F2:
            print(self.tbFile.isVisible())

    def selectFirstNeighbors(self, items):
        view = self.currentView
        for item in items:
            if item.Type == ui.Node.Type:
                for v in self.graph.vs[item.index].neighbors():
                    try:
                        if view == self.gvNetwork:
                            v['__network_gobj'].setSelected(True)
                        elif view == self.gvTSNE:
                            v['__tsne_gobj'].setSelected(True)
                    except (KeyError, AttributeError):
                        pass

    def showItems(self, items):
        for item in items:
            item.show()

    def hideItems(self, items):
        for item in items:
            item.hide()

    def switchFullScreen(self):
        if not self.isFullScreen():
            self.setWindowFlags(Qt.Window)
            self.showFullScreen()
        else:
            self.setWindowFlags(Qt.Widget)
            self.showNormal()

    def showAbout(self):
        dialog = QMessageBox(self)
        message = ['Version: {0}'.format(QCoreApplication.applicationVersion()),
                   '',
                   'Should say something here.']
        dialog.about(self, 'About {0}'.format(QCoreApplication.applicationName()),
                     '\n'.join(message))

    def showAboutQt(self):
        dialog = QMessageBox(self)
        dialog.aboutQt(self)

    def showEvent(self, event):
        # Load settings
        settings = QSettings()
        geom = settings.value('MainWindow.Geometry')
        if geom is not None:
            self.restoreGeometry(geom)
        state = settings.value('MainWindow.State')
        if state is not None:
            self.restoreState(state)
        super().showEvent(event)

    def closeEvent(self, event):
        if not DEBUG and self._workers:
            reply = QMessageBox.question(self, None,
                                         "There is process running. Do you really want to exit?",
                                         QMessageBox.Close, QMessageBox.Cancel)
        else:
            reply = QMessageBox.Close

        if reply == QMessageBox.Close:
            event.accept()
            self.saveSettings()
        else:
            event.ignore()

    def saveSettings(self):
        settings = QSettings()
        settings.setValue('MainWindow.Geometry', self.saveGeometry())
        settings.setValue('MainWindow.State', self.saveState())

    def deleteWorker(self, worker):
        del self._workers[worker]
        if not self._workers:
            self.widgetProgress.setVisible(False)

    def applyNetworkLayout(self, view, layout):
        try:
            for coord, node in zip(layout, self.graph.vs):
                node['__network_gobj'].setPos(QPointF(*coord))
        except (KeyError, AttributeError):
            pass

        self.graph.network_layout = layout

        view.zoomToFit()
        view.minimap.zoomToFit()

    def drawNetwork(self, view, interactions=None, layout=None):
        view.scene().clear()

        if interactions is not None:
            widths = np.array(interactions['Cosine'])
            min_ = max(0, widths.min() - 0.1)
            if min_ != widths.max():
                widths = (config.RADIUS - 1) * (widths - min_) / (widths.max() - min_) + 1
            else:
                widths = config.RADIUS

            self.graph.es['__weight'] = interactions['Cosine']
            self.graph.es['__width'] = widths

        # Add nodes
        group = QGraphicsRectItem()  # Create a pseudo-group, QGraphicsItemGroup is not used because it does not let children handle events
        group.setZValue(1)  # Draw nodes on top of edges
        for i, n in enumerate(self.graph.vs):
            node = ui.Node(i, n['__label'])
            node.setParentItem(group)
        self.graph.vs['__network_gobj'] = group.childItems()
        view.scene().addItem(group)
        self.nodes_group = group

        # Add edges
        group = QGraphicsRectItem()
        group.setZValue(0)
        for i, e in enumerate(self.graph.es):
            edge = ui.Edge(i, self.graph.vs['__network_gobj'][e.source], self.graph.vs['__network_gobj'][e.target],
                           e['__weight'], e['__width'])
            edge.setParentItem(group)
        self.graph.es['__network_gobj'] = group.childItems()
        view.scene().addItem(group)
        self.edges_group = group

        if layout is None:
            # Compute layout
            def update_progress(i):
                self.progressBar.setFormat('Computing layout: {s}%'.format(i))
                self.progressBar.setValue(i)

            def process_finished():
                layout = worker.result()
                del self._workers[worker]
                if layout is not None:
                    self.applyNetworkLayout(view, layout)

            def process_canceled():
                del self._workers[worker]

            self.progressBar.setFormat('Computing layout...')
            self.progressBar.setMaximum(100)
            thread = QThread(self)
            worker = workers.NetworkWorker(self.graph)
            worker.moveToThread(thread)
            worker.updated.connect(update_progress)
            worker.finished.connect(process_finished)
            worker.canceled.connect(process_canceled)
            self.btCancelProcess.pressed.connect(lambda: worker.stop())
            thread.started.connect(worker.run)
            thread.start()
            self._workers[
                worker] = thread  # Keep a reference to both thread and worker to prevent them to be garbage collected

            return worker, thread
        else:
            self.applyNetworkLayout(view, layout)
            return None, None

    def applyTSNELayout(self, view, layout):
        try:
            for coord, node in zip(layout, self.graph.vs):
                node['__tsne_gobj'].setPos(QPointF(*coord))
        except (KeyError, AttributeError):
            pass

        self.graph.tsne_layout = layout

        view.zoomToFit()
        view.minimap.zoomToFit()

    def drawTSNE(self, view, scores=None, layout=None):
        view.scene().clear()

        # Add nodes
        group = QGraphicsRectItem()  # Create a pseudo-group, QGraphicsItemGroup is not used because it does not let children handle events
        group.setZValue(1)  # Draw nodes on top of edges
        for i, n in enumerate(self.graph.vs):
            node = ui.Node(i, n['__label'])
            node.setParentItem(group)
        self.graph.vs['__tsne_gobj'] = group.childItems()
        view.scene().addItem(group)
        self.nodes_group = group

        if layout is None:
            # Compute layout
            scores[scores < 0.65] = 0

            mask = scores.sum(axis=0) > 1
            layout = np.zeros((scores.shape[0], 2))

            if np.any(mask):
                def update_progress(i):
                    self.progressBar.setFormat('TSNE: Iteration {:d} of {:d}'.format(i, self.progressBar.maximum()))
                    self.progressBar.setValue(i)

                def process_finished():
                    nonlocal layout
                    layout[mask] = worker.result()
                    del self._workers[worker]

                    bb = ig.Layout(layout.tolist()).bounding_box()
                    dx, dy = 0, 0
                    for index in np.where(~mask)[0]:
                        layout[index] = (bb.left + dx, bb.height + dy)
                        dx += 5
                        if dx >= bb.width:
                            dx = 0
                            dy += 5

                    layout = ig.Layout(layout.tolist())
                    layout.scale(config.RADIUS)

                    self.applyTSNELayout(view, layout)

                def process_canceled():
                    del self._workers[worker]

                self.progressBar.setFormat('Computing TSNE...')
                self.progressBar.setMaximum(1000)  # TODO
                thread = QThread(self)
                worker = workers.TSNEWorker(1 - scores[mask][:, mask])
                worker.moveToThread(thread)
                worker.updated.connect(update_progress)
                worker.finished.connect(process_finished)
                worker.canceled.connect(process_canceled)
                self.btCancelProcess.pressed.connect(lambda: worker.stop())
                thread.started.connect(worker.run)
                thread.start()
                self._workers[
                    worker] = thread  # Keep a reference to both thread and worker to prevent them to be garbage collected
                return worker, thread
            else:
                self.applyTSNELayout(view, layout)
                return None, None
        else:
            self.applyTSNELayout(view, layout)
            return None, None

    def computeScoresFromSpectra(self, spectra, use_multiprocessing):
        def update_progress(i):
            self.progressBar.setValue(self.progressBar.value() + i)

        def process_finished():
            del self._workers[worker]

        def process_canceled():
            del self._workers[worker]

        num_spectra = len(spectra)
        num_scores_to_compute = num_spectra * (num_spectra - 1) // 2

        self.progressBar.setFormat('Computing scores...')
        self.progressBar.setMaximum(num_scores_to_compute)
        thread = QThread(self)
        worker = workers.ComputeScoresWorker(spectra, use_multiprocessing, self.options.cosine)
        worker.moveToThread(thread)
        worker.updated.connect(update_progress)
        worker.finished.connect(process_finished)
        worker.canceled.connect(process_canceled)
        self.btCancelProcess.pressed.connect(lambda: worker.stop())
        thread.started.connect(worker.run)
        thread.start()
        self._workers[
            worker] = thread  # Keep a reference to both thread and worker to prevent them to be garbage collected
        return worker, thread

    def readMGF(self, filename):
        def update_progress(i):
            self.progressBar.setValue(self.progressBar.value() + i)

        def process_finished():
            del self._workers[worker]

        def process_canceled():
            del self._workers[worker]

        self.progressBar.setFormat('Reading MGF...')
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(0)

        thread = QThread(self)
        worker = workers.ReadMGFWorker(filename, self.options.cosine)
        worker.moveToThread(thread)
        worker.updated.connect(update_progress)
        worker.finished.connect(process_finished)
        worker.canceled.connect(process_canceled)
        self.btCancelProcess.pressed.connect(lambda: worker.stop())
        thread.started.connect(worker.run)
        thread.start()
        self._workers[
            worker] = thread  # Keep a reference to both thread and worker to prevent them to be garbage collected
        return worker, thread

    def showOpenFileDialog(self):
        dialog = ui.OpenFileDialog(self, options=self.options)
        if dialog.exec_() == QDialog.Accepted:
            self.fname = None
            self.has_unsaved_changes = True
            self.gvNetwork.scene().clear()
            self.gvTSNE.scene().clear()

            process_file, metadata_file, compute_options, tsne_options, network_options = dialog.getValues()
            self.options.cosine = compute_options
            self.options.tsne = tsne_options
            self.options.network = network_options

            def file_read():
                nonlocal worker
                self.network.spectra = worker.result()
                multiprocess = len(self.network.spectra) > 1000  # TODO: Tune this, arbitrary decision
                worker, thread = self.computeScoresFromSpectra(self.network.spectra, multiprocess)
                worker.finished.connect(scores_computed)

            def scores_computed():
                self.network.scores = worker.result()
                interactions = generate_network(self.network.scores, self.network.spectra, self.options.network,
                                                use_self_loops=True)

                self.network.infos = np.array([(spectrum.mz_parent,) for spectrum in self.network.spectra],
                                              dtype=[('m/z parent', np.float32)])

                nodes_idx = np.arange(self.network.scores.shape[0])
                self.createGraph(nodes_idx, self.network.infos, interactions, labels=None)

                self.draw(self.network.scores, interactions, self.network.infos, labels=None)

            worker, thread = self.readMGF(process_file)
            worker.finished.connect(file_read)

    def openVisualizationDialog(self):
        sender = self.sender()
        if sender.objectName() == "btNetworkOptions":  # Network
            dialog = ui.EditNetworkOptionDialog(self, options=self.options)
            if dialog.exec_() == QDialog.Accepted:
                options = dialog.getValues()
                if options != self.options.network:
                    self.options.network = options
                    self.has_unsaved_changes = True
                # TODO restart Network graphics
        else:  # t-SNE
            dialog = ui.EditTSNEOptionDialog(self, options=self.options)
            if dialog.exec_() == QDialog.Accepted:
                options = dialog.getValues()
                if options != self.options.tsne:
                    self.options.tsne = options
                    self.has_unsaved_changes = True
                # TODO restart TSNE graphics

    def createGraph(self, nodes_idx, infos, interactions, labels=None):
        # Delete all previously created edges and nodes
        self.graph.delete_edges(self.graph.es)
        self.graph.delete_vertices(self.graph.vs)

        self.graph.add_vertices(nodes_idx.tolist())
        self.graph.add_edges(zip(interactions['Source'], interactions['Target']))

        if infos is not None:
            for col in infos.dtype.names:
                self.graph.vs[col] = infos[col]

        if interactions is not None:
            for col in interactions.dtype.names:
                self.graph.es[col] = interactions[col]

        if labels is not None:
            self.graph.vs['__label'] = labels.astype('str')
        else:
            self.graph.vs['__label'] = nodes_idx.astype('str')

    def draw(self, scores=None, interactions=None, infos=None, labels=None, compute_layouts=True):  # TODO: Use infos and labels
        self.tvNodes.model().sourceModel().beginResetModel()
        self.tvEdges.model().sourceModel().beginResetModel()

        if not compute_layouts and self.graph.network_layout is not None:
            worker, thread = self.drawNetwork(self.gvNetwork, layout=self.graph.network_layout)
        else:
            worker, thread = self.drawNetwork(self.gvNetwork, interactions)

        if not compute_layouts and self.graph.tsne_layout is not None:
            draw_tsne = lambda: self.drawTSNE(self.gvTSNE, layout=self.graph.tsne_layout)
        else:
            draw_tsne = lambda: self.drawTSNE(self.gvTSNE, scores)

        if worker is not None:
            worker.finished.connect(draw_tsne)
        else:
            draw_tsne()

        self.tvNodes.model().sourceModel().endResetModel()
        self.tvEdges.model().sourceModel().endResetModel()
        self.updateSearchBar()

    def onSelectionChanged(self):
        view = self.currentView
        items = view.scene().selectedItems()
        nodes_idx, edges_idx = [], []
        for item in items:
            if item.Type == ui.Node.Type:
                nodes_idx.append(item.index)
            elif item.Type == ui.Edge.Type:
                edges_idx.append(item.index)
        self.tvNodes.model().setSelection(nodes_idx)
        self.tvEdges.model().setSelection(edges_idx)

        if self.actionLinkViews.isChecked():
            if view == self.gvNetwork:
                self.gvTSNE.scene().selectionChanged.disconnect()
                self.gvTSNE.scene().clearSelection()
                try:
                    for idx in nodes_idx:
                        self.graph.vs['__tsne_gobj'][idx].setSelected(True)
                except (KeyError, AttributeError):
                    pass
                self.gvTSNE.scene().selectionChanged.connect(self.onSelectionChanged)
            elif view == self.gvTSNE:
                self.gvNetwork.scene().selectionChanged.disconnect()
                self.gvNetwork.scene().clearSelection()
                try:
                    for idx in nodes_idx:
                        self.graph.vs['__network_gobj'][idx].setSelected(True)
                    for idx in edges_idx:
                        self.graph.es['__network_gobj'][idx].setSelected(True)
                except (KeyError, AttributeError):
                    pass
                self.gvNetwork.scene().selectionChanged.connect(self.onSelectionChanged)

    def doSearch(self, value):
        self.tvNodes.model().setFilterRegExp(str(value))

    def updateSearchBar(self):
        menu = QMenu(self)
        group = QActionGroup(menu, exclusive=True)

        model = self.tvNodes.model()

        for index in range(model.columnCount() + 1):
            text = "All" if index == 0 else model.headerData(index - 1, Qt.Horizontal, Qt.DisplayRole)
            action = group.addAction(QAction(str(text), checkable=True))
            action.setData(index)
            menu.addAction(action)
            if index == 0:
                action.setChecked(True)
                menu.addSeparator()

        self.btSearch.setMenu(menu)
        self.btSearch.setPopupMode(QToolButton.InstantPopup)
        group.triggered.connect(self.updateSearchMenu)
        self.tvNodes.model().setFilterKeyColumn(-1)

    def updateSearchMenu(self, action):
        self.tvNodes.model().setFilterKeyColumn(action.data() - 1)

    def exportToCytoscape(self):
        try:
            from py2cytoscape.data.cyrest_client import CyRestClient

            # Create exportable copy of the graph object
            g = self.graph.copy()
            for attr in g.vs.attributes():
                if attr.startswith('__'):
                    del g.vs[attr]
                else:
                    g.vs[attr] = [str(x) for x in g.vs[attr]]
            for attr in g.es.attributes():
                if attr.startswith('__'):
                    del g.es[attr]
                else:
                    g.es[attr] = [str(x) for x in g.es[attr]]

            cy = CyRestClient()
            # cy.session.delete()
            g_cy = cy.network.create_from_igraph(g)

            # cy.layout.apply(name='force-directed', network=g_cy)

            layout = np.empty((g.vcount(), 2))
            for item in self.currentView.scene().items():
                if item.Type == ui.Node.Type:
                    layout[item.index] = (item.x(), item.y())
            positions = [(suid, x, y) for suid, (x, y) in zip(g_cy.get_nodes()[::-1], layout)]
            cy.layout.apply_from_presets(network=g_cy, positions=positions)

            with open('styles.json', 'r') as f:
                style_js = json.load(f)
            style = cy.style.create('cyREST style', style_js)
            cy.style.apply(style, g_cy)
        except ConnectionRefusedError:
            print('Please launch Cytoscape before trying to export.')
        except ImportError:
            print('py2tocytoscape is required for this action (https://pypi.python.org/pypi/py2cytoscape).')
        except FileNotFoundError:
            print('styles.json not found...')

        # for c in g_cy.get_view(g_cy.get_views()[0])['elements']['nodes']:
        # pos = c['position']
        # id_ = int(c['data']['id_original'])
        # nodes[id_].setPos(QPointF(pos['x'], pos['y']))

    def exportAsImage(self):
        filename, filter_ = QFileDialog.getSaveFileName(self, "Save image",
                                                        filter=("SVG Files (*.svg);;BMP Files (*.bmp);;"
                                                                "JPEG (*.JPEG);;PNG (*.png)"))
        if filename:
            if filter_ == 'SVG Files (*.svg)':
                try:
                    from PyQt5.QtSvg import QSvgGenerator
                except ImportError:
                    print('QtSvg was not found on your system. It is needed for SVG export.')
                else:
                    svg_gen = QSvgGenerator()

                    svg_gen.setFileName(filename)
                    svg_gen.setSize(self.size())
                    svg_gen.setViewBox(self.scene().sceneRect())
                    svg_gen.setTitle("SVG Generator Example Drawing")
                    svg_gen.setDescription("An SVG drawing created by the SVG Generator.")

                    painter = QPainter(svg_gen)
                    self.currentView.scene().render(painter)
                    painter.end()
            else:
                image = QImage(self.view.scene().sceneRect().size().toSize(), QImage.Format_ARGB32)
                image.fill(Qt.transparent)

                painter = QPainter(image)
                self.currentView.scene().render(painter);
                image.save(filename)

    def openProject(self):
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.ExistingFile)
        dialog.setNameFilters(["{} Files (*{})".format(QCoreApplication.applicationName(),
                                                       config.FILE_EXTENSION),
                               "All files (*.*)"])
        if dialog.exec_() == QDialog.Accepted:
            filename = dialog.selectedFiles()[0]
            self.load(filename)

    def saveProject(self):
        if self.fname is None:
            self.saveProjectAs()
        else:
            self.save(self.fname)

    def saveProjectAs(self):
        dialog = QFileDialog(self)
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        dialog.setNameFilters(["{} Files (*{})".format(QCoreApplication.applicationName(),
                                                       config.FILE_EXTENSION),
                               "All files (*.*)"])
        if dialog.exec_() == QDialog.Accepted:
            filename = dialog.selectedFiles()[0]
            self.save(filename)

    def save(self, fname):
        """Save current project to a file for future access"""

        # Export graph to GraphML format
        writer = graphml.GraphMLWriter()
        gxl = writer.tostring(self.graph).decode()

        # Convert list of Spectrum objects to something that be saved
        spectra = getattr(self.network, 'spectra', [])
        spec_infos = [{'id': s.id, 'mz_parent': s.mz_parent} for s in spectra]
        spec_data = {'network/spectra/{}'.format(s.id): s.data for s in spectra}

        # Create dict for saving
        d = {'network/scores': getattr(self.network, 'scores', np.array([])),
             'network/spectra/index.json': spec_infos,
             'network/infos': getattr(self.network, 'infos', np.array([])),
             'graph.gxl': gxl,
             'network_layout': getattr(self.graph, 'network_layout', np.array([])),
             'tsne_layout': getattr(self.graph, 'tsne_layout', np.array([])),
             'options.json': self.options}
        d.update(spec_data)

        try:
            save.savez(fname, version=1, **d)
        except PermissionError as e:
            dialog = QMessageBox(self)
            dialog.warning(self, None, str(e))
            return False
        else:
            self.fname = fname
            self.has_unsaved_changes = False

    def load(self, fname):
        """Load project from a previously saved file"""

        try:
            with save.MnzFile(fname) as fid:
                try:
                    version = int(fid['version'])
                except ValueError:
                    version = 1

                if version == 1:
                    network = Network()
                    network.scores = fid['network/scores']
                    network.infos = fid['network/infos']

                    spec_infos = fid['network/spectra/index.json']
                    network.spectra = [workers.Spectrum(s['id'], s['mz_parent'], fid['network/spectra/{}'.format(s['id'])]) for
                                       s in spec_infos]

                    # Load options
                    options = utils.AttrDict(fid['options.json'])
                    for k, v in options.items():
                        options[k] = utils.AttrDict(v)

                    # Load graph
                    gxl = fid['graph.gxl']
                    parser = graphml.GraphMLParser()
                    graph = parser.fromstring(gxl)

                    graph.network_layout = fid['network_layout']
                    graph.tsne_layout = fid['tsne_layout']

                    self.options = options
                    self.graph = graph
                    self.network = network

                    # Draw
                    self.draw(compute_layouts=False)

                    # Save filename and set window title
                    self.fname = fname
                    self.has_unsaved_changes = False
                else:
                    dialog = QMessageBox(self)
                    dialog.warning(self, None,
                                   "Unrecognized file format version (version={}).".format(version))
                    return False
        except FileNotFoundError:
            dialog = QMessageBox(self)
            dialog.warning(self, None,
                           "File '{}' not found.".format(fname))
            return False


if __name__ == '__main__':
    import logging
    from logging.handlers import RotatingFileHandler

    from PyQt5.QtWidgets import QApplication, QMainWindow
    from PyQt5.QtCore import QCoreApplication


    def exceptionHandler(exctype, value, trace):
        """
            This exception handler prevents quitting to the command line when there is
            an unhandled exception while processing a Qt signal.

            The script/application willing to use it should implement code similar to:

            .. code-block:: python
            
                if __name__ == "__main__":
                    sys.excepthook = exceptionHandler
            
            """

        logger.error('{} in {}'.format(exctype.__name__, trace.tb_frame.f_code.co_name),
                     exc_info=(exctype, value, trace))
        msg = QMessageBox(window)
        msg.setWindowTitle("Unhandled exception")
        msg.setIcon(QMessageBox.Warning)
        msg.setText(("It seems you have found a bug in {}. Please report details.\n"
                     "You should restart the application now.").format(QCoreApplication.applicationName()))
        msg.setInformativeText(str(value))
        msg.setDetailedText(''.join(traceback.format_exception(exctype, value, trace)))
        btRestart = msg.addButton("Restart now", QMessageBox.ResetRole)
        msg.addButton(QMessageBox.Ignore)
        msg.raise_()
        msg.exec_()
        if msg.clickedButton() == btRestart:  # Restart application
            os.execv(sys.executable, [sys.executable] + sys.argv)


    # Create logger
    if not os.path.exists(LOG_PATH):
        os.makedirs(LOG_PATH)

    logger = logging.getLogger()
    formatter = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s')
    file_handler = RotatingFileHandler(os.path.join(LOG_PATH, '{}.log'.format(__file__)), 'a', 1000000, 1)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    if DEBUG:
        stream_handler = logging.StreamHandler()
        logger.addHandler(stream_handler)

        logger.setLevel(logging.DEBUG)
        file_handler.setLevel(logging.DEBUG)
        stream_handler.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.WARN)
        file_handler.setLevel(logging.WARN)

    app = QApplication(sys.argv)

    QCoreApplication.setOrganizationDomain("CNRS")
    QCoreApplication.setOrganizationName("ICSN")
    QCoreApplication.setApplicationName("tsne-network")
    QCoreApplication.setApplicationVersion("0.1")

    window = MainWindow()

    sys.excepthook = exceptionHandler

    window.show()

    # Support for file association
    if len(sys.argv) > 1:
        fname = sys.argv[1]
        if os.path.exists(fname) and os.path.splitext(fname)[1] == '.mnz':
            window.load(fname)

    sys.exit(app.exec_())
