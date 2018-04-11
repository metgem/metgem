#!/usr/bin/env python

import sys
import os
import traceback
import json

from pyteomics.auxiliary import PyteomicsError
from requests import ConnectionError

import numpy as np
import igraph as ig

from PyQt5.QtWidgets import (QDialog, QFileDialog,
                             QMessageBox, QWidget,
                             QMenu, QToolButton, QActionGroup,
                             QAction, QDockWidget, QWIDGETSIZE_MAX)
from PyQt5.QtCore import QSettings, Qt, QSignalMapper, QSize
from PyQt5.QtGui import QPainter, QImage, QCursor

from PyQt5 import uic

from lib import ui, config, utils, workers, errors

MAIN_UI_FILE = os.path.join('lib', 'ui', 'main_window.ui')
if getattr(sys, 'frozen', False):
    MAIN_UI_FILE = os.path.join(sys._MEIPASS, MAIN_UI_FILE)

DEBUG = os.getenv('DEBUG_MODE', 'false').lower() in ('true', '1')
EMBED_JUPYTER = os.getenv('EMBED_JUPYTER', 'false').lower() in ('true', '1')

if sys.platform.startswith('win'):
    LOG_PATH = os.path.expandvars(r'%APPDATA%\tsne-network\log')
    DATABASES_PATH = os.path.expandvars(r'%APPDATA%\tsne-network\databases')
elif sys.platform.startswith('darwin'):
    LOG_PATH = os.path.expanduser('~/Library/Logs/tsne-network/log')
    DATABASES_PATH = os.path.expanduser(r'~/Library/tsne-network/databases')
elif sys.platform.startswith('linux'):
    LOG_PATH = os.path.expanduser('~/.config/tsne-network/log')
    DATABASES_PATH = os.path.expanduser(r'~/.config/tsne-network/databases')
else:
    LOG_PATH = 'log'
    DATABASES_PATH = 'databases'

MainWindowUI, MainWindowBase = uic.loadUiType(MAIN_UI_FILE, from_imports='lib.ui', import_from='lib.ui')


class MainWindow(MainWindowBase, MainWindowUI):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Keep track of unsaved changes
        self._has_unsaved_changes = False

        # Opened file
        self.fname = None

        # Workers' references
        self._workers = workers.WorkerSet(self)

        # Create graph
        self.graph = ig.Graph()

        # Setup User interface
        self.setupUi(self)
        self.gvNetwork.setFocus()

        # Activate first tab of tab widget
        self.tabWidget.setCurrentIndex(0)

        # Create a corner button to hide/show pages of tab widget
        w = QToolButton(self)
        w.setArrowType(Qt.DownArrow)
        w.setIconSize(QSize(12, 12))
        w.setAutoRaise(True)
        self.tabWidget.setCornerWidget(w, Qt.TopRightCorner)

        # Assigning cosine computation and visualization default options
        self.options = utils.AttrDict({'cosine': workers.CosineComputationOptions(),
                                       'network': workers.NetworkVisualizationOptions(),
                                       'tsne': workers.TSNEVisualizationOptions()})

        # Create an object to store all computed objects
        self.network = utils.Network()

        # Add model to table views
        for table, Model, name in ((self.tvNodes, ui.widgets.NodesModel, "Nodes"),
                                   (self.tvEdges, ui.widgets.EdgesModel, "Edges")):
            table.setSortingEnabled(True)
            model = Model(self)
            proxy = ui.widgets.ProxyModel()
            proxy.setSourceModel(model)
            table.setModel(proxy)
            table.setItemDelegate(ui.widgets.EnsureStringItemDelegate())

        # Move search layout to search toolbar
        w = QWidget()
        self.layoutSearch.setParent(None)
        w.setLayout(self.layoutSearch)
        self.tbSearch.addWidget(w)

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
        self.tvNodes.horizontalHeader().customContextMenuRequested.connect(self.on_nodes_header_contextmenu)
        #self.tvNodes.selectionModel().selectionChanged.connect(self.on_nodes_table_selection_changed)
        self.tvNodes.customContextMenuRequested.connect(self.on_nodes_table_contextmenu)

        self.gvNetwork.scene().selectionChanged.connect(self.on_scene_selection_changed)
        self.gvTSNE.scene().selectionChanged.connect(self.on_scene_selection_changed)
        self.gvNetwork.showSpectrumTriggered.connect(lambda node: self.on_show_spectrum_triggered('show', node))
        self.gvTSNE.showSpectrumTriggered.connect(lambda node: self.on_show_spectrum_triggered('show', node))
        self.gvNetwork.compareSpectrumTriggered.connect(lambda node: self.on_show_spectrum_triggered('compare', node))
        self.gvTSNE.compareSpectrumTriggered.connect(lambda node: self.on_show_spectrum_triggered('compare', node))

        self.actionQuit.triggered.connect(self.close)
        self.actionAbout.triggered.connect(self.on_about_triggered)
        self.actionAboutQt.triggered.connect(self.on_about_qt_triggered)
        self.actionProcessFile.triggered.connect(self.on_process_file_triggered)
        self.actionCurrentParameters.triggered.connect(self.on_current_parameters_triggered)
        self.actionZoomIn.triggered.connect(lambda: self.current_view.scaleView(1.2))
        self.actionZoomOut.triggered.connect(lambda: self.current_view.scaleView(1 / 1.2))
        self.actionZoomToFit.triggered.connect(self.current_view.zoomToFit)
        self.actionZoomSelectedRegion.triggered.connect(
            lambda: self.current_view.fitInView(self.current_view.scene().selectionArea().boundingRect(),
                                                Qt.KeepAspectRatio))
        self.leSearch.textChanged.connect(self.on_search_text_changed)
        self.actionOpen.triggered.connect(self.on_open_project_triggered)
        self.actionSave.triggered.connect(self.on_save_project_triggered)
        self.actionSaveAs.triggered.connect(self.on_save_project_as_triggered)

        self.actionFullScreen.triggered.connect(self.on_full_screen_triggered)
        self.actionHideSelected.triggered.connect(self.current_view.scene().hideSelectedItems)
        self.actionShowAll.triggered.connect(self.current_view.scene().showAllItems)
        self.actionNeighbors.triggered.connect(
            lambda: self.on_select_first_neighbors_triggered(self.current_view.scene().selectedItems()))
        self.actionExportToCytoscape.triggered.connect(self.on_export_to_cytoscape_triggered)
        self.actionExportAsImage.triggered.connect(self.on_export_as_image_triggered)

        self.actionDownloadDatabases.triggered.connect(self.on_download_databases_triggered)
        self.actionViewDatabases.triggered.connect(self.on_view_databases_triggered)

        self._mapper = QSignalMapper(self)
        self.btNetworkOptions.clicked.connect(self._mapper.map)
        self._mapper.setMapping(self.btNetworkOptions, 'network')
        self.btTSNEOptions.clicked.connect(self._mapper.map)
        self._mapper.setMapping(self.btTSNEOptions, 't-sne')
        self._mapper.mapped[str].connect(self.on_edit_options_triggered)

        self.tabWidget.cornerWidget(Qt.TopRightCorner).clicked.connect(self.minimize_tabwidget)

        # Add a menu to show/hide toolbars
        popup_menu = self.createPopupMenu()
        popup_menu.setTitle("Toolbars")
        self.menuView.addMenu(popup_menu)

        # Build research bar
        self.update_search_menu()

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
            self.actionSave.setEnabled(True)
        else:
            self.actionSave.setEnabled(False)

        self._has_unsaved_changes = value
        self.setWindowTitle(self.window_title)

    @property
    def current_view(self):
        for view in (self.gvNetwork, self.gvTSNE):
            if view.hasFocus():
                return view
        return self.gvNetwork

    def load_project(self, filename):
        worker = self.prepare_load_project_worker(filename)
        if worker is not None:
            self._workers.add(worker)

    def save_project(self, filename):
        worker = self.prepare_save_project_worker(filename)
        if worker is not None:
            self._workers.add(worker)

    def update_search_menu(self):
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
        group.triggered.connect(lambda: self.tvNodes.model().setFilterKeyColumn(action.data()-1))
        self.tvNodes.model().setFilterKeyColumn(-1)

    def keyPressEvent(self, event):
        key = event.key()

        if key == Qt.Key_M:  # Show/hide minimap
            view = self.current_view
            view.minimap.setVisible(not view.minimap.isVisible())

    def showEvent(self, event):
        self.load_settings()
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
            self.save_settings()
        else:
            event.ignore()

    def on_scene_selection_changed(self):
        view = self.current_view
        nodes_idx = [item.index() for item in view.scene().selectedNodes()]
        edges_idx = [item.index() for item in view.scene().selectedEdges()]
        self.tvNodes.model().setSelection(nodes_idx)
        self.tvEdges.model().setSelection(edges_idx)

        if self.actionLinkViews.isChecked():
            if view == self.gvNetwork:
                with utils.SignalBlocker(self.gvTSNE.scene()):
                    self.gvTSNE.scene().setNodesSelection(nodes_idx)
            elif view == self.gvTSNE:
                with utils.SignalBlocker(self.gvNetwork.scene()):
                    self.gvNetwork.scene().setNodesSelection(nodes_idx)

    def on_search_text_changed(self, value):
        self.tvNodes.model().setFilterRegExp(str(value))

    def on_open_project_triggered(self):
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.ExistingFile)
        dialog.setNameFilters([f"{QCoreApplication.applicationName()} Files (*{config.FILE_EXTENSION})",
                               "All files (*.*)"])
        if dialog.exec_() == QDialog.Accepted:
            filename = dialog.selectedFiles()[0]
            self.load_project(filename)

    def on_save_project_triggered(self):
        if self.fname is None:
            self.on_save_project_as_triggered()
        else:
            self.save_project(self.fname)

    def on_save_project_as_triggered(self):
        dialog = QFileDialog(self)
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        dialog.setNameFilters([f"{QCoreApplication.applicationName()} Files (*{config.FILE_EXTENSION})",
                               "All files (*.*)"])
        if dialog.exec_() == QDialog.Accepted:
            filename = dialog.selectedFiles()[0]
            self.save_project(filename)

    def on_about_triggered(self):
        message = (f'Version: {QCoreApplication.applicationVersion()}',
                   '',
                   'Should say something here.')
        QMessageBox.about(self, f'About {QCoreApplication.applicationName()}',
                     '\n'.join(message))

    def on_about_qt_triggered(self):
        QMessageBox.aboutQt(self)

    def on_export_to_cytoscape_triggered(self):
        try:
            from py2cytoscape.data.cyrest_client import CyRestClient

            cy = CyRestClient()

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

            # cy.session.delete()
            g_cy = cy.network.create_from_igraph(g)

            # cy.layout.apply(name='force-directed', network=g_cy)

            layout = np.empty((g.vcount(), 2))
            for item in self.current_view.scene().nodes():
                layout[item.index()] = (item.x(), item.y())
            positions = [(suid, x, y) for suid, (x, y) in zip(g_cy.get_nodes()[::-1], layout)]
            cy.layout.apply_from_presets(network=g_cy, positions=positions)

            with open('styles.json', 'r') as f:
                style_js = json.load(f)
            style = cy.style.create('cyREST style', style_js)
            cy.style.apply(style, g_cy)
        except (ConnectionRefusedError, ConnectionError):
            QMessageBox.information(self, None,
                               'Please launch Cytoscape before trying to export.')
        except json.decoder.JSONDecodeError:
            QMessageBox.information(self, None,
                               'Cytoscape was not ready to receive data. Please try again.')
        except ImportError:
            QMessageBox.information(self, None,
                               'py2tocytoscape is required for this action (https://pypi.python.org/pypi/py2cytoscape).')
        except FileNotFoundError:
            QMessageBox.warning(self, None,
                           f'styles.json not found. You may have to reinstall {QCoreApplication.applicationName()}')

        # for c in g_cy.get_view(g_cy.get_views()[0])['elements']['nodes']:
        # pos = c['position']
        # id_ = int(c['data']['id_original'])
        # nodes[id_].setPos(QPointF(pos['x'], pos['y']))

    def on_export_as_image_triggered(self):
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
                    self.current_view.scene().render(painter)
                    painter.end()
            else:
                image = QImage(self.view.scene().sceneRect().size().toSize(), QImage.Format_ARGB32)
                image.fill(Qt.transparent)

                painter = QPainter(image)
                self.current_view.scene().render(painter)
                image.save(filename)

    def on_show_spectrum_triggered(self, type_, node):
        if self.network.spectra is not None:
            try:
                data = self.network.spectra[node.index()].human_readable_data
            except KeyError:
                dialog = QDialog(self)
                dialog.warning(self, None, 'Selected spectrum does not exists.')
            else:
                # Set data as first or second spectrum
                if type_ == 'compare':
                    self.cvSpectrum.set_spectrum2(data, node.label)
                else:
                    self.cvSpectrum.set_spectrum1(data, node.label)

                # Show spectrum tab
                self.tabWidget.setCurrentIndex(self.tabWidget.indexOf(self.cvSpectrum))

    def on_select_first_neighbors_triggered(self, items):
        view = self.current_view
        for item in items:
            if item.Type == ui.Node.Type:
                for v in self.graph.vs[item.index()].neighbors():
                    try:
                        if view == self.gvNetwork:
                            v['__network_gobj'].setSelected(True)
                        elif view == self.gvTSNE:
                            v['__tsne_gobj'].setSelected(True)
                    except (KeyError, AttributeError):
                        pass

    def on_nodes_header_contextmenu(self, event):
        """ A right click on a column name allows the info to be displayed in the graphView """
        selected_column_index = self.tvNodes.columnAt(event.x())
        if selected_column_index != -1:
            menu = QMenu(self)
            action = QAction("Use column as node labels", self)
            menu.addAction(action)
            menu.popup(QCursor.pos())
            action.triggered.connect(lambda: self.set_nodes_label(selected_column_index))

    def on_nodes_table_contextmenu(self, event):
        selected_column_index = self.tvNodes.columnAt(event.x())
        selected_row_index = self.tvNodes.rowAt(event.y())
        if selected_column_index != -1 and selected_row_index != -1:
            menu = QMenu(self)
            action = QAction("Highlight selected nodes", self)
            menu.addAction(action)
            menu.popup(QCursor.pos())
            action.triggered.connect(lambda: self.highlight_selected_nodes())

    def highlight_selected_nodes(self):
        selected = {index.row() for index in self.tvNodes.selectionModel().selectedIndexes()}
        network_deselected = {item.index() for item in self.gvNetwork.scene().selectedItems()} - selected
        tsne_deselected = {item.index() for item in self.gvNetwork.scene().selectedItems()} - selected
        with utils.SignalBlocker(self.gvNetwork.scene(), self.gvTSNE.scene()):
            network_nodes = self.graph.vs['__network_gobj']
            tsne_nodes = self.graph.vs['__tsne_gobj']
            for index in network_deselected:
                network_nodes[index].setSelected(False)
            for index in tsne_deselected:
                tsne_nodes[index].setSelected(False)
            for index in selected:
                network_nodes[index].setSelected(True)
                tsne_nodes[index].setSelected(True)

    def on_current_parameters_triggered(self):
        dialog = ui.CurrentParametersDialog(self, options=self.options)
        dialog.exec_()

    def on_full_screen_triggered(self):
        if not self.isFullScreen():
            self.setWindowFlags(Qt.Window)
            self.showFullScreen()
        else:
            self.setWindowFlags(Qt.Widget)
            self.showNormal()

    def on_process_file_triggered(self):
        dialog = ui.OpenFileDialog(self, options=self.options)
        if dialog.exec_() == QDialog.Accepted:
            self.fname = None
            self.has_unsaved_changes = True
            self.gvNetwork.scene().clear()
            self.gvTSNE.scene().clear()

            process_file, use_metadata, metadata_file, csv_separator,\
                compute_options, tsne_options, network_options = dialog.getValues()
            self.options.cosine = compute_options
            self.options.tsne = tsne_options
            self.options.network = network_options

            worker = self.prepare_read_mgf_worker(process_file, metadata_file, csv_separator)
            if worker is not None:
                self._workers.add(worker)

    def on_edit_options_triggered(self, type_):
        if hasattr(self.network, 'scores'):
            if type_ == 'network':
                dialog = ui.EditNetworkOptionsDialog(self, options=self.options)
                if dialog.exec_() == QDialog.Accepted:
                    options = dialog.getValues()
                    if options != self.options.network:
                        self.options.network = options
                        self.has_unsaved_changes = True

                        interactions = workers.generate_network(self.network.scores,
                                                        self.network.spectra,
                                                        self.options.network,
                                                        use_self_loops=True)
                        self.create_graph(interactions)
                        self.draw(which='network', interactions=interactions)
                        try:
                            self.graph.vs['__tsne_gobj'] = self.gvTSNE.nodes()
                        except AttributeError:
                            pass
                        self.update_search_menu()
            elif type_ == 't-sne':
                dialog = ui.EditTSNEOptionsDialog(self, options=self.options)
                if dialog.exec_() == QDialog.Accepted:
                    options = dialog.getValues()
                    if options != self.options.tsne:
                        self.options.tsne = options
                        self.has_unsaved_changes = True

                        self.draw(which='t-sne')
                        self.update_search_menu()
        else:
            QMessageBox.information(self, None, "No network found, please open a file first.")

    def on_download_databases_triggered(self):
        dialog = ui.DownloadDatabasesDialog(self, base_path=DATABASES_PATH)
        dialog.exec_()

    def on_view_databases_triggered(self):
        dialog = ui.ViewDatabasesDialog(self, base_path=DATABASES_PATH)
        dialog.exec_()

    def show_items(self, items):
        for item in items:
            item.show()

    def hide_items(self, items):
        for item in items:
            item.hide()

    def minimize_tabwidget(self):
        w = self.tabWidget.cornerWidget(Qt.TopRightCorner)
        if w.arrowType() == Qt.DownArrow:
            w.setArrowType(Qt.UpArrow)
            self.tabWidget.setMaximumHeight(self.tabWidget.tabBar().height())
            self.tabWidget.setDocumentMode(True)
        else:
            w.setArrowType(Qt.DownArrow)
            self.tabWidget.setDocumentMode(False)
            self.tabWidget.setMaximumHeight(QWIDGETSIZE_MAX)

    def set_nodes_label(self, column_index):
        model = self.tvNodes.model().sourceModel()
        for i, vertex in enumerate(self.graph.vs):
            try:
                label = str(model.index(i, column_index).data())
                vertex['__tsne_gobj'].setLabel(label)
                vertex['__network_gobj'].setLabel(label)
            except (KeyError, AttributeError):
                pass
        self.gvNetwork.scene().update()

    def save_settings(self):
        settings = QSettings()
        settings.setValue('MainWindow.Geometry', self.saveGeometry())
        settings.setValue('MainWindow.State', self.saveState())
        settings.setValue('MainWindow.TabWidget.State',
                          self.tabWidget.cornerWidget(Qt.TopRightCorner).arrowType() == Qt.UpArrow)

    def load_settings(self):
        settings = QSettings()
        setting = settings.value('MainWindow.Geometry')
        if setting is not None:
            self.restoreGeometry(setting)
            setting = settings.value('MainWindow.State')
        if setting is not None:
            self.restoreState(setting)
        setting = settings.value('MainWindow.TabWidget.State', type=bool)
        if setting:
            self.minimize_tabwidget()

    def create_graph(self, interactions, labels=None):
        # Delete all previously created edges and nodes
        self.tvNodes.model().sourceModel().beginResetModel()
        self.tvEdges.model().sourceModel().beginResetModel()

        self.graph.delete_edges(self.graph.es)
        self.graph.delete_vertices(self.graph.vs)

        nodes_idx = np.arange(self.network.scores.shape[0])
        self.graph.add_vertices(nodes_idx.tolist())
        self.graph.add_edges(zip(interactions['Source'], interactions['Target']))

        if self.network.infos is not None:
            for col in self.network.infos.dtype.names:
                self.graph.vs[col] = self.network.infos[col]

        if interactions is not None:
            for col in interactions.dtype.names:
                self.graph.es[col] = interactions[col]

        if labels is not None:
            self.graph.vs['__label'] = labels.astype('str')
        else:
            self.graph.vs['__label'] = nodes_idx.astype('str')

        self.tvNodes.model().sourceModel().endResetModel()
        self.tvEdges.model().sourceModel().endResetModel()

    def draw(self, interactions=None, compute_layouts=True, which='all'):
        if which == 'all':
            which = {'network', 't-sne'}
        elif isinstance(which, str):
            which = set((which,))

        self.tvNodes.model().sourceModel().beginResetModel()
        self.tvEdges.model().sourceModel().beginResetModel()

        worker = None
        if 'network' in which:
            if not compute_layouts and self.graph.network_layout is not None:
                worker = self.prepare_draw_network_worker(layout=self.graph.network_layout)
            else:
                worker = self.prepare_draw_network_worker(interactions=interactions)

        if 't-sne' in which:
            layout = None

            def draw_tsne():
                worker = self.prepare_draw_tsne_worker(layout=layout)
                self._workers.add(worker)

            if not compute_layouts and self.graph.tsne_layout is not None:
                layout = self.graph.tsne_layout

            if worker is not None:
                worker.finished.connect(draw_tsne)
            else:
                draw_tsne()

        if worker is not None:
            self._workers.add(worker)

        self.tvNodes.model().sourceModel().endResetModel()
        self.tvEdges.model().sourceModel().endResetModel()
        self.update_search_menu()

    def apply_layout(self, layout, view):
        view.scene().setLayout(layout)

        view.scene().setSceneRect(view.scene().itemsBoundingRect())
        view.zoomToFit()
        view.minimap.zoomToFit()

    def apply_network_layout(self, layout):
        self.apply_layout(layout, self.gvNetwork)
        self.graph.network_layout = layout

    def apply_tsne_layout(self, layout):
        self.apply_layout(layout, self.gvTSNE)
        self.graph.tsne_layout = layout

    def prepare_draw_network_worker(self, interactions=None, layout=None):
        self.gvNetwork.scene().clear()

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
        self.graph.vs['__network_gobj'] = nodes = self.gvNetwork.scene().addNodes(self.graph.vs.indices,
                                                                                  self.graph.vs['__label'])

        # Add edges
        edges_attr = [(e.index, nodes[e.source], nodes[e.target], e['__weight'], e['__width'])
                      for e in self.graph.es if not e.is_loop()]
        self.graph.es['__network_gobj'] = self.gvNetwork.scene().addEdges(*zip(*edges_attr))

        if layout is None:
            # Compute layout
            def process_finished():
                layout = worker.result()
                if layout is not None:
                    self.apply_network_layout(layout)

            worker = workers.NetworkWorker(self.graph)
            worker.finished.connect(process_finished)

            return worker
        else:
            worker = workers.GenericWorker(self.apply_network_layout, layout)
            return worker

    def prepare_draw_tsne_worker(self, layout=None):
        self.gvTSNE.scene().clear()

        # Add nodes
        self.graph.vs['__tsne_gobj'] = self.gvTSNE.scene().addNodes(self.graph.vs.indices,
                                                                    self.graph.vs['__label'])

        if layout is None:
            # Compute layout
            def process_finished():
                layout = worker.result()
                if layout is not None:
                    self.apply_tsne_layout(layout)

            worker = workers.TSNEWorker(self.network.scores, self.options.tsne)
            worker.finished.connect(process_finished)

            return worker
        else:
            worker = workers.GenericWorker(self.apply_tsne_layout, layout)
            return worker

    def prepare_compute_scores_worker(self, spectra, use_multiprocessing):
        def error(e):
            if e.__class__ == OSError:
                QMessageBox.warning(self, None, str(e))
            else:
                raise e

        worker = workers.ComputeScoresWorker(spectra, use_multiprocessing, self.options.cosine)
        worker.error.connect(error)

        return worker

    def prepare_read_mgf_worker(self, mgf_filename, metadata_filename = None, csv_separator = None):
        worker = workers.ReadMGFWorker(mgf_filename, self.options.cosine)

        def mgf_file_read():
            nonlocal worker
            self.network.spectra = worker.result()
            multiprocess = len(self.network.spectra) > 1000  # TODO: Tune this, arbitrary decision
            worker = self.prepare_compute_scores_worker(self.network.spectra, multiprocess)
            if worker is not None:
                worker.finished.connect(scores_computed)
                self._workers.add(worker)

        def mgf_error(e):
            if e.__class__ == PyteomicsError:
                QMessageBox.warning(self, None, e.message)

        def scores_computed():
            nonlocal worker
            self.network.scores = worker.result()
            interactions = workers.generate_network(self.network.scores,
                                                    self.network.spectra,
                                                    self.options.network,
                                                    use_self_loops=True)
            self.network.infos = np.array([(spectrum.mz_parent,) for spectrum in self.network.spectra],
                                          dtype=[('m/z parent', np.float32)])
            self.create_graph(interactions)
            self.draw(interactions=interactions)
            if metadata_filename is not None:
                worker = workers.ReadMetadataWorker(metadata_filename, csv_separator)
                if worker is not None:
                    worker.finished.connect(metadata_file_read)
                    self._workers.add(worker)

        def metadata_file_read():
            nonlocal worker
            data = worker.result()
            self.tvNodes.model().sourceModel().beginResetModel()
            for column in data:
                self.graph.vs[column] = data[column]
            self.tvNodes.model().sourceModel().endResetModel()

        worker.finished.connect(mgf_file_read)
        worker.error.connect(mgf_error)
        return worker

    def prepare_save_project_worker(self, fname):
        """Save current project to a file for future access"""

        def process_finished():
            self.fname = fname
            self.has_unsaved_changes = False

        def error(e):
            if e.__class__ == PermissionError:
                QMessageBox.warning(self, None, str(e))
            else:
                raise e

        worker = workers.SaveProjectWorker(fname, self.graph, self.network, self.options)
        worker.finished.connect(process_finished)
        worker.error.connect(error)

        return worker

    def prepare_load_project_worker(self, fname):
        """Load project from a previously saved file"""

        def process_finished():
            graph, network, options = worker.result()

            self.options = options
            self.graph = graph
            self.network = network

            # Draw
            self.draw(compute_layouts=False)

            # Save filename and set window title
            self.fname = fname
            self.has_unsaved_changes = False

        def error(e):
            if isinstance(e, FileNotFoundError):
                QMessageBox.warning(self, None, f"File '{self.filename}' not found.")
            elif isinstance(e, errors.UnsupportedVersionError):
                QMessageBox.warning(self, None, str(e))
            else:
                raise e

        worker = workers.LoadProjectWorker(fname)
        worker.finished.connect(process_finished)
        worker.error.connect(error)

        return worker


if __name__ == '__main__':
    import logging
    from logging.handlers import RotatingFileHandler

    from PyQt5.QtWidgets import QApplication
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

        if trace is not None:
            msg = f"{exctype.__name__} in {trace.tb_frame.f_code.co_name}"
        else:
            msg = exctype.__name__
        logger.error(msg, exc_info=(exctype, value, trace))
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
    file_handler = RotatingFileHandler(os.path.join(LOG_PATH, f'{os.path.basename(__file__)}.log'), 'a', 1000000, 1)
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
            window.load_project(fname)

    sys.exit(app.exec_())
