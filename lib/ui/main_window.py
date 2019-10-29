import bisect
import csv
import io
from typing import List, Callable, Dict, Union, Tuple

from .. import config, ui, utils, workers, errors
from ..utils.network import Network
from ..logger import get_logger, debug

import os
import sys
import json
import zipfile
import subprocess

import requests

import numpy as np
import igraph as ig
import sqlalchemy

from PyQt5.QtWidgets import (QDialog, QFileDialog, QMessageBox, QWidget, QMenu, QActionGroup, QMainWindow,
                             QAction, qApp, QTableView, QComboBox, QToolBar,
                             QApplication, QGraphicsView, QLineEdit)
from PyQt5.QtCore import QSettings, Qt, QCoreApplication
from PyQt5.QtGui import QPainter, QImage, QColor, QKeyEvent, QIcon, QFontMetrics, QFont, QKeySequence

from PyQt5 import uic

from PyQtNetworkView import style_from_css, style_to_cytoscape, disable_opengl

from PyQtAds.QtAds import (CDockManager, CDockWidget,
                           BottomDockWidgetArea, CenterDockWidgetArea,
                           TopDockWidgetArea, LeftDockWidgetArea)

from libmetgem import human_readable_data

UI_FILE = os.path.join(os.path.dirname(__file__), 'main_window.ui')
MainWindowUI, MainWindowBase = uic.loadUiType(UI_FILE, from_imports='lib.ui', import_from='lib.ui')

COLUMN_MAPPING_PIE_CHARTS = 0
COLUMN_MAPPING_LABELS = 1
COLUMN_MAPPING_NODES_SIZES = 2
COLUMN_MAPPING_NODES_COLORS = 3


# noinspection PyCallByClass,PyArgumentList
class MainWindow(MainWindowBase, MainWindowUI):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._logger = get_logger()

        # Keep track of unsaved changes
        self._has_unsaved_changes = False

        # Opened file
        self.fname = None

        # Workers' references
        self._workers = workers.WorkerQueue(self, ui.ProgressDialog(self))

        # List of Network widgets
        self._network_docks = {}

        # Style of network widgets
        self._style = None

        # Network object
        self._network = None

        # Setup User interface
        if not config.get_use_opengl_flag():
            disable_opengl(True)
        self.setupUi(self)

        # Add Dockable Windows
        self.add_docks()

        # Add model to table views
        self.tvNodes.setModel(ui.widgets.NodesModel(self))
        self.tvEdges.setModel(ui.widgets.EdgesModel(self))

        # Init project's objects
        self.init_project()

        # Move search layout to search toolbar
        self.search_widget = QWidget()
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'widgets', 'search.ui'), self.search_widget)
        self.tbSearch.addWidget(self.search_widget)

        # Reorganise export as image actions
        export_button = ui.widgets.ToolBarMenu()
        export_button.setDefaultAction(self.actionExportAsImage)
        export_button.addAction(self.actionExportAsImage)
        export_button.addAction(self.actionExportCurrentViewAsImage)
        self.tbExport.insertWidget(self.actionExportAsImage, export_button)
        self.tbExport.removeAction(self.actionExportAsImage)
        self.tbExport.removeAction(self.actionExportCurrentViewAsImage)

        # Reorganize export metadata actions
        export_button = ui.widgets.ToolBarMenu()
        export_button.setDefaultAction(self.actionExportMetadata)
        export_button.addAction(self.actionExportMetadata)
        export_button.addAction(self.actionExportDatabaseResults)
        self.tbExport.insertWidget(self.actionExportMetadata, export_button)
        self.tbExport.removeAction(self.actionExportMetadata)
        self.tbExport.removeAction(self.actionExportDatabaseResults)

        # Create actions to add new views
        create_network_button = ui.widgets.ToolBarMenu()
        create_network_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        set_default = True
        for view_class in ui.widgets.AVAILABLE_NETWORK_WIDGETS.values():
            action = create_network_button.addAction('Add {} view'.format(view_class.title))
            action.setIcon(self.actionAddNetworkView.icon())
            action.setData(view_class)
            action.triggered.connect(self.on_add_view_triggered)
            if set_default:
                create_network_button.setDefaultAction(action)
                set_default = False
        self.tbFile.insertWidget(self.actionAddNetworkView, create_network_button)
        self.tbFile.removeAction(self.actionAddNetworkView)

        color_button = ui.widgets.ColorPicker(self.actionSetNodesColor, color_group='Node', default_color=Qt.blue)
        self.tbNetwork.insertWidget(self.actionSetNodesColor, color_button)
        self.tbNetwork.removeAction(self.actionSetNodesColor)

        size_combo = QComboBox(self.tbNetwork)
        size_combo.setFixedSize(self.tbNetwork.height() + 60, self.tbNetwork.height())
        size_combo.setEditable(True)
        size_combo.setInsertPolicy(QComboBox.NoInsert)
        items = [str(x) for x in range(10, 101, 10)]
        size_combo.addItems(items)
        size_combo.setCurrentText(str(config.RADIUS))
        size_combo.setCurrentIndex(items.index(str(config.RADIUS)))
        size_combo.setStatusTip(self.actionSetNodesSize.statusTip())
        size_combo.setToolTip(self.actionSetNodesSize.toolTip())
        edit = QLineEdit()
        size_action = edit.addAction(self.actionSetNodesSize.icon(), QLineEdit.LeadingPosition)
        size_combo.setLineEdit(edit)
        self.tbNetwork.insertWidget(self.actionSetNodesSize, size_combo)
        self.tbNetwork.removeAction(self.actionSetNodesSize)

        # Connect events
        self.nodes_widget.actionUseColumnForLabels.triggered.connect(
            lambda: self.on_use_columns_for(COLUMN_MAPPING_LABELS))
        self.nodes_widget.actionResetLabelMapping.triggered.connect(lambda: self.set_nodes_label(None))
        self.nodes_widget.actionUseColumnsForPieCharts.triggered.connect(
            lambda: self.on_use_columns_for(COLUMN_MAPPING_PIE_CHARTS))
        self.nodes_widget.actionResetPieColorMapping.triggered.connect(lambda: self.set_nodes_pie_chart_values(None))
        self.nodes_widget.actionUseColumnForNodesSizes.triggered.connect(
            lambda: self.on_use_columns_for(COLUMN_MAPPING_NODES_SIZES))
        self.nodes_widget.actionResetSizeMapping.triggered.connect(lambda: self.set_nodes_sizes_values(None))
        self.nodes_widget.actionUseColumnForNodesColors.triggered.connect(
            lambda: self.on_use_columns_for(COLUMN_MAPPING_NODES_COLORS))
        self.nodes_widget.actionResetColorMapping.triggered.connect(lambda: self.set_nodes_colors_values(None))
        self.nodes_widget.btHighlightSelectedNodes.clicked.connect(self.highlight_selected_nodes)
        self.nodes_widget.actionViewSpectrum.triggered.connect(
            lambda: self.on_show_spectrum_from_table_triggered('show'))
        self.nodes_widget.actionViewCompareSpectrum.triggered.connect(
            lambda: self.on_show_spectrum_from_table_triggered('compare'))
        self.nodes_widget.actionFindStandards.triggered.connect(lambda: self.on_query_databases('standards'))
        self.nodes_widget.actionFindAnalogs.triggered.connect(lambda: self.on_query_databases('analogs'))

        self.edges_widget.actionHighlightSelectedEdges.triggered.connect(self.highlight_selected_edges)
        self.edges_widget.actionHighlightNodesFromSelectedEdges.triggered.connect(
            self.highlight_nodes_from_selected_edges)

        for dock in self.network_docks.values():
            widget = dock.widget()
            view = dock.widget().gvNetwork
            scene = view.scene()
            scene.selectionChanged.connect(self.on_scene_selection_changed)
            view.focusedIn.connect(lambda: self.on_scene_selection_changed(update_view=False))
            scene.pieChartsVisibilityChanged.connect(
                lambda visibility: self.actionSetPieChartsVisibility.setChecked(visibility))
            widget.btOptions.clicked.connect(lambda: self.on_edit_options_triggered(widget))

        self.actionQuit.triggered.connect(self.close)
        self.actionAbout.triggered.connect(lambda: ui.AboutDialog().exec_())
        self.actionAboutQt.triggered.connect(lambda: QMessageBox.aboutQt(self))
        self.actionProcessFile.triggered.connect(self.on_process_file_triggered)
        self.actionImportMetadata.triggered.connect(self.on_import_metadata_triggered)
        self.actionImportGroupMapping.triggered.connect(self.on_import_group_mapping_triggered)
        self.actionCurrentParameters.triggered.connect(self.on_current_parameters_triggered)
        self.actionPreferences.triggered.connect(self.on_preferences_triggered)
        self.actionResetLayout.triggered.connect(self.reset_layout)
        self.actionOpenUserFolder.triggered.connect(self.on_open_user_folder_triggered)
        self.actionZoomIn.triggered.connect(lambda: self.current_view.scaleView(1.2)
                                            if self.current_view is not None else None)
        self.actionZoomOut.triggered.connect(lambda: self.current_view.scaleView(1 / 1.2)
                                             if self.current_view is not None else None)
        self.actionZoomToFit.triggered.connect(lambda: self.current_view.zoomToFit()
                                               if self.current_view is not None else None)
        self.actionZoomSelectedRegion.triggered.connect(
            lambda: self.current_view.fitInView(self.current_view.scene().selectedNodesBoundingRect(),
                                                Qt.KeepAspectRatio)
            if self.current_view is not None else None)
        self.search_widget.leSearch.textChanged.connect(self.on_do_search)
        self.search_widget.leSearch.returnPressed.connect(self.on_do_search)
        self.actionNewProject.triggered.connect(self.on_new_project_triggered)
        self.actionOpen.triggered.connect(self.on_open_project_triggered)
        self.actionSave.triggered.connect(self.on_save_project_triggered)
        self.actionSaveAs.triggered.connect(self.on_save_project_as_triggered)

        self.actionViewMiniMap.triggered.connect(self.on_switch_minimap_visibility)
        qApp.focusChanged.connect(self.on_focus_changed)
        self.actionViewSpectrum.triggered.connect(lambda: self.on_show_spectrum_triggered('show'))
        self.actionViewCompareSpectrum.triggered.connect(lambda: self.on_show_spectrum_triggered('compare'))

        self.actionFullScreen.triggered.connect(self.on_full_screen_triggered)
        self.actionHideSelected.triggered.connect(lambda: self.current_view.scene().hideSelectedItems()
                                                  if self.current_view is not None else None)
        self.actionShowAll.triggered.connect(lambda: self.current_view.scene().showAllItems()
                                             if self.current_view is not None else None)
        self.actionHideIsolatedNodes.triggered.connect(lambda x: [d.widget().show_isolated_nodes(x)
                                                                  for d in self.network_docks.values()])
        color_button.colorSelected.connect(self.on_set_selected_nodes_color)
        color_button.colorReset.connect(self.on_reset_selected_nodes_color)
        size_combo.currentIndexChanged['QString'].connect(self.on_set_selected_nodes_size)
        size_action.triggered.connect(lambda: self.on_set_selected_nodes_size(size_combo.currentText()))
        self.actionNeighbors.triggered.connect(
            lambda: self.on_select_first_neighbors_triggered(self.current_view.scene().selectedNodes())
            if self.current_view is not None else None)
        self.actionSetPieChartsVisibility.toggled.connect(self.on_set_pie_charts_visibility_toggled)
        self.actionExportToCytoscape.triggered.connect(self.on_export_to_cytoscape_triggered)
        self.actionExportAsImage.triggered.connect(lambda: self.on_export_as_image_triggered('full'))
        self.actionExportCurrentViewAsImage.triggered.connect(lambda: self.on_export_as_image_triggered('current'))
        self.actionExportMetadata.triggered.connect(self.on_export_metadata)
        self.actionExportDatabaseResults.triggered.connect(self.on_export_db_results)

        self.actionDownloadDatabases.triggered.connect(self.on_download_databases_triggered)
        self.actionImportUserDatabase.triggered.connect(self.on_import_user_database_triggered)
        self.actionViewDatabases.triggered.connect(self.on_view_databases_triggered)

        self.dock_nodes.visibilityChanged.connect(lambda v: self.update_search_menu(self.tvNodes) if v else None)
        self.dock_edges.visibilityChanged.connect(lambda v: self.update_search_menu(self.tvEdges) if v else None)
        self.dock_spectra.visibilityChanged.connect(lambda v: self.update_search_menu(self.tvNodes) if v else None)

        self.tvNodes.viewDetailsClicked.connect(self.on_view_details_clicked)
        self.tvNodes.model().dataChanged.connect(self.on_nodes_table_data_changed)

        # Add a menu to show/hide toolbars
        popup_menu = self.createPopupMenu()
        popup_menu.setTitle("Toolbars")
        self.menuView.addMenu(popup_menu)

        # Populate list of recently opened projects
        menu = QMenu()
        self.recent_projects = []

        self.actionRecentProjects.setMenu(menu)
        for i in range(10):
            action = QAction(self)
            action.setVisible(False)
            action.triggered.connect(self.on_open_recent_project_triggered)
            menu.addAction(action)
        menu.addSeparator()
        action = QAction("&Clear menu", self)
        action.triggered.connect(lambda: self.update_recent_projects(clear=True))
        menu.addAction(action)

        # Build research bar
        self._last_table = self.tvNodes
        self.update_search_menu()

    # noinspection PyAttributeOutsideInit
    @debug
    def add_docks(self):
        self.dock_manager = CDockManager(self)
        self.dock_manager.setViewMenuInsertionOrder(CDockManager.MenuSortedByInsertion)
        self.dock_manager.viewMenu().setTitle("Data")
        self.setDockOptions(QMainWindow.AllowTabbedDocks)

        self.dock_placeholder = CDockWidget("Placeholder")
        self.dock_placeholder.setObjectName("placeholder")
        self.dock_manager.addDockWidget(TopDockWidgetArea, self.dock_placeholder)
        self.dock_placeholder.toggleView(False)

        if config.EMBED_JUPYTER:
            try:
                self.jupyter_widget = ui.widgets.JupyterWidget()
            except AttributeError:
                pass
            else:
                dock = CDockWidget("Jupyter Console")
                dock.setObjectName("jupyter")
                dock.setIcon(QIcon(":/icons/images/python.svg"))
                dock.setWidget(self.jupyter_widget)
                self.jupyter_widget.push(app=qApp, win=self)
                self.dock_manager.addDockWidget(TopDockWidgetArea, dock)
                self.dock_manager.addToggleViewActionToMenu(dock.toggleViewAction())

        self.dock_nodes = CDockWidget("Nodes")
        self.dock_nodes.setObjectName("0nodes")
        self.dock_nodes.setIcon(QIcon(":/icons/images/node.svg"))
        self.nodes_widget = ui.widgets.NodesWidget()
        self.tvNodes = self.nodes_widget.tvNodes
        self.dock_nodes.setWidget(self.nodes_widget)
        dock_area = self.dock_manager.addDockWidget(BottomDockWidgetArea, self.dock_nodes)
        self.dock_manager.addToggleViewActionToMenu(self.dock_nodes.toggleViewAction())
        self.dock_nodes.toggleView(False)

        self.dock_edges = CDockWidget("Edges")
        self.dock_edges.setObjectName("1edges")
        self.dock_edges.setIcon(QIcon(":/icons/images/edge.svg"))
        self.edges_widget = ui.widgets.EdgesWidget()
        self.tvEdges = self.edges_widget.tvEdges
        self.dock_edges.setWidget(self.edges_widget)
        self.dock_manager.addDockWidget(CenterDockWidgetArea, self.dock_edges, dock_area)
        self.dock_manager.addToggleViewActionToMenu(self.dock_edges.toggleViewAction())
        self.dock_edges.toggleView(False)

        self.dock_spectra = CDockWidget("Spectra")
        self.dock_spectra.setObjectName("2spectra")
        self.dock_spectra.setIcon(QIcon(":/icons/images/spectrum.svg"))
        self.spectra_widget = ui.widgets.spectrum.ExtendedSpectrumWidget()
        self.dock_spectra.setWidget(self.spectra_widget)
        self.dock_manager.addDockWidget(CenterDockWidgetArea, self.dock_spectra, dock_area)
        self.dock_manager.addToggleViewActionToMenu(self.dock_spectra.toggleViewAction())
        self.dock_spectra.toggleView(False)

        self.dock_manager.viewMenu().addSeparator()
        self.menuView.addMenu(self.dock_manager.viewMenu())
        dock_area.setCurrentIndex(0)

    @debug
    def init_project(self):
        # Create an object to store all computed objects
        self.network = Network()

        # Create graph
        self._network.graph = ig.Graph()

        # Create options dict
        self._network.options = utils.AttrDict()

        for dock in self.network_docks.values():
            self.dock_manager.viewMenu().removeAction(dock.toggleViewAction())
        self.network_docks = {}

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
        docks = list(self.network_docks.values())
        for dock in docks:
            view = dock.widget().gvNetwork
            if view.hasFocus():
                return view

        try:
            return docks[0].widget().gvNetwork
        except IndexError:
            return

    @property
    def network(self):
        return self._network

    @network.setter
    def network(self, network):
        network.infosAboutToChange.connect(self.tvNodes.model().sourceModel().beginResetModel)
        network.infosChanged.connect(self.tvNodes.model().sourceModel().endResetModel)
        network.interactionsAboutToChange.connect(self.tvEdges.model().sourceModel().beginResetModel)
        network.interactionsChanged.connect(self.tvEdges.model().sourceModel().endResetModel)

        self.tvNodes.setColumnHidden(1, network.db_results is None or len(network.db_results) == 0)

        self._network = network

    @property
    def style(self):
        return self._style

    @style.setter
    def style(self, style):
        self._style = style
        for dock in self.network_docks.values():
            dock.widget().set_style(style)

    @property
    def network_docks(self):
        return self._network_docks

    @network_docks.setter
    def network_docks(self, docks):
        for dock in self.network_docks.values():
            self.menuView.removeAction(dock.toggleViewAction())

        self._network_docks = docks

        for dock in docks:
            self.menuView.addAction(dock.toggleViewAction())

    @debug
    def nodes_selection(self):
        selected_indexes = self.tvNodes.model().mapSelectionToSource(
            self.tvNodes.selectionModel().selection()).indexes()
        return {index.row() for index in selected_indexes}

    @debug
    def edges_selection(self):
        selected_indexes = self.tvEdges.model().mapSelectionToSource(
            self.tvEdges.selectionModel().selection()).indexes()
        return {index.row() for index in selected_indexes}

    @debug
    def load_project(self, filename):
        def create_draw_workers(worker: workers.LoadProjectWorker):
            self.reset_project()

            self.tvNodes.model().setSelection([])
            self.tvEdges.model().setSelection([])
            self.tvNodes.model().sourceModel().beginResetModel()
            self.tvEdges.model().sourceModel().beginResetModel()
            self.network, layouts = worker.result()
            self.tvNodes.model().sourceModel().endResetModel()
            self.tvEdges.model().sourceModel().endResetModel()
            self.dock_edges.toggleView(True)
            self.dock_nodes.toggleView(True)

            workers = []
            for name, value in layouts.items():
                try:
                    widget_class = ui.widgets.AVAILABLE_NETWORK_WIDGETS[name]
                except KeyError:
                    pass
                else:
                    widget = self.add_network_widget(widget_class)
                    if widget is not None:
                        layout = value.get('layout')
                        self.apply_layout(widget, layout, value.get('isolated_nodes'))
                        if layout is not None:
                            colors = value.get('colors', {})
                            colors = [QColor(colors.get(str(i), '')) for i in range(layout.shape[0])]
                        else:
                            colors = []
                        worker = widget.create_draw_worker(compute_layouts=False,
                                                           colors=colors,
                                                           radii=value.get('radii', []))
                        workers.append(worker)

            if workers:
                return workers

        def save_filename(*args):
            # Save filename and set window title
            self.fname = filename
            self.has_unsaved_changes = False

        worker = self.prepare_load_project_worker(filename)
        if worker is not None:
            self._workers.append(worker)
            self._workers.append(create_draw_workers)
            self._workers.append(lambda _: self.update_columns_mappings())
            self._workers.append(save_filename)
            self._workers.append(lambda _: self.update_recent_projects(filename))  # Update list of recent projects
            self._workers.start()

    @debug
    def save_project(self, filename):
        worker = self.prepare_save_project_worker(filename)
        if worker is not None:
            self._workers.append(worker)
            self._workers.start()

    @debug
    def reset_project(self):
        self.fname = None
        self.has_unsaved_changes = False
        try:
            self.network.spectra.close()
        except AttributeError:
            pass

        for dock in self.network_docks.values():
            self.dock_manager.removeDockWidget(dock)

        self.tvNodes.model().sourceModel().beginResetModel()
        self.tvEdges.model().sourceModel().beginResetModel()
        self.init_project()
        self.tvNodes.model().sourceModel().endResetModel()
        self.tvEdges.model().sourceModel().endResetModel()
        self.spectra_widget.set_spectrum1(None)
        self.spectra_widget.set_spectrum2(None)
        self.update_search_menu()

    @debug
    def update_search_menu(self, table: QTableView = None):
        if table is None:
            table = self._last_table

        model = table.model()

        menu = QMenu(self)
        group = QActionGroup(menu, exclusive=True)

        for index in range(model.columnCount() + 1):
            text = "All" if index == 0 else model.headerData(index - 1, Qt.Horizontal, Qt.DisplayRole)
            action = group.addAction(QAction(str(text), checkable=True))
            action.setData(index)
            menu.addAction(action)
            if index == 0:
                action.setChecked(True)
                menu.addSeparator()

        self.search_widget.btSearch.setMenu(menu)
        group.triggered.connect(lambda act: table.model().setFilterKeyColumn(act.data() - 1))
        model.setFilterKeyColumn(-1)

        self._last_table = table

    def update_recent_projects(self, add_fname=None, remove_fname=None, clear=False):
        if clear:
            self.recent_projects = []
        elif remove_fname is not None:
            try:
                self.recent_projects.remove(remove_fname)
            except ValueError:
                pass

        if add_fname is not None:
            try:
                self.recent_projects.remove(add_fname)
            except ValueError:
                pass
            self.recent_projects.insert(0, add_fname)

        self.recent_projects = self.recent_projects[:10]

        actions = self.actionRecentProjects.menu().actions()
        for i, act in enumerate(actions):
            if act.isSeparator():
                break

            try:
                fname = self.recent_projects[i]
                act.setText(f"{i + 1} | {fname}")
                act.setData(fname)
                act.setVisible(True)
            except IndexError:
                act.setVisible(False)

    def keyPressEvent(self, event: QKeyEvent):
        widget = QApplication.focusWidget()

        if event.matches(QKeySequence.NextChild):
            # Navigate between GraphicsViews
            docks = list(self.network_docks.values())
            current_index = -1
            for i, dock in enumerate(docks):
                view = dock.widget().gvNetwork
                if view.hasFocus():
                    current_index = i
                elif current_index >= 0:
                    try:
                        next_dock = docks[current_index + 1]
                        if next_dock.isVisible():
                            next_dock.widget().gvNetwork.setFocus(Qt.TabFocusReason)
                            break
                    except IndexError:
                        pass

            if current_index == -1 or current_index == len(docks) - 1:
                try:
                    docks[0].widget().gvNetwork.setFocus(Qt.TabFocusReason)
                except IndexError:
                    pass

        elif widget is not None:
            if isinstance(widget, QGraphicsView):
                # Copy image to clipboard
                event_without_shift = QKeyEvent(event.type(), event.key(), event.modifiers() ^ Qt.ShiftModifier)
                if event.matches(QKeySequence.Copy) or event_without_shift.matches(QKeySequence.Copy):
                    type_ = 'full' if event.modifiers() & Qt.ShiftModifier else 'current'
                    self.on_export_as_image_triggered(type_, to_clipboard=True)
            elif isinstance(widget, QTableView) and event.matches(QKeySequence.Copy):
                # Copy data to clipboard
                selection = widget.selectedIndexes()
                if selection is not None:
                    rows = sorted(index.row() for index in selection)
                    first_row = rows[0]
                    columns = sorted(index.column() for index in selection)
                    first_column = columns[0]
                    rowcount = rows[-1] - first_row + 1
                    colcount = columns[-1] - first_column + 1
                    selected_columns = widget.selectionModel().selectedColumns()
                    add_header = len(selected_columns) > 0

                    if add_header:
                        rowcount += 1

                    table = [[''] * colcount for _ in range(rowcount)]

                    if add_header:
                        table[0] = [widget.model().headerData(c.column(), Qt.Horizontal) for c in selected_columns]

                    for index in selection:
                        row = index.row() - first_row + add_header
                        column = index.column() - first_column
                        table[row][column] = index.data()

                    stream = io.StringIO()
                    csv.writer(stream, delimiter='\t').writerows(table)
                    QApplication.clipboard().setText(stream.getvalue())

    def showEvent(self, event):
        super().showEvent(event)
        if not hasattr(self, '_first_show'):
            self.load_settings()
            self._default_state = self.dock_manager.saveState()
            self._first_show = False

    def closeEvent(self, event):
        if not config.get_debug_flag():
            reply = self.confirm_save_changes()
            if reply == QMessageBox.Cancel:
                event.ignore()
                return

        if not config.get_debug_flag() and self._workers:
            reply = QMessageBox.question(self, None,
                                         "There is process running. Do you really want to exit?",
                                         QMessageBox.Close | QMessageBox.Cancel)
        else:
            reply = QMessageBox.Close

        if reply == QMessageBox.Close:
            event.accept()
            self.save_settings()
        else:
            event.ignore()

    # noinspection PyUnusedLocal
    @debug
    def on_focus_changed(self, old: QWidget, now: QWidget):
        if hasattr(now, 'name') and now in self.network_docks.values():
            current_view = self.current_view
            if current_view is not None:
                self.actionViewMiniMap.setChecked(self.current_view.minimap.isVisible())

    @debug
    def on_switch_minimap_visibility(self, *args):
        view = self.current_view
        if view is not None:
            visible = view.minimap.isVisible()
            view.minimap.setVisible(not visible)
            self.actionViewMiniMap.setChecked(not visible)

    @debug
    def on_scene_selection_changed(self, update_view=True):
        current_view = self.current_view
        if current_view is None:
            return

        nodes_idx = [item.index() for item in current_view.scene().selectedNodes()]
        edges_idx = [item.index() for item in current_view.scene().selectedEdges()]
        self.tvNodes.model().setSelection(nodes_idx)
        self.tvEdges.model().setSelection(edges_idx)

        if update_view and self.actionLinkViews.isChecked():
            for dock in self.network_docks.values():
                view = dock.widget().gvNetwork
                if view != current_view:
                    with utils.SignalBlocker(view.scene()):
                        view.scene().setNodesSelection(nodes_idx)

    @debug
    def on_set_selected_nodes_color(self, color: QColor):
        for dock in self.network_docks.values():
            dock.widget().gvNetwork.scene().setSelectedNodesColor(color)

        # try:
        #     self.network.graph.vs['__color'] = dock.widget().gvNetwork.scene().nodesColors()
        # except UnboundLocalError:
        #     pass

        self.has_unsaved_changes = True

    @debug
    def on_reset_selected_nodes_color(self):
        for dock in self.network_docks.values():
            scene = dock.widget().gvNetwork.scene()
            scene.setSelectedNodesColor(scene.networkStyle().nodeBrush().color())

        # try:
        #     self.network.graph.vs['__color'] = dock.widget().gvNetwork.scene().nodesColors()
        # except UnboundLocalError:
        #     pass

        self.has_unsaved_changes = True

    @debug
    def on_set_selected_nodes_size(self, text: str):
        try:
            size = int(text)
        except ValueError:
            return

        for dock in self.network_docks.values():
            dock.widget().gvNetwork.scene().setSelectedNodesRadius(size)

        # try:
            # self.network.graph.vs['__size'] = dock.widget().scene().nodesRadii()
        # except UnboundLocalError:
        #     pass

        self.has_unsaved_changes = True

    @debug
    def on_do_search(self, *args):
        if self._last_table is None:
            return
        self._last_table.model().setFilterRegExp(str(self.search_widget.leSearch.text()))

    @debug
    def on_new_project_triggered(self, *args):
        reply = self.confirm_save_changes()

        if reply != QMessageBox.Cancel:
            self.reset_project()

        return reply

    @debug
    def on_open_recent_project_triggered(self, *args):
        action = self.sender()
        if action is not None:
            self.load_project(action.data())

    @debug
    def on_open_project_triggered(self, *args):
        reply = self.confirm_save_changes()
        if reply == QMessageBox.Cancel:
            return

        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.ExistingFile)
        dialog.setNameFilters([f"{QCoreApplication.applicationName()} Files (*{config.FILE_EXTENSION})",
                               "All files (*.*)"])
        if dialog.exec_() == QDialog.Accepted:
            filename = dialog.selectedFiles()[0]
            self.load_project(filename)

    @debug
    def on_save_project_triggered(self, *args):
        if self.fname is None:
            self.on_save_project_as_triggered()
        else:
            self.save_project(self.fname)

    @debug
    def on_save_project_as_triggered(self, *args):
        dialog = QFileDialog(self)
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        dialog.setNameFilters([f"{QCoreApplication.applicationName()} Files (*{config.FILE_EXTENSION})",
                               "All files (*.*)"])
        if dialog.exec_() == QDialog.Accepted:
            filename = dialog.selectedFiles()[0]
            self.save_project(filename)

    @debug
    def on_set_pie_charts_visibility_toggled(self, visibility):
        for dock in self.network_docks.values():
            view = dock.widget().gvNetwork
            scene = view.scene()
            scene.setPieChartsVisibility(visibility)
            view.updateVisibleItems()

    @debug
    def on_export_to_cytoscape_triggered(self, *args):
        try:
            from py2cytoscape.data.cyrest_client import CyRestClient
            from py2cytoscape import cyrest

            view = self.current_view
            if view is None:
                return

            cy = CyRestClient()

            self._logger.debug('Creating exportable copy of the graph object')
            g = self.network.graph.copy()

            try:
                g.es['cosine'] = g.es['__weight']
                g.es['interaction'] = 'interacts with'
                g.es['name'] = [f"{e.source} (interacts with) {e.target}" for e in g.es]
            except KeyError:
                pass

            for attr in g.vs.attributes():
                if attr.startswith('__'):
                    del g.vs[attr]
                else:
                    g.vs[attr] = [str(x + 1) for x in g.vs[attr]]

            g = view.process_graph_before_export(g)

            # cy.session.delete()
            self._logger.debug('CyREST: Creating network')
            g_cy = cy.network.create_from_igraph(g)

            self._logger.debug('CyREST: Set layout')
            layout = np.empty((g.vcount(), 2))
            for item in view.scene().nodes():
                layout[item.index()] = (item.x(), item.y())
            positions = [(suid, x, y) for suid, (x, y) in zip(g_cy.get_nodes()[::-1], layout)]
            cy.layout.apply_from_presets(network=g_cy, positions=positions)

            self._logger.debug('CyREST: Set style')
            style_js = style_to_cytoscape(view.scene().networkStyle())
            style = cy.style.create(style_js['title'], style_js)
            cy.style.apply(style, g_cy)

            # Fit view to content
            cyrest.cyclient().view.fit_content()
        except (ConnectionRefusedError, requests.ConnectionError):
            QMessageBox.information(self, None,
                                    'Please launch Cytoscape before trying to export.')
            self._logger.error('Cytoscape was not launched.')
        except json.decoder.JSONDecodeError:
            QMessageBox.information(self, None,
                                    'Cytoscape was not ready to receive data. Please try again.')
            self._logger.error('Cytoscape was not ready to receive data.')
        except ImportError:
            QMessageBox.information(self, None,
                                    ('py2tocytoscape is required for this action '
                                     'https://pypi.python.org/pypi/py2cytoscape).'))
            self._logger.error('py2cytoscape not found.')
        except requests.exceptions.HTTPError as e:
            QMessageBox.warning(self, None, 'The following error occurred during export to Cytoscape: {str(e)}')
            e.strerror
            self._logger.error(f'py2cytoscape HTTPError: {str(e)}')

    @debug
    def on_export_as_image_triggered(self, type_, to_clipboard=False):
        view = self.current_view
        if view is None:
            return

        if to_clipboard:
            filename = '__clipboard__'
            filter_ = ''
        else:
            filter_ = ["PNG - Portable Network Graphics (*.png)",
                       "JPEG - Joint Photographic Experts Group (*.jpeg)",
                       "SVG - Scalable Vector Graphics (*.svg)",
                       "BMP - Windows Bitmap (*.bmp)"]
            if type_ == 'current':
                filter_.remove("SVG - Scalable Vector Graphics (*.svg)")

            filename, filter_ = QFileDialog.getSaveFileName(self, "Save image",
                                                            filter=";;".join(filter_))

        if filename:
            if filter_.endswith("(*.svg)"):
                try:
                    from PyQt5.QtSvg import QSvgGenerator
                except ImportError:
                    QMessageBox.warning(self, None, 'QtSvg was not found on your system. It is needed for SVG export.')
                else:
                    svg_gen = QSvgGenerator()

                    svg_gen.setFileName(filename)
                    rect = view.scene().sceneRect()
                    svg_gen.setViewBox(rect)
                    svg_gen.setSize(rect.size().toSize())
                    svg_gen.setTitle("SVG Generator Example Drawing")
                    svg_gen.setDescription("An SVG drawing created by the SVG Generator.")

                    painter = QPainter(svg_gen)
                    view.scene().render(painter, target=rect)
                    painter.end()
            else:
                use_transparency = filter_.endswith('(*.png)')
                rect = view.viewport().rect() if type_ == 'current' else view.scene().sceneRect().toRect()
                fmt = QImage.Format_ARGB32 if use_transparency else QImage.Format_RGB32
                size = rect.size() * 4 if type_ == 'current' else rect.size()
                image = QImage(size, fmt)
                image.fill(Qt.transparent) if use_transparency else image.fill(Qt.white)
                painter = QPainter(image)
                painter.setRenderHint(QPainter.Antialiasing)
                view.render(painter, source=rect) if type_ == 'current' else view.scene().render(painter)

                if to_clipboard:
                    QApplication.clipboard().setImage(image)
                else:
                    image.save(filename)

    @debug
    def on_export_metadata(self, *args):
        filter_ = ["CSV - Comma Separated Values (*.csv)",
                   "TSV - Tab Separated Values (*.tsv)"]

        filename, filter_ = QFileDialog.getSaveFileName(self, "Export metadata",
                                                        filter=";;".join(filter_))

        if filename:
            sep = '\t' if filter_.endswith("(*.tsv)") else ','

            worker = self.prepare_export_metadata_worker(filename, self.tvNodes.model().sourceModel(), sep)
            if worker is not None:
                self._workers.append(worker)
                self._workers.start()

    @debug
    def on_export_db_results(self, *args):
        filter_ = ["YAML - YAML Ain't Markup Language (*.yaml)",
                   "JSON - JavaScript Notation Object (*.json)"]

        filename, filter_ = QFileDialog.getSaveFileName(self, "Export Database Results",
                                                        filter=";;".join(filter_))

        if filename:
            fmt = 'json' if filter_.endswith("(*.json)") else 'yaml'
            worker = self.prepare_export_db_results_worker(filename, self.tvNodes.model().sourceModel(), fmt=fmt)
            if worker is not None:
                self._workers.append(worker)
                self._workers.start()

    @debug
    def on_show_spectrum_from_table_triggered(self, type_):
        model = self.tvNodes.model()
        selected_indexes = model.mapSelectionToSource(
            self.tvNodes.selectionModel().selection()).indexes()

        if not selected_indexes:
            return

        try:
            node_idx = model.mapToSource(selected_indexes[0]).row()
        except IndexError:
            pass
        else:
            self.on_show_spectrum_triggered(type_, node_idx=node_idx)

    @debug
    def on_show_spectrum_triggered(self, type_, node=None, node_idx=None):
        if getattr(self.network, 'spectra', None) is not None:
            try:
                if node_idx is None:
                    if node is None:
                        # No node specified, try to get it from current view's selection
                        view = self.current_view
                        if view is None:
                            return
                        node = view.scene().selectedNodes()[0]
                    node_idx = node.index()

                data = human_readable_data(self.network.spectra[node_idx])

                if self.network.mzs:
                    mz_parent = self.network.mzs[node_idx]
                else:
                    mz_parent = None
            except IndexError:
                pass
            except KeyError:
                QMessageBox.warning(self, None, 'Selected spectrum does not exists.')
            else:
                # Set data as first or second spectrum
                if type_ == 'compare':
                    score = self.network.scores[self.spectra_widget.spectrum1_index, node_idx] \
                        if self.spectra_widget.spectrum1_index is not None else None
                    set_spectrum = self.spectra_widget.set_spectrum2
                else:
                    score = self.network.scores[node_idx, self.spectra_widget.spectrum2_index] \
                        if self.spectra_widget.spectrum2_index is not None else None
                    set_spectrum = self.spectra_widget.set_spectrum1
                if score is not None:
                    self.spectra_widget.set_title(f'Score: {score:.4f}')
                set_spectrum(data, node_idx, mz_parent)

                # Show spectrum tab
                self.dock_spectra.dockAreaWidget().setCurrentDockWidget(self.dock_spectra)

    @debug
    def on_select_first_neighbors_triggered(self, nodes, *args):
        view = self.current_view
        if view is not None:
            neighbors = [v.index for node in nodes for v in self.network.graph.vs[node.index()].neighbors()]
            view.scene().setNodesSelection(neighbors)

    @debug
    def on_use_columns_for(self, type_):
        if self.tvNodes.model().columnCount() <= 1:
            return

        selected_columns_indexes = self.tvNodes.selectionModel().selectedColumns(0)
        len_ = len(selected_columns_indexes)

        if type_ == COLUMN_MAPPING_LABELS:
            if len_ == 0:
                return
            elif len_ > 1:
                QMessageBox.information(self, None, "Please select only one column.")
            else:
                id_ = selected_columns_indexes[0].column()
                self.set_nodes_label(id_)
                self.has_unsaved_changes = True
        elif type_ == COLUMN_MAPPING_PIE_CHARTS:
            dialog = ui.PieColorMappingDialog(self.tvNodes.model(), selected_columns_indexes)
            if dialog.exec_() == QDialog.Accepted:
                columns, colors = dialog.getValues()
                self.set_nodes_pie_chart_values(columns, colors)
                self.has_unsaved_changes = True
        elif type_ == COLUMN_MAPPING_NODES_SIZES:
            if len_ > 1:
                QMessageBox.information(self, None, "Please select only one column.")
            else:
                id_ = selected_columns_indexes[0].column() if len_ > 0 else -1
                dialog = ui.SizeMappingDialog(self.tvNodes.model(), id_)
                if dialog.exec_() == QDialog.Accepted:
                    id_, func = dialog.getValues()
                    if id_ > 0:
                        self.set_nodes_sizes_values(id_, func)
                    self.has_unsaved_changes = True
        elif type_ == COLUMN_MAPPING_NODES_COLORS:
            if len_ > 1:
                QMessageBox.information(self, None, "Please select only one column.")
            else:
                id_ = selected_columns_indexes[0].column() if len_ > 0 else -1
                column_title = self.tvNodes.model().headerData(id_, Qt.Horizontal)
                try:
                    data = self._network.infos[column_title]
                except IndexError:
                    pass
                else:
                    dialog = ui.ColorMappingDialog(self.tvNodes.model(), id_, data)
                    if dialog.exec_() == QDialog.Accepted:
                        id_, mapping = dialog.getValues()
                        if id_ > 0:
                            self.set_nodes_colors_values(id_, mapping)
                        self.has_unsaved_changes = True

    @debug
    def on_show_spectrum(self, *args):
        indexes = self.tvNodes.selectedIndexes()
        if not indexes:
            return

    @debug
    def on_nodes_table_data_changed(self, *args):
        self.has_unsaved_changes = True

    @debug
    def on_query_databases(self, type_='standards'):
        selected_idx = self.nodes_selection()
        if not selected_idx:
            return
        options = workers.QueryDatabasesOptions()
        options.analog_search = (type_ == 'analogs')

        try:
            dialog = ui.QueryDatabasesDialog(self, options=options)
            if dialog.exec_() == QDialog.Accepted:
                options = dialog.getValues()
                worker = self.prepare_query_database_worker(selected_idx, options)
                if worker is not None:
                    self._workers.append(worker)
                    self._workers.start()
        except FileNotFoundError:
            QMessageBox.warning(self, None, "No database found. Please download at least one database.")

    @debug
    def on_current_parameters_triggered(self, *args):
        if hasattr(self._network.options, 'cosine'):
            dialog = ui.CurrentParametersDialog(self, options=self.network.options)
            dialog.exec_()

    @debug
    def on_preferences_triggered(self, *args):
        dialog = ui.SettingsDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.style = dialog.getValues()

    @debug
    def on_open_user_folder_triggered(self, *args):
        if sys.platform.startswith('win'):
            os.startfile(config.USER_PATH)
        elif sys.platform.startswith('darwin'):
            subprocess.Popen(["open", config.USER_PATH])
        else:
            subprocess.Popen(["xdg-open", config.USER_PATH])

    @debug
    def on_full_screen_triggered(self, *args):
        if not self.isFullScreen():
            self.setWindowFlags(Qt.Window)
            self.showFullScreen()
        else:
            self.setWindowFlags(Qt.Widget)
            self.showNormal()

    @debug
    def on_process_file_triggered(self, *args):
        reply = self.confirm_save_changes()
        if reply == QMessageBox.Cancel:
            return

        dialog = ui.ProcessDataDialog(self, options=self.network.options)
        if dialog.exec_() == QDialog.Accepted:
            def create_compute_scores_worker(worker: workers.ReadDataWorker):
                self.tvNodes.model().setSelection([])
                self.tvNodes.model().sourceModel().beginResetModel()
                self.network.mzs, self.network.spectra = worker.result()
                self.tvNodes.model().sourceModel().endResetModel()
                mzs = self.network.mzs
                if not mzs:
                    mzs = np.zeros((len(self.network.spectra),), dtype=int)
                return self.prepare_compute_scores_worker(mzs, self.network.spectra)

            def store_scores(worker: workers.ComputeScoresWorker):
                self.tvEdges.model().setSelection([])
                scores = worker.result()
                if not isinstance(scores, np.ndarray):
                    return
                self.tvEdges.model().sourceModel().beginResetModel()
                self._network.scores = scores
                self._network.interactions = None
                self.tvEdges.model().sourceModel().endResetModel()

                self.dock_edges.toggleView(True)
                self.dock_nodes.toggleView(True)

            def add_graph_vertices(*args):
                nodes_idx = np.arange(self._network.scores.shape[0])
                self._network.graph.add_vertices(nodes_idx.tolist())

            self.reset_project()

            process_file, use_metadata, metadata_file, metadata_options, options, views = dialog.getValues()

            self._network.options = options
            self._workers.append(self.prepare_read_data_worker(process_file))
            self._workers.append(create_compute_scores_worker)
            self._workers.append(store_scores)
            self._workers.append(add_graph_vertices)
            if use_metadata:
                self._workers.append(self.prepare_read_metadata_worker(metadata_file, metadata_options))
            if 'network' in views:
                self._workers.append(lambda _: self.prepare_generate_network_worker())

            for name in views:
                try:
                    widget_class = ui.widgets.AVAILABLE_NETWORK_WIDGETS[name]
                except KeyError:
                    pass
                else:
                    if widget_class is not None:
                        widget = self.add_network_widget(widget_class)
                        if widget is not None:
                            self._workers.append(lambda _, w=widget: w.create_draw_worker())

            self._workers.start()

    @debug
    def on_import_metadata_triggered(self, *args):
        dialog = ui.ImportMetadataDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            metadata_filename, options = dialog.getValues()
            worker = self.prepare_read_metadata_worker(metadata_filename, options)
            if worker is not None:
                self._workers.append(worker)
                self._workers.start()

    @debug
    def on_import_group_mapping_triggered(self, *args):
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.ExistingFile)
        dialog.setNameFilters(["Text Files (*.txt; *.csv; *.tsv)", "All files (*.*)"])
        if dialog.exec_() == QDialog.Accepted:
            filename = dialog.selectedFiles()[0]
            worker = self.prepare_read_group_mapping_worker(filename)
            if worker is not None:
                self._workers.append(worker)
                self._workers.start()

    @debug
    def on_add_view_triggered(self, *args):
        if hasattr(self._network, 'graph') and hasattr(self._network, 'scores'):
            action = self.sender()
            widget_class = action.data()
            if widget_class is not None:
                options = self.network.options.get(widget_class.name, {})
                dialog = widget_class.dialog_class(self, options=options)
                if dialog.exec_() == QDialog.Accepted:
                    options = dialog.getValues()
                    widget = self.add_network_widget(widget_class)
                    self.network.options[widget.name] = options

                    if widget is not None:
                        if widget.name == 'network':
                            self._workers.append(lambda _: self.prepare_generate_network_worker())
                        self._workers.append(widget.create_draw_worker)
                        self._workers.start()

    @debug
    def on_edit_options_triggered(self, widget):
        if hasattr(self.network, 'scores'):
            options = self.network.options.get(widget.name, {})
            dialog = widget.dialog_class(self, options=options)
            if dialog.exec_() == QDialog.Accepted:
                new_options = dialog.getValues()
                if new_options != options:
                    self.network.options[widget.name] = new_options

                    self.has_unsaved_changes = True

                    widget.reset_layout()
                    if widget.name == 'network':
                        self._network.interactions = None
                        self._workers.append(lambda _: self.prepare_generate_network_worker(keep_vertices=True))
                    self._workers.append(widget.create_draw_worker)
                    self._workers.start()
                    self.update_search_menu()
        else:
            QMessageBox.information(self, None, "No network found, please open a file first.")

    @debug
    def on_download_databases_triggered(self, *args):
        dialog = ui.DownloadDatabasesDialog(self, base_path=config.DATABASES_PATH)
        dialog.exec_()

    @debug
    def on_import_user_database_triggered(self, *args):
        dialog = ui.ImportUserDatabaseDialog(self, base_path=config.DATABASES_PATH)
        dialog.exec_()

    @debug
    def on_view_databases_triggered(self, *args):
        path = config.SQL_PATH
        if os.path.exists(path) and os.path.isfile(path) and os.path.getsize(path) > 0:
            dialog = ui.ViewDatabasesDialog(self, base_path=config.DATABASES_PATH)
            dialog.exec_()
        else:
            QMessageBox.information(self, None, "No databases found, please download one or more database first.")

    @debug
    def on_view_details_clicked(self, row: int, selection: dict):
        if selection:
            path = config.SQL_PATH
            if os.path.exists(path) and os.path.isfile(path) and os.path.getsize(path) > 0:
                spectrum = human_readable_data(self.network.spectra[row])
                dialog = ui.ViewStandardsResultsDialog(self, spectrum=spectrum,
                                                       selection=selection, base_path=config.DATABASES_PATH)
                if dialog.exec_() == QDialog.Accepted:
                    current = dialog.getValues()
                    if current is not None:
                        self.network.db_results[row]['current'] = current
                        self.has_unsaved_changes = True
            else:
                QMessageBox.information(self, None, "No databases found, please download one or more database first.")

    @debug
    def confirm_save_changes(self):
        reply = QMessageBox.Yes
        if self.has_unsaved_changes:
            if self.fname is not None:
                message = f"There is unsaved changes in {self.fname}. Would you like to save them?"
            else:
                message = f"Current work has not been saved. Would you like to save now?"
            reply = QMessageBox.question(self, QCoreApplication.applicationName(),
                                         message, QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)

            if reply == QMessageBox.Yes:
                self.on_save_project_triggered()

        return reply

    @debug
    def highlight_selected_nodes(self, *args):
        selected = self.nodes_selection()
        for dock in self.network_docks.values():
            scene = dock.widget().gvNetwork.scene()
            with utils.SignalBlocker(scene):
                scene.setNodesSelection(selected)

    @debug
    def highlight_selected_edges(self, *args):
        selected = self.edges_selection()
        for dock in self.network_docks.values():
            scene = dock.widget().gvNetwork.scene()
            with utils.SignalBlocker(scene):
                scene.setEdgesSelection(selected)

    @debug
    def highlight_nodes_from_selected_edges(self, *args):
        selected = self.edges_selection()
        model = self.tvEdges.model().sourceModel()
        sel = set()
        for row in selected:
            source = model.index(row, 0).data() - 1
            dest = model.index(row, 1).data() - 1
            sel.add(source)
            sel.add(dest)

        for dock in self.network_docks.values():
            scene = dock.widget().gvNetwork.scene()
            with utils.SignalBlocker(scene):
                scene.setNodesSelection(sel)

    def add_network_widget(self, widget_class):
        try:
            dock = self.network_docks[widget_class.name]
            QMessageBox.warning(self, None, "A network of this type already exists.")
            if dock is not None and dock.isClosed():
                dock.toggleView()
            dock.widget().gvNetwork.setFocus(Qt.ActiveWindowFocusReason)
        except KeyError:
            widget = widget_class(self.network)
            view = widget.gvNetwork
            scene = view.scene()
            scene.setNetworkStyle(self.style)
            scene.selectionChanged.connect(self.on_scene_selection_changed)
            view.focusedIn.connect(lambda: self.on_scene_selection_changed(update_view=False))
            scene.pieChartsVisibilityChanged.connect(
                lambda visibility: self.actionSetPieChartsVisibility.setChecked(visibility))
            widget.btOptions.clicked.connect(lambda: self.on_edit_options_triggered(widget))

            dock = CDockWidget(widget.title)
            dock.setWidget(widget)
            self.dock_manager.addDockWidget(LeftDockWidgetArea, dock, self.dock_placeholder.dockAreaWidget())
            dock.toggleView(False)
            self.dock_placeholder.toggleView(False)
            dock.toggleView(True)
            self.dock_manager.addToggleViewActionToMenu(dock.toggleViewAction())
            self.network_docks[widget_class.name] = dock
            self._default_state = self.dock_manager.saveState()

            return widget

    @debug
    def set_nodes_label(self, column_id):
        model = self.tvNodes.model().sourceModel()
        for column in range(model.columnCount()):
            font = model.headerData(column, Qt.Horizontal, role=Qt.FontRole)
            if font is not None and font.overline():
                model.setHeaderData(column, Qt.Horizontal, None, role=Qt.FontRole)

        if column_id is not None:
            font = model.headerData(column_id, Qt.Horizontal, role=Qt.FontRole)
            font = font if font is not None else QFont()
            font.setOverline(True)
            model.setHeaderData(column_id, Qt.Horizontal, font, role=Qt.FontRole)

            for dock in self.network_docks.values():
                scene = dock.widget().gvNetwork.scene()
                scene.setLabelsFromModel(model, column_id, ui.widgets.LabelRole)
            self.network.columns_mappings['label'] = column_id
        else:
            for dock in self.network_docks.values():
                dock.widget().gvNetwork.scene().resetLabels()

            try:
                del self.network.columns_mappings['label']
            except KeyError:
                pass

        self.has_unsaved_changes = True

    @debug
    def set_nodes_pie_chart_values(self, column_ids, colors: List[QColor] = []):
        model = self.tvNodes.model().sourceModel()
        if column_ids is not None:
            if len(colors) < len(column_ids):
                QMessageBox.critical(self, None, "There is more columns selected than colors available.")
                return

            for column in range(model.columnCount()):
                model.setHeaderData(column, Qt.Horizontal, None, role=ui.widgets.metadata.ColorMarkRole)

            save_colors = []
            for column, color in zip(column_ids, colors):
                color = QColor(color)
                save_colors.append(color)
                model.setHeaderData(column, Qt.Horizontal, color, role=ui.widgets.metadata.ColorMarkRole)

            for dock in self.network_docks.values():
                scene = dock.widget().gvNetwork.scene()
                scene.setPieColors(colors)
                scene.setPieChartsFromModel(model, column_ids)
                scene.setPieChartsVisibility(True)

            self.network.columns_mappings['pies'] = (column_ids, save_colors)
        else:
            for column in range(model.columnCount()):
                model.setHeaderData(column, Qt.Horizontal, None, role=ui.widgets.metadata.ColorMarkRole)

            for dock in self.network_docks.values():
                dock.widget().gvNetwork.scene().resetPieCharts()

            try:
                del self.network.columns_mappings['pies']
            except KeyError:
                pass

        self.has_unsaved_changes = True

    @debug
    def set_nodes_sizes_values(self, column_id, func: Callable = None):
        model = self.tvNodes.model().sourceModel()
        for column in range(model.columnCount()):
            font = model.headerData(column, Qt.Horizontal, role=Qt.FontRole)
            if font is not None and font.underline():
                model.setHeaderData(column, Qt.Horizontal, None, role=Qt.FontRole)

        if column_id is not None:
            font = model.headerData(column_id, Qt.Horizontal, role=Qt.FontRole)
            font = font if font is not None else QFont()
            font.setUnderline(True)
            model.setHeaderData(column_id, Qt.Horizontal, font, role=Qt.FontRole)

            for dock in self.network_docks.values():
                dock.widget().gvNetwork.scene().setNodesRadiiFromModel(model, column_id, Qt.DisplayRole, func)

            self.network.columns_mappings['size'] = (column_id, func)
        else:
            for dock in self.network_docks.values():
                dock.widget().gvNetwork.scene().resetNodesRadii()

            try:
                del self.network.columns_mappings['size']
            except KeyError:
                pass

        self.has_unsaved_changes = True

    @debug
    def set_nodes_colors_values(self, column_id, mapping: Union[Dict[str, QColor], Tuple[List[float], List[QColor]]] = {}):
        model = self.tvNodes.model().sourceModel()
        for column in range(model.columnCount()):
            font = model.headerData(column, Qt.Horizontal, role=Qt.FontRole)
            if font is not None and font.italic():
                model.setHeaderData(column, Qt.Horizontal, None, role=Qt.FontRole)

        if column_id is not None:
            font = model.headerData(column_id, Qt.Horizontal, role=Qt.FontRole)
            font = font if font is not None else QFont()
            font.setItalic(True)
            model.setHeaderData(column_id, Qt.Horizontal, font, role=Qt.FontRole)

            column_title = model.headerData(column_id, Qt.Horizontal)
            try:
                data = self._network.infos[column_title]
            except IndexError:
                pass
            else:
                if isinstance(mapping, dict):
                    color_list = [mapping.get(key, QColor()) for key in data]
                elif isinstance(mapping, tuple):
                    try:
                        bins, colors = mapping
                    except TypeError:
                        return

                    def r(ranges, colors, val):
                        if val == ranges[-1]:
                            return colors[-1]

                        b = bisect.bisect_left(ranges, val)
                        try:
                            return colors[b-1]
                        except IndexError:
                            return QColor()

                    color_list = []
                    for value in data:
                        color_list.append(r(bins, colors, value))
                else:
                    return

                for dock in self.network_docks.values():
                    dock.widget().gvNetwork.scene().setNodesColors(color_list)

                self.network.columns_mappings['colors'] = (column_id, mapping)
        else:
            for dock in self.network_docks.values():
                scene = dock.widget().gvNetwork.scene()
                color = scene.networkStyle().nodeBrush().color()
                scene.setNodesColors([color for _ in scene.nodes()])

            try:
                del self.network.columns_mappings['colors']
            except KeyError:
                pass

        self.has_unsaved_changes = True

    @debug
    def save_settings(self):
        settings = QSettings()

        settings.beginGroup('MainWindow')
        settings.setValue('Geometry', self.saveGeometry())
        settings.setValue('State', self.saveState())
        if self.recent_projects:
            settings.setValue('RecentProjects', self.recent_projects)
        settings.endGroup()

    @debug
    def load_settings(self):
        settings = QSettings()
        settings.beginGroup('MainWindow')
        setting = settings.value('Geometry')
        if setting is not None:
            self.restoreGeometry(setting)
        setting = settings.value('State')
        if setting is not None:
            self.restoreState(setting)
        self.recent_projects = settings.value('RecentProjects', type=list)
        self.update_recent_projects()
        settings.endGroup()

        settings.beginGroup('NetworkView')
        setting = settings.value('style', None)
        self.style = style_from_css(setting)

        settings.endGroup()

    @debug
    def reset_layout(self, *args):
        # Move all docks to default areas
        dock_area = None
        for dock in self.dock_manager.dockWidgetsMap().values():
            if dock.objectName() == 'placeholder':
                pass
            elif dock.objectName() == 'jupyter':
                self.dock_manager.addDockWidget(TopDockWidgetArea, dock)
            elif hasattr(dock.widget(), 'gvNetwork'):
                self.dock_manager.addDockWidget(LeftDockWidgetArea, dock, self.dock_placeholder.dockAreaWidget())
            else:
                if dock_area is None:
                    dock_area = self.dock_manager.addDockWidget(BottomDockWidgetArea, dock)
                else:
                    self.dock_manager.addDockWidget(CenterDockWidgetArea, dock, dock_area)

                if dock.objectName() == '2spectra':
                    dock.toggleView(True)
                    dock.toggleView(False)

        if dock_area is not None:
            dock_area.setCurrentIndex(0)

        # Make sure all toolbars are visible
        for w in self.findChildren(QToolBar):
            if w.objectName() != "":
                w.setVisible(True)
                self.addToolBar(w)

    @debug
    def draw(self, compute_layouts=True, keep_vertices=False):
        for dock in self.network_docks.values():
            dock.widget().draw(compute_layouts, keep_vertices)

    @debug
    def apply_layout(self, widget, layout, isolated_nodes=None):
        hide_isolated_nodes = self.actionHideIsolatedNodes.isChecked()
        widget.apply_layout(layout, isolated_nodes=isolated_nodes, hide_isolated_nodes=hide_isolated_nodes)

    @debug
    def update_columns_mappings(self):
        columns_mappings = getattr(self.network, 'columns_mappings', {})

        id_ = columns_mappings.get('label', None)
        if id_ is not None:
            self.set_nodes_label(id_)

        try:
            ids, colors = columns_mappings.get('pies', (None, None))
        except TypeError:
            pass
        else:
            if ids is not None and colors is not None:
                self.set_nodes_pie_chart_values(ids, colors)

        try:
            id_, func = columns_mappings.get('size', (None, None))
        except TypeError:
            pass
        else:
            if id_ is not None and func is not None:
                self.set_nodes_sizes_values(id_, func)

        try:
            id_, colors = columns_mappings.get('colors', (None, None))
        except TypeError:
            pass
        else:
            if id_ is not None and colors is not None:
                self.set_nodes_colors_values(id_, colors)

    @debug
    def prepare_compute_scores_worker(self, spectra, use_multiprocessing):
        def error(e):
            if isinstance(e, OSError):
                QMessageBox.warning(self, None, str(e))
            if isinstance(e, MemoryError):
                QMessageBox.critical(self, None, "Not enough memory was available to compute scores matrix.")
            else:
                raise e

        worker = workers.ComputeScoresWorker(spectra, use_multiprocessing, self.network.options.cosine)
        worker.error.connect(error)

        return worker

    @debug
    def prepare_read_data_worker(self, mgf_filename):
        def error(e):
            if isinstance(e, KeyError) and e.args[0] in ("pepmass", "precursormz"):
                QMessageBox.warning(self, None, "File format is incorrect. At least one scan has no parent's "
                                                "m/z defined.")
            elif isinstance(e, NotImplementedError):
                QMessageBox.warning(self, None, "File format is not supported.")
            elif hasattr(e, 'message'):
                QMessageBox.warning(self, None, e.message)
            else:
                QMessageBox.warning(self, None, str(e))

        worker = workers.ReadDataWorker(mgf_filename, self.network.options.cosine)
        worker.error.connect(error)

        return worker

    @debug
    def prepare_generate_network_worker(self, keep_vertices=False):
        if self._network.interactions is not None:
            return

        mzs = self._network.mzs
        if not mzs:
            mzs = np.zeros(self._network.scores.shape[:1], dtype=int)

        worker = workers.GenerateNetworkWorker(self._network.scores, mzs, self._network.graph,
                                               self._network.options.network, keep_vertices=keep_vertices)

        def store_interactions(worker: workers.GenerateNetworkWorker):
            interactions, graph = worker.result()
            self._network.interactions = interactions
            self._network.graph = graph

        return [worker, store_interactions]

    @debug
    def prepare_read_metadata_worker(self, filename, options):
        def file_read():
            nonlocal worker
            model = self.tvNodes.model().sourceModel()
            model.beginResetModel()
            self.network.infos = worker.result()  # TODO: Append metadata instead of overriding
            self.network.mappings = {}
            self.has_unsaved_changes = True
            self.set_nodes_pie_chart_values(None)
            self.set_nodes_sizes_values(None)
            self.set_nodes_colors_values(None)
            self.set_nodes_label(None)
            model.endResetModel()

        def error(e):
            message = str(e).strip("\n")
            QMessageBox.warning(self, None, "Metadata were not imported because the following error occurred:\n"
                                            f"\"{message}\".\n"
                                            "Your metadata file might be corrupted/invalid.")

        worker = workers.ReadMetadataWorker(filename, options)
        worker.finished.connect(file_read)
        worker.error.connect(error)

        return worker

    @debug
    def prepare_save_project_worker(self, fname):
        """Save current project to a file for future access"""

        def process_finished():
            # Save filename and set window title
            self.fname = fname
            self.has_unsaved_changes = False

            # Update list of recent projects
            self.update_recent_projects(fname)

            # Clean-up saved color/size properties
            # for name, dock in self._network_docks.items():
            #     if '__{}_color'.format(name) in self._network.graph.vs.attributes():
            #         del self._network.graph.vs['__{}_color'.format(name)]
            #     if '__{}_size'.format(name) in self._network.graph.vs.attributes():
            #         del self._network.graph.vs['__{}_size'.format(name)]

        def error(e):
            if isinstance(e, PermissionError):
                QMessageBox.warning(self, None, str(e))
            else:
                raise e

        # # Save color/size properties
        # for name, dock in self._network_docks.items():
        #     self._network.graph.vs['__{}_color'.format(name)] = dock.widget().gvNetwork.scene().nodesColors()
        #     self._network.graph.vs['__{}_size'.format(name)] = dock.widget().gvNetwork.scene().nodesRadii()

        worker = workers.SaveProjectWorker(fname, self.network.graph, self.network, self.network.options,
                                           layouts={d.widget().name: d.widget().get_layout_data() for d in
                                                    self.network_docks.values()},
                                           original_fname=self.fname)
        worker.finished.connect(process_finished)
        worker.error.connect(error)

        return worker

    @debug
    def prepare_load_project_worker(self, fname):
        """Load project from a previously saved file"""

        def error(e):
            if isinstance(e, FileNotFoundError):
                QMessageBox.warning(self, None, f"File '{fname}' not found.")
                self.update_recent_projects(remove_fname=fname)
            elif isinstance(e, errors.UnsupportedVersionError):
                QMessageBox.warning(self, None, str(e))
            elif isinstance(e, KeyError):
                QMessageBox.critical(self, None, str(e))
            elif isinstance(e, zipfile.BadZipFile):
                QMessageBox.warning(self, None,
                                    f"Selected file is not a valid {QCoreApplication.applicationName()} file")
            else:
                raise e

        worker = workers.LoadProjectWorker(fname)
        worker.error.connect(error)

        return worker

    @debug
    def prepare_query_database_worker(self, indices, options):
        if (getattr(self.network, 'mzs', None) is None or getattr(self.network, 'spectra', None) is None
                or not os.path.exists(config.SQL_PATH)):
            return

        if self.network.mzs:
            mzs = [self.network.mzs[index] for index in indices]
        else:
            mzs = [0] * len(indices)
        spectra = [self.network.spectra[index] for index in indices]
        worker = workers.QueryDatabasesWorker(indices, mzs, spectra, options)

        def query_finished():
            nonlocal worker
            result = worker.result()
            if result:
                self.tvNodes.model().sourceModel().beginResetModel()
                type_ = "analogs" if options.analog_search else "standards"
                # Update db_results with these new results
                num_results = 0
                for row in result:
                    if result[row][type_]:
                        num_results += len(result[row][type_])
                        if row in self.network.db_results:
                            self.network.db_results[row][type_] = result[row][type_]
                        else:
                            self.network.db_results[row] = {type_: result[row][type_]}
                    elif row in self.network.db_results and type_ in self.network.db_results[row]:
                        del self.network.db_results[row][type_]
                self.has_unsaved_changes = True
                self.tvNodes.model().sourceModel().endResetModel()

                # Show column if db_results is not empty
                was_hidden = self.tvNodes.isColumnHidden(1)
                self.tvNodes.setColumnBlinking(1, True)
                self.tvNodes.setColumnHidden(1, self.network.db_results is None or len(self.network.db_results) == 0)
                if was_hidden:
                    fm = QFontMetrics(self.tvNodes.font())
                    width = fm.width(self.tvNodes.model().headerData(1, Qt.Horizontal)) + 36
                    self.tvNodes.setColumnWidth(1, width)

                QMessageBox.information(self, None, f'{num_results} results found.')
            else:
                QMessageBox.warning(self, None, 'No results found.')

        def error(e):
            if isinstance(e, sqlalchemy.exc.OperationalError):
                QMessageBox.warning(self, None, 'You have to download at least one database before trying to query it.')

        worker.started.connect(lambda: self.tvNodes.setColumnBlinking(1, False))
        worker.finished.connect(query_finished)
        worker.error.connect(error)
        return worker

    @debug
    def prepare_read_group_mapping_worker(self, filename):
        worker = workers.ReadGroupMappingWorker(filename)

        def finished():
            nonlocal worker
            result = worker.result()
            self.tvNodes.model().sourceModel().beginResetModel()
            self.network.mappings = result
            self.has_unsaved_changes = True
            self.tvNodes.model().sourceModel().endResetModel()

        def error(e):
            if isinstance(e, ValueError):
                QMessageBox.warning(self, None, "Group mapping file format was not recognized.")
            elif isinstance(e, FileNotFoundError):
                QMessageBox.warning(self, None, "Group mapping file does not exist.")
            else:
                QMessageBox.warning(self, None,
                                    f"Group mapping was not loaded because the following error occurred: {str(e)}")

        worker.finished.connect(finished)
        worker.error.connect(error)
        return worker

    @debug
    def prepare_export_metadata_worker(self, filename, model, sep):
        worker = workers.ExportMetadataWorker(filename, model, sep)

        def finished():
            QMessageBox.information(self, None, f"Metadata were successfully exported to \"{filename}\".")

        def error(e):
            QMessageBox.warning(self, None,
                                f"Metadata were not exported because the following error occurred: {str(e)})")

        worker.finished.connect(finished)
        worker.error.connect(error)
        return worker

    @debug
    def prepare_export_db_results_worker(self, filename, model, fmt):
        worker = workers.ExportDbResultsWorker(filename, model, fmt)

        def finished():
            QMessageBox.information(self, None, f"Database results were successfully exported to \"{filename}\".")

        def error(e):
            QMessageBox.warning(self, None,
                                f"Database results were not exported because the following error occurred: {str(e)})")

        worker.finished.connect(finished)
        worker.error.connect(error)
        return worker
