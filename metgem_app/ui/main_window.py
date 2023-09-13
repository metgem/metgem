import bisect
import csv
import io
import json
import os
import zipfile
from typing import List, Callable, Dict, Union, Tuple

import igraph as ig
import numpy as np
import pandas as pd
import requests
import sqlalchemy

from PySide6.QtCore import (QSettings, Qt, QCoreApplication, QRectF, QAbstractTableModel)
from PySide6.QtGui import (QPainter, QImage, QColor, QKeyEvent, QIcon, QFontMetrics, QFont,
                           QKeySequence, QCursor, QBrush, QAction, QActionGroup)
from PySide6.QtWidgets import (QDialog, QFileDialog, QMessageBox, QWidget, QMenu, QMainWindow,
                               QTableView, QComboBox, QToolBar,
                               QApplication, QGraphicsView, QLineEdit, QListWidget, QLabel, QToolButton)

from PySide6QtAds import (CDockManager, CDockWidget,
                          BottomDockWidgetArea, CenterDockWidgetArea,
                          TopDockWidgetArea, LeftDockWidgetArea)
from libmetgem import human_readable_data

try:
    # noinspection PyUnresolvedReferences
    from PySide6.QtSvg import QSvgGenerator
except ImportError:
    HAS_SVG = False
else:
    HAS_SVG = True

from metgem_app.models import metadata
from metgem_app import config, ui, utils
from metgem_app.workers import core as workers_core
from metgem_app.workers import gui as workers_gui
from metgem_app.workers import net as workers_net
from metgem_app.workers import databases as workers_dbs
from metgem_app.workers import options as workers_opts
from metgem_app.ui import widgets
from metgem_app.logger import logger, debug
from metgem_app.utils.network import Network, generate_id
from metgem_app.utils.emf_export import HAS_EMF_EXPORT

if HAS_EMF_EXPORT:
    from ..utils.emf_export import EMFPaintDevice
from ..utils.gui import enumerateMenu, SignalGrouper, SignalBlocker
from ..config import get_python_rendering_flag
from ..utils import hasinstance
from .main_window_ui import Ui_MainWindow
from .widgets.search_ui import Ui_Form as Ui_SearchWidget

from PySide6MolecularNetwork.node import NodePolygon
if get_python_rendering_flag():
    from PySide6MolecularNetwork._pure import style_from_css, style_to_cytoscape, disable_opengl, DefaultStyle
else:
    from PySide6MolecularNetwork import style_from_css, style_to_cytoscape, disable_opengl, DefaultStyle

COLUMN_MAPPING_PIE_CHARTS = 0
COLUMN_MAPPING_LABELS = 1
COLUMN_MAPPING_NODES_SIZES = 2
COLUMN_MAPPING_NODES_COLORS = 3
COLUMN_MAPPING_NODES_PIXMAPS = 4


class SearchWidget(QWidget, Ui_SearchWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)


# noinspection PyCallByClass,PyArgumentList
class MainWindow(QMainWindow, Ui_MainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Keep a reference to the currently opened dialog
        self._dialog = None

        # Keep track of unsaved changes
        self._has_unsaved_changes = False

        # Opened file
        self.fname = None

        # Workers' references
        self._workers = workers_core.WorkerQueue(self, ui.ProgressDialog(self))

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

        self.setAcceptDrops(True)

        self._status_nodes_widget = QLabel("")
        self.statusBar().addPermanentWidget(self._status_nodes_widget)
        self._status_edges_widget = QLabel("")
        self.statusBar().addPermanentWidget(self._status_edges_widget)

        # Add Dockable Windows
        self.add_docks()

        # add welcome screen
        self._welcome_screen = widgets.WelcomeWidget(self.dock_manager)

        # Add model to table views
        model = metadata.NodesModel(self)
        proxy = metadata.NodesSortFilterProxyModel()
        proxy.setSourceModel(model)
        self.tvNodes.setModel(proxy)
        model = metadata.EdgesModel(self)
        proxy = metadata.EdgesSortFilterProxyModel()
        proxy.setSourceModel(model)
        self.tvEdges.setModel(proxy)

        # Init project's objects
        self.init_project()

        # Move search layout to search toolbar
        self.search_widget = SearchWidget()
        self.tbSearch.addWidget(self.search_widget)

        # Reorganise export as image actions
        export_button = widgets.ToolBarMenu(self)
        export_button.setDefaultAction(self.actionExportAsImage)
        export_button.addAction(self.actionExportAsImage)
        export_button.addAction(self.actionExportCurrentViewAsImage)
        self.tbExport.insertWidget(self.actionExportAsImage, export_button)
        self.tbExport.removeAction(self.actionExportAsImage)
        self.tbExport.removeAction(self.actionExportCurrentViewAsImage)

        # Reorganize export metadata actions
        export_button = widgets.ToolBarMenu(self)
        export_button.setDefaultAction(self.actionExportMetadata)
        export_button.addAction(self.actionExportMetadata)
        export_button.addAction(self.actionExportDatabaseResults)
        self.tbExport.insertWidget(self.actionExportMetadata, export_button)
        self.tbExport.removeAction(self.actionExportMetadata)
        self.tbExport.removeAction(self.actionExportDatabaseResults)

        # Create actions to add new views
        self._create_network_button = widgets.ToolBarMenu()
        self._create_network_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        set_default = True
        extras_menu = None
        for view_class in widgets.AVAILABLE_NETWORK_WIDGETS.values():
            if view_class.extra:
                if extras_menu is None:
                    extras_menu = self._create_network_button.addMenu("Extras")
                action = extras_menu.addAction('Add {} view'.format(view_class.title))
            else:
                action = self._create_network_button.addAction('Add {} view'.format(view_class.title))
            action.setIcon(self.actionAddNetworkView.icon())
            action.setData(view_class)
            action.triggered.connect(self.on_add_view_triggered)
            if set_default:
                self._create_network_button.setDefaultAction(action)
                set_default = False
        self.tbFile.insertWidget(self.actionAddNetworkView, self._create_network_button)
        self.tbFile.removeAction(self.actionAddNetworkView)

        color_button = widgets.ColorPicker(self.actionSetNodesColor, color_group='Node', default_color=Qt.blue)
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
        self._welcome_screen.importDataClicked.connect(self.on_process_file_triggered)
        self._welcome_screen.openProjectClicked.connect(self.on_open_project_triggered)

        self._docks_closed_signals_grouper = SignalGrouper()  # Group signals emitted when dock widgets are closed
        self._docks_closed_signals_grouper.groupped.connect(self.on_network_widget_closed)

        self.nodes_widget.tvNodes.customContextMenuRequested.connect(self.on_nodes_table_contextmenu)
        self.tvEdges.customContextMenuRequested.connect(self.on_edges_table_contextmenu)
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
        self.nodes_widget.actionUseColumnForNodesPixmaps.triggered.connect(
            lambda: self.on_use_columns_for(COLUMN_MAPPING_NODES_PIXMAPS))
        self.nodes_widget.actionResetPixmapMapping.triggered.connect(lambda: self.set_nodes_pixmaps_values(None))
        self.nodes_widget.actionHighlightSelectedNodes.triggered.connect(self.highlight_selected_nodes)
        self.nodes_widget.actionViewSpectrum.triggered.connect(
            lambda: self.on_show_spectrum_from_table_triggered('show'))
        self.nodes_widget.actionViewCompareSpectrum.triggered.connect(
            lambda: self.on_show_spectrum_from_table_triggered('compare'))
        self.nodes_widget.actionFindStandards.triggered.connect(lambda: self.on_query_databases('standards'))
        self.nodes_widget.actionFindAnalogs.triggered.connect(lambda: self.on_query_databases('analogs'))
        # self.nodes_widget.actionMetFrag.triggered.connect(lambda: self.on_query_in_silico_db('metfrag'))
        # self.nodes_widget.actionCFMID.triggered.connect(lambda: self.on_query_in_silico_db('cfm-id'))
        self.nodes_widget.actionAddColumnsByFormulae.triggered.connect(self.on_add_columns_by_formulae)
        self.nodes_widget.actionClusterize.triggered.connect(self.on_clusterize)
        self.nodes_widget.actionNumberize.triggered.connect(self.on_numberize)
        self.nodes_widget.actionDeleteColumns.triggered.connect(self.on_delete_nodes_columns)
        self.nodes_widget.actionFilterByMZ.triggered.connect(self.on_filter)

        self.edges_widget.actionHighlightSelectedEdges.triggered.connect(self.highlight_selected_edges)
        self.edges_widget.actionHighlightNodesFromSelectedEdges.triggered.connect(
            self.highlight_nodes_from_selected_edges)

        self.actionQuit.triggered.connect(self.close)
        self.actionCheckUpdates.triggered.connect(
            lambda: self.check_for_updates(could_ignore=False, notify_if_no_update=True))
        self.actionShowPluginManager.triggered.connect(self.on_show_plugins_manager_triggered)
        self.actionOpenPluginsFolder.triggered.connect(lambda: utils.open_folder(config.PLUGINS_PATH))
        self.actionAbout.triggered.connect(lambda: ui.AboutDialog().exec_())
        self.actionAboutQt.triggered.connect(lambda: QMessageBox.aboutQt(self))
        self.actionProcessFile.triggered.connect(self.on_process_file_triggered)
        self.actionImportMetadata.triggered.connect(self.on_import_metadata_triggered)
        self.actionImportGroupMapping.triggered.connect(self.on_import_group_mapping_triggered)
        self.actionCurrentParameters.triggered.connect(self.on_current_parameters_triggered)
        self.actionPreferences.triggered.connect(self.on_preferences_triggered)
        self.actionResetLayout.triggered.connect(self.reset_layout)
        self.actionOpenUserFolder.triggered.connect(lambda: utils.open_folder(config.USER_PATH))
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
        QCoreApplication.instance().focusChanged.connect(self.on_focus_changed)
        self.actionViewSpectrum.triggered.connect(lambda: self.on_show_spectrum_triggered('show'))
        self.actionViewCompareSpectrum.triggered.connect(lambda: self.on_show_spectrum_triggered('compare'))
        # noinspection PyPep8
        self.actionFindStandards.triggered.connect(lambda: self.on_query_databases('show',
            {node.index() for node in self.current_view.scene().selectedNodes()}))
        # noinspection PyPep8
        self.actionFindAnalogs.triggered.connect(lambda: self.on_query_databases('compare',
            {node.index() for node in self.current_view.scene().selectedNodes()}))

        self.actionFullScreen.triggered.connect(self.on_full_screen_triggered)
        self.actionHideSelected.triggered.connect(lambda: self.current_view.scene().hideSelectedItems()
                                                  if self.current_view is not None else None)
        self.actionShowAll.triggered.connect(lambda: self.current_view.scene().showAllItems()
                                             if self.current_view is not None else None)
        self.actionHideIsolatedNodes.triggered.connect(lambda x: [d.widget().show_isolated_nodes(x)
                                                                  for d in self.network_docks.values()])
        color_button.colorSelected.connect(self.on_set_selected_nodes_color)
        color_button.colorReset.connect(self.on_reset_selected_nodes_color)
        size_combo.currentIndexChanged.connect(lambda x: self.on_set_selected_nodes_size(size_combo.itemText(x)))
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

        group_tool = QActionGroup(self)
        group_tool.addAction(self.actionSelectItems)
        group_tool.addAction(self.actionAddAnnotationLine)
        group_tool.addAction(self.actionAddAnnotationArrow)
        group_tool.addAction(self.actionAddAnnotationRect)
        group_tool.addAction(self.actionAddAnnotationEllipse)
        group_tool.addAction(self.actionAddAnnotationText)
        group_tool.setExclusive(True)
        self.actionSelectItems.triggered.connect(lambda: self.on_set_annotations_mode(None))
        self.actionAddAnnotationLine.triggered.connect(
            lambda x: self.on_set_annotations_mode(widgets.MODE_LINE if x else None))
        self.actionAddAnnotationArrow.triggered.connect(
            lambda x: self.on_set_annotations_mode(widgets.MODE_ARROW if x else None))
        self.actionAddAnnotationRect.triggered.connect(
            lambda x: self.on_set_annotations_mode(widgets.MODE_RECT if x else None))
        self.actionAddAnnotationEllipse.triggered.connect(
            lambda x: self.on_set_annotations_mode(widgets.MODE_ELLIPSE if x else None))
        self.actionAddAnnotationText.triggered.connect(
            lambda x: self.on_set_annotations_mode(widgets.MODE_TEXT if x else None))
        self.actionDeleteAnnotations.triggered.connect(self.on_delete_selected_annotations)
        self.actionClearAnnotations.triggered.connect(self.on_clear_annotations)
        self.actionUndoAnnotations.triggered.connect(self.on_undo_annotations)
        self.actionRedoAnnotations.triggered.connect(self.on_redo_annotations)
        self.btUndoAnnotations = widgets.ToolBarMenu()
        self.btUndoAnnotations.setDefaultAction(self.actionUndoAnnotations)
        self.btUndoAnnotations.setIcon(self.actionUndoAnnotations.icon())
        self.btUndoAnnotations.setPopupMode(QToolButton.DelayedPopup)
        self.tbAnnotations.insertWidget(self.actionUndoAnnotations, self.btUndoAnnotations)
        self.tbAnnotations.removeAction(self.actionUndoAnnotations)

        self.dock_nodes.visibilityChanged.connect(lambda v: self.update_search_menu(self.tvNodes) if v else None)
        self.dock_edges.visibilityChanged.connect(lambda v: self.update_search_menu(self.tvEdges) if v else None)
        self.dock_spectra.visibilityChanged.connect(lambda v: self.update_search_menu(self.tvNodes) if v else None)
        self.dock_edges.dockAreaWidget().currentChanging.connect(lambda v: self.on_current_tab_changing(v))

        self.tvNodes.viewDetailsClicked.connect(self.on_view_details_clicked)
        self.tvNodes.model().dataChanged.connect(self.on_nodes_table_data_changed)
        self.tvNodes.model().modelReset.connect(self.update_columns_mappings)
        self.tvNodes.horizontalHeader().sectionMoved.connect(self.on_nodes_table_column_moved)

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
            self._welcome_screen.addRecentProject("")
        self._welcome_screen.recentProjectsItemClicked.connect(self.on_open_recent_project_triggered)

        menu.addSeparator()
        action = QAction("&Clear menu", self)
        action.triggered.connect(lambda: self.update_recent_projects(clear=True))
        self._welcome_screen.clearRecentProjectsClicked.connect(action.trigger)
        menu.addAction(action)

        # Build research bar
        self._last_table = self.tvNodes
        self.update_search_menu()

        # Check for updates
        self.check_for_updates()

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
                self.jupyter_widget = widgets.JupyterWidget()
            except (AttributeError, ImportError):
                pass
            else:
                dock = CDockWidget("Jupyter Console")
                dock.setObjectName("jupyter")
                dock.setIcon(QIcon(":/icons/images/python.svg"))
                dock.setWidget(self.jupyter_widget)
                self.jupyter_widget.push(app=QCoreApplication.instance(), win=self)
                self.dock_manager.addDockWidget(TopDockWidgetArea, dock)
                self.dock_manager.addToggleViewActionToMenu(dock.toggleViewAction())

        self.dock_nodes = CDockWidget("Nodes")
        self.dock_nodes.setObjectName("0nodes")
        self.dock_nodes.setIcon(QIcon(":/icons/images/node.svg"))
        self.nodes_widget = widgets.NodesWidget()
        self.tvNodes = self.nodes_widget.tvNodes
        self.dock_nodes.setWidget(self.nodes_widget)
        dock_area = self.dock_manager.addDockWidget(BottomDockWidgetArea, self.dock_nodes)
        self.dock_manager.addToggleViewActionToMenu(self.dock_nodes.toggleViewAction())
        self.dock_nodes.toggleView(False)

        self.dock_edges = CDockWidget("Edges")
        self.dock_edges.setObjectName("1edges")
        self.dock_edges.setIcon(QIcon(":/icons/images/edge.svg"))
        self.edges_widget = widgets.EdgesWidget()
        self.tvEdges = self.edges_widget.tvEdges
        self.dock_edges.setWidget(self.edges_widget)
        self.dock_manager.addDockWidget(CenterDockWidgetArea, self.dock_edges, dock_area)
        self.dock_manager.addToggleViewActionToMenu(self.dock_edges.toggleViewAction())
        self.dock_edges.toggleView(False)

        self.dock_spectra = CDockWidget("Spectra")
        self.dock_spectra.setObjectName("2spectra")
        self.dock_spectra.setIcon(QIcon(":/icons/images/spectrum.svg"))
        self.spectra_widget = widgets.SpectraComparisonWidget(self)
        self.dock_spectra.setWidget(self.spectra_widget)
        self.dock_manager.addDockWidget(CenterDockWidgetArea, self.dock_spectra, dock_area)
        self.dock_manager.addToggleViewActionToMenu(self.dock_spectra.toggleViewAction())
        self.dock_spectra.toggleView(False)

        self.dock_annotations = CDockWidget("Annotations")
        self.dock_annotations.setObjectName("3annotations")
        self.dock_annotations.setIcon(QIcon(":/icons/images/add-text.svg"))
        self.annotations_widget = widgets.AnnotationsWidget()
        self.dock_annotations.setWidget(self.annotations_widget)
        self.dock_manager.addDockWidget(CenterDockWidgetArea, self.dock_annotations, dock_area)
        self.dock_manager.addToggleViewActionToMenu(self.dock_annotations.toggleViewAction())
        self.dock_annotations.toggleView(False)

        self.dock_manager.viewMenu().addSeparator()
        self.menuView.addMenu(self.dock_manager.viewMenu())
        dock_area.setCurrentIndex(0)

    @debug
    def init_project(self):
        # Create an object to store all computed objects
        self.network = Network()

        # Create options dict
        self._network.options = workers_opts.AttrDict()

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
    def current_network_widget(self):
        docks = list(self.network_docks.values())
        for dock in docks:
            widget = dock.widget()
            if widget.view().hasFocus():
                return widget

        try:
            return docks[0].widget()
        except IndexError:
            return

    @property
    def current_view(self):
        widget = self.current_network_widget
        return widget.view() if widget is not None else None

    @property
    def network(self):
        return self._network

    @network.setter
    def network(self, network):
        network.infosAboutToChange.connect(self.tvNodes.sourceModel().beginResetModel)
        network.infosChanged.connect(self.tvNodes.sourceModel().endResetModel)

        self.tvNodes.setColumnHidden(1, network.db_results is None or len(network.db_results) == 0)

        self._network = network

        self.update_status_widgets()

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
        # noinspection PyShadowingNames
        def create_draw_workers(worker: workers_core.LoadProjectWorker):
            self.reset_project()

            self.tvNodes.model().setSelection([])
            self.tvEdges.model().setSelection([])
            self.tvNodes.sourceModel().beginResetModel()
            network, layouts, graphs, annotations = worker.result()
            self.network = network
            self.tvNodes.sourceModel().endResetModel()
            self.tvEdges.sourceModel().beginResetModel()
            self.tvEdges.sourceModel().endResetModel()

            self.tvNodes.setColumnHidden(1, self.network.db_results is None or len(self.network.db_results) == 0)

            self.dock_edges.toggleView(True)
            self.dock_nodes.toggleView(True)

            workers = []
            for id_, value in layouts.items():
                try:
                    name = id_.split('_')[0]
                    widget_class = widgets.AVAILABLE_NETWORK_WIDGETS[name]
                except (KeyError, IndexError):
                    pass
                else:
                    g = graphs.get(id_, {})
                    graph = g.get('graph', ig.Graph())
                    interactions = g.get('interactions', pd.DataFrame())
                    widget = self.add_network_widget(widget_class, id_, graph, interactions)
                    if widget is not None:
                        layout = value.get('layout')
                        if layout is not None:
                            colors = value.get('colors', {})
                            colors = [QColor(colors.get(str(i), '')) for i in range(layout.shape[0])]
                        else:
                            colors = []

                        worker = widget.create_draw_worker(compute_layouts=False,
                                                           colors=colors,
                                                           radii=value.get('radii', []),
                                                           layout=layout,
                                                           isolated_nodes=value.get('isolated_nodes'))
                        ann = annotations.get(name)
                        if ann:
                            worker.finished.connect(lambda ann=ann, w=widget: w.set_annotations_data(ann))
                        workers.append(worker)
            if workers:
                return workers

        # noinspection PyUnusedLocal
        def save_filename(*args):
            # Save filename and set window title
            self.fname = filename
            self.has_unsaved_changes = False

        worker = self.prepare_load_project_worker(filename)
        if worker is not None:
            self._workers.append(worker)
            self._workers.append(create_draw_workers)
            self._workers.append(lambda _: self.update_columns_mappings(force_reset_mapping=False))
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
        try:
            self.network.spectra.close()
        except AttributeError:
            pass

        for dock in self.network_docks.values():
            self.dock_manager.removeDockWidget(dock)

        self.dock_nodes.toggleView(False)
        self.dock_edges.toggleView(False)
        self.dock_spectra.toggleView(False)
        self.dock_annotations.toggleView(False)

        self.tvNodes.sourceModel().beginResetModel()
        self.tvEdges.sourceModel().beginResetModel()
        self.init_project()
        self.tvNodes.sourceModel().endResetModel()
        self.tvEdges.sourceModel().endResetModel()
        self.spectra_widget.set_spectrum1(None)
        self.spectra_widget.set_spectrum2(None)
        self.update_search_menu()
        self.has_unsaved_changes = False

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

            item = self._welcome_screen.recentProjectItem(i)

            try:
                fname = self.recent_projects[i]

                act.setText(f"{i + 1} | {fname}")
                act.setData(fname)
                act.setVisible(True)

                item.setText(fname)
                item.setData(Qt.UserRole, fname)
                item.setToolTip(fname)
                item.setHidden(False)
            except IndexError:
                act.setVisible(False)
                item.setHidden(True)

    # noinspection PyUnusedLocal
    def update_status_widgets(self, *args):
        mzs = getattr(self.network, 'mzs', pd.Series(dtype='float64'))
        widget = self.current_network_widget
        if widget is not None and mzs.size > 0:
            num_nodes = len(mzs)
            self._status_nodes_widget.setText(
                f'<img src=":/icons/images/node.svg" height="20" style="vertical-align: top;" /> <i>{num_nodes}</i>')
            self._status_nodes_widget.setToolTip(f"{num_nodes} Nodes" if num_nodes > 0 else "No Node")

            num_edges = widget.interactions.size
            self._status_edges_widget.setText(
                f'<img src=":/icons/images/edge.svg" height="20" style="vertical-align: top;" /> <i>{num_edges}</i>')
            self._status_edges_widget.setToolTip(f"{num_edges} Edges" if num_edges > 0 else "No Edge")
        else:
            self._status_nodes_widget.setText("")
            self._status_nodes_widget.setToolTip("")
            self._status_edges_widget.setText("")
            self._status_edges_widget.setToolTip("")

    def keyPressEvent(self, event: QKeyEvent):
        widget = QApplication.focusWidget()

        if event.matches(QKeySequence.NextChild):
            # Navigate between GraphicsViews
            docks = list(self.network_docks.values())
            current_index = -1
            for i, dock in enumerate(docks):
                view = dock.widget().view()
                if view.hasFocus():
                    current_index = i
                elif current_index >= 0:
                    try:
                        next_dock = docks[current_index + 1]
                        if next_dock.isVisible():
                            next_dock.widget().view().setFocus(Qt.TabFocusReason)
                            break
                    except IndexError:
                        pass

            if current_index == -1 or current_index == len(docks) - 1:
                try:
                    docks[0].widget().view().setFocus(Qt.TabFocusReason)
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
            # noinspection PyAttributeOutsideInit
            self._default_state = self.dock_manager.saveState()
            # noinspection PyAttributeOutsideInit
            self._first_show = False

        self._welcome_screen.move(self.rect().center() - self._welcome_screen.rect().center())
        self._welcome_screen.lower()
        self.dock_placeholder.toggleView(True)  # TODO: Work around for welcome screen not being clickable at start-up
        self._welcome_screen.show()
        self.dock_placeholder.toggleView(False)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._welcome_screen.move(self.rect().center() - self._welcome_screen.rect().center())

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

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("text/uri-list"):
            event.acceptProposedAction()

    def dropEvent(self, event):
        mime_data = event.mimeData()
        if mime_data.hasUrls():
            for url in mime_data.urls():
                path = url.toLocalFile()
                if os.path.splitext(path)[1] == config.FILE_EXTENSION:
                    reply = self.confirm_save_changes()
                    if reply == QMessageBox.Cancel:
                        return

                    self.load_project(path)
                    event.acceptProposedAction()
                    break

    # noinspection PyUnusedLocal
    @debug
    def on_focus_changed(self, old: QWidget, now: QWidget):
        if isinstance(now, widgets.AnnotationsNetworkView):
            self.update_status_widgets()

            self.tvEdges.sourceModel().beginResetModel()
            self.tvEdges.sourceModel().endResetModel()

            self.actionViewMiniMap.setChecked(now.minimap.isVisible())
            self.btUndoAnnotations.setMenu(now.undoMenu())
            self.annotations_widget.setModel(widgets.AnnotationsModel(now.scene()))

    @debug
    def on_current_tab_changing(self, index: int):
        if index == 1:  # Edges
            self.tvEdges.sourceModel().beginResetModel()
            self.tvEdges.sourceModel().endResetModel()

    # noinspection PyUnusedLocal
    @debug
    def on_switch_minimap_visibility(self, *args):
        view = self.current_view
        if view is not None:
            visible = view.minimap.isVisible()
            view.minimap.setVisible(not visible)
            self.actionViewMiniMap.setChecked(not visible)

    @debug
    def on_scene_selection_changed(self, scene, update_view=True):
        nodes_idx = [item.index() for item in scene.selectedNodes()]
        edges_idx = [item.index() for item in scene.selectedEdges()]
        self.tvNodes.model().setSelection(nodes_idx)
        self.tvEdges.model().setSelection(edges_idx)

        if update_view and self.actionLinkViews.isChecked():
            for dock in self.network_docks.values():
                widget_scene = dock.widget().scene()
                if widget_scene != scene:
                    with SignalBlocker(widget_scene):
                        widget_scene.setNodesSelection(nodes_idx)

    @debug
    def on_set_selected_nodes_color(self, color: QColor):
        for dock in self.network_docks.values():
            dock.widget().scene().setSelectedNodesColor(color)

        self.has_unsaved_changes = True

    @debug
    def on_reset_selected_nodes_color(self):
        for dock in self.network_docks.values():
            scene = dock.widget().scene()
            scene.setSelectedNodesColor(scene.networkStyle().nodeBrush().color())

        self.has_unsaved_changes = True

    @debug
    def on_set_selected_nodes_size(self, text: str):
        try:
            size = int(text)
        except ValueError:
            return

        for dock in self.network_docks.values():
            dock.widget().scene().setSelectedNodesRadius(size)

        self.has_unsaved_changes = True

    # noinspection PyUnusedLocal
    @debug
    def on_do_search(self, *args):
        if self._last_table is None:
            return
        self._last_table.model().setFilterRegularExpression(str(self.search_widget.leSearch.text()))

    # noinspection PyUnusedLocal
    @debug
    def on_new_project_triggered(self, *args):
        reply = self.confirm_save_changes()

        if reply != QMessageBox.Cancel:
            self.reset_project()

        return reply

    @debug
    def on_open_recent_project_triggered(self, *args):
        sender = self.sender()
        if sender is not None:
            if isinstance(sender, QAction):
                self.load_project(sender.data())
            elif isinstance(sender, QListWidget):
                self.load_project(args[0].data(Qt.UserRole))

    # noinspection PyUnusedLocal
    @debug
    def on_open_project_triggered(self, *args):
        reply = self.confirm_save_changes()
        if reply == QMessageBox.Cancel:
            return

        self._dialog = QFileDialog(self)
        self._dialog.setFileMode(QFileDialog.ExistingFile)
        self._dialog.setNameFilters([f"{QCoreApplication.applicationName()} Files (*{config.FILE_EXTENSION})",
                               "All files (*)"])

        def open_file(result):
            if result == QDialog.Accepted:
                filename = self._dialog.selectedFiles()[0]
                self.load_project(filename)

        self._dialog.finished.connect(open_file)
        self._dialog.open()

    # noinspection PyUnusedLocal
    @debug
    def on_save_project_triggered(self, *args):
        if self.fname is None:
            self.on_save_project_as_triggered()
        else:
            self.save_project(self.fname)

    # noinspection PyUnusedLocal
    @debug
    def on_save_project_as_triggered(self, *args):
        self._dialog = QFileDialog(self)
        self._dialog.setAcceptMode(QFileDialog.AcceptSave)
        self._dialog.setDefaultSuffix(config.FILE_EXTENSION)
        self._dialog.setNameFilters([f"{QCoreApplication.applicationName()} Files (*{config.FILE_EXTENSION})",
                               "All files (*)"])

        def save_file(result):
            if result == QDialog.Accepted:
                filename = self._dialog.selectedFiles()[0]
                self.save_project(filename)

        self._dialog.finished.connect(save_file)
        self._dialog.open()

    @debug
    def on_set_pie_charts_visibility_toggled(self, visibility):
        for dock in self.network_docks.values():
            view = dock.widget().view()
            scene = view.scene()
            scene.setPieChartsVisibility(visibility)
            view.updateVisibleItems()

    # noinspection PyUnusedLocal
    @debug
    def on_export_to_cytoscape_triggered(self, *args):
        try:
            from py2cytoscape.data.cyrest_client import CyRestClient
            from py2cytoscape import cyrest

            widget = self.current_network_widget
            if widget is None:
                return
            view = widget.view()

            cy = CyRestClient()

            logger.debug('Creating exportable copy of the graph object')
            g = widget.graph.copy()
            if g.vcount() == 0:
                g.add_vertices(n.index() for n in view.scene().nodes())
            else:
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

                g = widget.process_graph_before_export(g)

            # cy.session.delete()
            logger.debug('CyREST: Creating network')
            g_cy = cy.network.create_from_igraph(g)

            logger.debug('CyREST: Set layout')
            layout = np.empty((g.vcount(), 2))
            for item in view.scene().nodes():
                layout[item.index()] = (item.x(), item.y())
            positions = [(suid, x, y) for suid, (x, y) in zip(g_cy.get_nodes()[::-1], layout)]
            cy.layout.apply_from_presets(network=g_cy, positions=positions)

            logger.debug('CyREST: Set style')
            style_js = style_to_cytoscape(view.scene().networkStyle())
            style = cy.style.create(style_js['title'], style_js)
            cy.style.apply(style, g_cy)

            # Fit view to content
            cyrest.cyclient().view.fit_content()
        except (ConnectionRefusedError, requests.ConnectionError):
            QMessageBox.information(self, None,
                                    'Please launch Cytoscape before trying to export.')
            logger.error('Cytoscape was not launched.')
        except json.decoder.JSONDecodeError:
            QMessageBox.information(self, None,
                                    'Cytoscape was not ready to receive data. Please try again.')
            logger.error('Cytoscape was not ready to receive data.')
        except ImportError:
            QMessageBox.information(self, None,
                                    ('py2tocytoscape is required for this action '
                                     '(https://pypi.python.org/pypi/py2cytoscape).'))
            logger.error('py2cytoscape not found.')
        except requests.exceptions.HTTPError as e:
            QMessageBox.warning(self, None, 'The following error occurred during export to Cytoscape: {str(e)}')
            logger.error(f'py2cytoscape HTTPError: {str(e)}')

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
                       "BMP - Windows Bitmap (*.bmp)"]
            if HAS_SVG:
                filter_.append("SVG - Scalable Vector Graphics (*.svg)")

            if HAS_EMF_EXPORT:
                filter_.append("EMF - Enhanced MetaFile (*.emf)")

            filename, filter_ = QFileDialog.getSaveFileName(self, "Save image",
                                                            filter=";;".join(filter_))

        if filename:
            if HAS_SVG and filter_.endswith("(*.svg)"):
                svg_gen = QSvgGenerator()

                svg_gen.setFileName(filename)
                rect = view.mapToScene(view.viewport().rect()).boundingRect()\
                    if type_ == 'current' else view.scene().sceneRect()
                svg_gen.setViewBox(rect)
                svg_gen.setSize(rect.size().toSize())
                svg_gen.setTitle("Molecular Network")
                svg_gen.setDescription(f"Generated by {QCoreApplication.applicationName()} "
                                       f"v{QCoreApplication.applicationVersion()}")

                painter = QPainter(svg_gen)
                if type_ == 'current':
                    view.scene().render(painter, target=rect, source=QRectF(rect))
                else:
                    view.scene().render(painter, target=rect)
                painter.end()
            elif filter_.endswith("(*.emf)") and HAS_EMF_EXPORT:  # Experimental EMF export support
                # noinspection PyPep8Naming
                DPI = 75
                # noinspection PyPep8Naming
                SCALE = 0.2

                rect = view.mapToScene(view.viewport().rect()).boundingRect()\
                    if type_ == 'current' else view.scene().sceneRect()
                rect2 = QRectF(rect.x() * SCALE, rect.y() * SCALE, rect.width() * SCALE, rect.height() * SCALE)
                trect = rect2.translated(-rect2.x(), -rect2.y())
                scaled_rect = QRectF(0, 0, rect2.width() / DPI * 100, rect2.height() / DPI * 100)
                paintdev = EMFPaintDevice(scaled_rect, dpi=DPI)
                painter = QPainter(paintdev)
                if type_ == 'current':
                    view.scene().render(painter, target=trect, source=QRectF(rect))
                else:
                    view.scene().render(painter, target=trect)
                painter.end()
                paintdev.paintEngine().saveFile(filename)
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

    # noinspection PyUnusedLocal
    @debug
    def on_export_metadata(self, *args):
        filter_ = ["CSV - Comma Separated Values (*.csv)",
                   "TSV - Tab Separated Values (*.tsv)"]

        filename, filter_ = QFileDialog.getSaveFileName(self, "Export metadata",
                                                        filter=";;".join(filter_))

        if filename:
            sep = '\t' if filter_.endswith("(*.tsv)") else ','
            selected_rows = [index.row() for index in self.tvNodes.selectionModel().selectedRows()]

            worker = self.prepare_export_metadata_worker(filename, self.tvNodes.model(),
                                                         sep, selected_rows)
            if worker is not None:
                self._workers.append(worker)
                self._workers.start()

    # noinspection PyUnusedLocal
    @debug
    def on_export_db_results(self, *args):
        self._dialog = ui.ExportDBResultsDialog(self)

        def export_db_results(result):
            if result == QDialog.Accepted:
                filename, *values = self._dialog.getValues()
                if not filename:
                    return
                selected_rows = [index.row() for index in self.tvNodes.selectionModel().selectedRows()]
                worker = self.prepare_export_db_results_worker(filename, values,
                                                               self.tvNodes.model(),
                                                               selected_rows)
                if worker is not None:
                    self._workers.append(worker)
                    self._workers.start()

        self._dialog.finished.connect(export_db_results)
        self._dialog.open()

    @debug
    def on_show_spectrum_from_table_triggered(self, type_):
        model = self.tvNodes.model()
        selected_indexes = model.mapSelectionToSource(
            self.tvNodes.selectionModel().selection()).indexes()

        if not selected_indexes:
            return

        try:
            node_idx = selected_indexes[0].row()
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

                data = self.network.spectra[self.network.mzs.index[node_idx]]
                if data.size == 0:
                    QMessageBox.warning(self, None, 'Selected spectrum is empty.')
                    return

                data = human_readable_data(data)

                if self.network.mzs is not None:
                    mz_parent = self.network.mzs.iloc[node_idx]
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
                    float_precision = QSettings().value('Metadata/float_precision', 4, type=int)
                    self.spectra_widget.set_title(f'Score: {score:.{float_precision}f}')
                set_spectrum(data, node_idx, mz_parent)

                # Show spectrum tab
                self.dock_spectra.dockAreaWidget().setCurrentDockWidget(self.dock_spectra)

    # noinspection PyUnusedLocal
    @debug
    def on_select_first_neighbors_triggered(self, nodes, *args):
        widget = self.current_network_widget
        if widget is not None:
            neighbors = [v.index for node in nodes for v in widget.graph.vs[node.index()].neighbors()]
            widget.view().scene().setNodesSelection(neighbors)

    @debug
    def on_use_columns_for(self, type_):
        model = self.tvNodes.sourceModel()
        if model.columnCount() <= 1:
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
            ids = None
            if len_ == 0:
                keys, _ = self.network.columns_mappings.get('pies', (None, None))
                if keys is not None and len(keys) > 0 and hasinstance(keys, str):
                    ids = model.headerKeysToIndices(keys)
            else:
                ids = [index.column() for index in selected_columns_indexes]

            self._dialog = ui.PieColorMappingDialog(self, model=self.tvNodes.model(), selected_columns=ids)

            def set_mapping(result):
                if result == QDialog.Accepted:
                    columns, colors = self._dialog.getValues()
                    self.set_nodes_pie_chart_values(columns, colors)
                    self.has_unsaved_changes = True
            self._dialog.finished.connect(set_mapping)
            self._dialog.open()
        elif type_ == COLUMN_MAPPING_NODES_SIZES:
            if len_ > 1:
                QMessageBox.information(self, None, "Please select only one column.")
            else:
                id_ = -1
                if len_ == 0:
                    key, func = self.network.columns_mappings.get('size', (None, None))
                    if key is not None and isinstance(key, str):
                        id_ = model.headerKeysToIndices([key])
                        id_ = id_[0] if id_ else -1
                else:
                    id_ = selected_columns_indexes[0].column()
                    func = None

                self._dialog = ui.SizeMappingDialog(self, model=self.tvNodes.model(),
                                                    column_id=id_, func=func)

                def set_mapping(result):
                    if result == QDialog.Accepted:
                        # noinspection PyShadowingNames
                        id_, func = self._dialog.getValues()
                        if id_ >= 0:
                            self.set_nodes_sizes_values(id_, func)
                        self.has_unsaved_changes = True

                self._dialog.finished.connect(set_mapping)
                self._dialog.open()
        elif type_ == COLUMN_MAPPING_NODES_COLORS:
            if len_ > 1:
                QMessageBox.information(self, None, "Please select only one column.")
            else:
                id_ = -1
                if len_ == 0:
                    key, mapping = self.network.columns_mappings.get('colors', (None, None))
                    if key is not None and isinstance(key, str):
                        id_ = model.headerKeysToIndices([key])
                        id_ = id_[0] if id_ else -1
                else:
                    id_ = selected_columns_indexes[0].column()
                    mapping = None

                self._dialog = ui.ColorMappingDialog(self, model=self.tvNodes.model(),
                                                     column_id=id_, mapping=mapping)

                def set_mapping(result):
                    if result == QDialog.Accepted:
                        # noinspection PyShadowingNames
                        id_, mapping = self._dialog.getValues()
                        if id_ >= 0:
                            self.set_nodes_colors_values(id_, mapping)
                        self.has_unsaved_changes = True

                self._dialog.finished.connect(set_mapping)
                self._dialog.open()
        elif type_ == COLUMN_MAPPING_NODES_PIXMAPS:
            if len_ == 0:
                return
            elif len_ > 1:
                QMessageBox.information(self, None, "Please select only one column.")
            else:
                id_ = selected_columns_indexes[0].column()
                self.set_nodes_pixmaps_values(id_)
                self.has_unsaved_changes = True

    @debug
    def on_nodes_table_contextmenu(self, event):
        column_index = self.nodes_widget.tvNodes.columnAt(event.x())
        row_index = self.nodes_widget.tvNodes.rowAt(event.y())
        if column_index != -1 and row_index != -1:
            menu = QMenu(self)
            menu.addAction(self.nodes_widget.actionHighlightSelectedNodes)
            menu.addAction(self.nodes_widget.actionViewSpectrum)
            menu.addAction(self.nodes_widget.actionViewCompareSpectrum)
            menu.addSeparator()
            menu.addAction(self.nodes_widget.actionFindStandards)
            menu.addAction(self.nodes_widget.actionFindAnalogs)
            # menu.addSeparator()
            # menu.addAction(self.nodes_widget.actionMetFrag)
            # menu.addAction(self.nodes_widget.actionCFMID)
            menu.popup(QCursor.pos())

    @debug
    def on_edges_table_contextmenu(self, event):
        column_index = self.tvEdges.columnAt(event.x())
        row_index = self.tvEdges.rowAt(event.y())
        if column_index != -1 and row_index != -1:
            menu = QMenu(self)
            menu.addAction(self.edges_widget.actionHighlightSelectedEdges)
            menu.addAction(self.edges_widget.actionHighlightNodesFromSelectedEdges)
            menu.popup(QCursor.pos())

    @debug
    def on_view_contextmenu(self, pos):
        view = self.sender()
        item = view.itemAt(pos)
        if item and item.isSelected():
            menu = QMenu(view)
            menu.addAction(self.actionViewSpectrum)
            menu.addAction(self.actionViewCompareSpectrum)
            menu.addSeparator()
            menu.addAction(self.actionFindStandards)
            menu.addAction(self.actionFindAnalogs)
            # menu.addSeparator()
            # menu.addAction(self.actionMetFrag)
            # menu.addAction(self.actionCFMID)
            menu.popup(view.mapToGlobal(pos))

    # noinspection PyUnusedLocal
    @debug
    def on_add_columns_by_formulae(self, *args):
        self._dialog = ui.AddColumnsByFormulaeDialog(self, model=self.tvNodes.model())

        def eval_fomulae(result):
            if result == QDialog.Accepted:
                alias, mappings = self._dialog.getValues()
                df = self._network.infos
                df_resolver = {k: df[v] for k, v in alias.items() if v in df.columns}

                # noinspection PyShadowingNames
                safe_dict = {
                            'sum': lambda *args: pd.DataFrame(args).sum(),
                            'mean': lambda *args: pd.DataFrame(args).mean(),
                            'median': lambda *args: pd.DataFrame(args).median(),
                            'prod': lambda *args: pd.DataFrame(args).prod(),
                            'std': lambda *args: pd.DataFrame(args).std(),
                            'var': lambda *args: pd.DataFrame(args).var(),
                            'quantile': lambda q, *args: pd.DataFrame(args).quantile(q),
                            'min': lambda *args: pd.DataFrame(args).min(),
                            'max': lambda *args: pd.DataFrame(args).max(),
                            'pi': np.pi, 'e': np.e,
                            'int': lambda *args: pd.DataFrame(args).fillna(0).astype(int).squeeze(),
                            'float': lambda *args: pd.DataFrame(args).astype(float).squeeze(),
                            'bool': lambda *args: pd.DataFrame(args).astype(bool).squeeze(),
                            'fillna': lambda v, *args: pd.DataFrame(args).fillna(v).squeeze(),
                             }

                self.tvNodes.sourceModel().beginResetModel()
                # noinspection PyShadowingNames
                errors = {}
                for name, mapping in mappings.items():
                    try:
                        df.eval('{} = {}'.format(name, mapping), resolvers=[df_resolver, safe_dict], inplace=True,
                                engine='numexpr')
                    except (TypeError, NotImplementedError):
                        try:
                            # Fallback to Python engine
                            df.eval('{} = {}'.format(name, mapping), resolvers=[df_resolver, safe_dict], inplace=True,
                                    engine='python')
                        except (pd.core.computation.ops.UndefinedVariableError, AttributeError, SyntaxError) as e:
                            errors[name] = e
                    except (pd.core.computation.ops.UndefinedVariableError, AttributeError, SyntaxError) as e:
                        errors[name] = e

                self.check_columns_mappings_after_data_changed(set(mappings.keys()))
                self.tvNodes.sourceModel().endResetModel()

                if errors:
                    str_errors = '\n'.join([f'"{name}" -> {error}' for (name, error) in errors.items()])
                    QMessageBox.warning(self, None, f'The following error(s) occurred:\n\n{str_errors}')

                self.has_unsaved_changes = True

        self._dialog.finished.connect(eval_fomulae)
        self._dialog.open()

    # noinspection PyUnusedLocal
    @debug
    def on_clusterize(self, *args):
        if not workers_core.ClusterizeWorker.enabled():
            QMessageBox.information(self, None,
                                    ('hdbscan is required for this action '
                                     '(https://hdbscan.readthedocs.io).'))
            return
        elif getattr(self.network, 'scores') is None:
            QMessageBox.warning(self, None, 'Please import spectra first.')
            return

        docks = self.network_docks.items()
        if not docks:
            QMessageBox.warning(self, None, 'Please add a view first.')
            return
        self._dialog = ui.ClusterizeDialog(self, views={k: f"{v.widget().title} ({v.widget().short_id})"
                                                        for k, v in docks})

        def do_clustering(result):
            if result == QDialog.Accepted:
                # noinspection PyShadowingNames
                def update_dataframe(worker: workers_core.ClusterizeWorker):
                    self.tvNodes.sourceModel().beginResetModel()
                    self.network.infos[options.column_name] = data = worker.result()
                    self.tvNodes.sourceModel().endResetModel()

                    column_index = self.network.infos.columns.get_loc(options.column_name)
                    self.tvNodes.setColumnBlinking(column_index + 2, True)
                    QMessageBox.information(self, None, f"Found {len(set(data)) - 1} clusters.")

                name, options = self._dialog.getValues()
                widget = self.network_docks[name].widget()
                worker = workers_core.ClusterizeWorker(widget, options)
                if worker is not None:
                    self._workers.append(worker)
                    self._workers.append(update_dataframe)
                    self._workers.start()

        self._dialog.finished.connect(do_clustering)
        self._dialog.open()

    @debug
    def on_numberize(self, *args):
        docks = self.network_docks.items()
        if not docks:
            QMessageBox.warning(self, None, 'Please add a view first.')
            return
        self._dialog = ui.NumberizeDialog(self, views={k: f"{v.widget().title} ({v.widget().short_id})"
                                                    for k, v in docks if v.widget().name == widgets.NetworkFrame.name})

        def do_numbering(result):
            if result == QDialog.Accepted:
                # noinspection PyShadowingNames
                def update_dataframe(worker: workers_core.ClusterizeWorker):
                    self.tvNodes.sourceModel().beginResetModel()
                    self.network.infos[options.column_name] = data = worker.result()
                    self.tvNodes.sourceModel().endResetModel()

                    column_index = self.network.infos.columns.get_loc(options.column_name)
                    self.tvNodes.setColumnBlinking(column_index + 2, True)
                    QMessageBox.information(self, None, f"Found {np.unique(data).size} clusters.")

                name, options = self._dialog.getValues()
                widget = self.network_docks[name].widget()
                worker = workers_core.NumberizeWorker(widget, options)
                if worker is not None:
                    self._workers.append(worker)
                    self._workers.append(update_dataframe)
                    self._workers.start()

        self._dialog.finished.connect(do_numbering)
        self._dialog.open()

    @debug
    def on_filter(self):
        self._dialog = ui.FilterDialog(self)

        def do_filter(result):
            if result == QDialog.Accepted:
                def set_filter(worker: workers_core.FilterWorker):
                    result = worker.result()
                    if not result:
                        QMessageBox.warning(self, None, 'No node matched the given conditions.')
                        return
                    self.tvNodes.model().setSelection(result)

                values, condition_criterium = self._dialog.getValues()
                worker = workers_core.FilterWorker(self._network.mzs, self._network.spectra,
                                                   values, condition_criterium)
                if worker is not None:
                    self._workers.append(worker)
                    self._workers.append(set_filter)
                    self._workers.start()
        self._dialog.finished.connect(do_filter)
        self._dialog.open()

    # noinspection PyUnusedLocal
    @debug
    def on_delete_nodes_columns(self, *args):
        if self.tvNodes.model().columnCount() <= 1:
            return

        df = self._network.infos
        if df is None:
            return

        selected_columns_indexes = self.tvNodes.selectionModel().selectedColumns(0)
        len_ = len(selected_columns_indexes)

        if len_ == 0:
            return

        message = f"Are you sure you want to delete {'this column' if len_ == 1 else 'these columns'}?"
        reply = QMessageBox.question(self, None, message)
        if reply == QMessageBox.No:
            return

        model = self.tvNodes.sourceModel()
        num_columns = model.columnCount()
        model.beginResetModel()
        column_names = set([model.headerData(index.column(), Qt.Horizontal, metadata.KeyRole)
                            for index in selected_columns_indexes])

        # Remove columns that are not group mappings
        if hasattr(self._network, 'mappings'):
            df_cols = column_names - self.network.mappings.keys()

            # Remove group mappings columns if any
            for col in column_names - df_cols:
                self.network.mappings.pop(col)
        else:
            df_cols = column_names

        df.drop(df_cols, axis=1, inplace=True, errors='ignore')

        model.endResetModel()

        if model.columnCount() < num_columns:
            self.has_unsaved_changes = True

    # noinspection PyUnusedLocal
    @debug
    def on_show_spectrum(self, *args):
        indexes = self.tvNodes.selectedIndexes()
        if not indexes:
            return

    # noinspection PyUnusedLocal
    @debug
    def on_nodes_table_data_changed(self, *args):
        self.has_unsaved_changes = True

    @debug
    def on_nodes_table_column_moved(self, logical_index: int, old_visual_index: int, new_visual_index: int):
        self.has_unsaved_changes = True

        # Cancel movement for columns not in the nodes' dataframe
        model = self.tvNodes.sourceModel()
        key = model.headerData(logical_index, Qt.Horizontal, metadata.KeyRole)
        if isinstance(key, int):
            with SignalBlocker(self.tvNodes.horizontalHeader()):
                self.tvNodes.horizontalHeader().moveSection(new_visual_index, old_visual_index)

    @debug
    def on_query_databases(self, type_='standards', selected_idx=None):
        if selected_idx is None:
            selected_idx = self.nodes_selection()

        if not selected_idx:
            return
        options = workers_opts.QueryDatabasesOptions()
        options.analog_search = (type_ == 'analogs')

        try:
            self._dialog = ui.QueryDatabasesDialog(self, options=options)

            def do_query(result):
                if result == QDialog.Accepted:
                    # noinspection PyShadowingNames
                    options = self._dialog.getValues()
                    worker = self.prepare_query_database_worker(selected_idx, options)
                    if worker is not None:
                        self._workers.append(worker)
                        self._workers.start()

            self._dialog.finished.connect(do_query)
            self._dialog.open()
        except FileNotFoundError:
            QMessageBox.warning(self, None, "No database found. Please download at least one database.")

    # noinspection PyUnusedLocal
    @debug
    def on_query_in_silico_db(self, type_='metfrag', selected_idx=None):
        dialog_class = {'metfrag': ui.MetFragDialog, 'cfm-id': ui.CFMIDDialog}.get(type_, None)
        if dialog_class is None:
            return

        if selected_idx is None:
            selected_idx = self.nodes_selection()

        if not selected_idx:
            return

        if self.network.mzs is not None:
            mz = self.network.mzs.iloc[list(selected_idx)[0]]
        else:
            QMessageBox.warning(self, None,
                                "Insilico Databases are only available for MS/MS spectra.")
            return
        spectrum = human_readable_data(self.network.spectra[self.network.mzs.index[list(selected_idx)[0]]])

        self._dialog = dialog_class(self, mz, spectrum)

        def store_result():
            print(self._dialog.getValues())
        self._dialog.finished.connect(store_result)
        self._dialog.open()

    # noinspection PyUnusedLocal
    @debug
    def on_current_parameters_triggered(self, *args):
        if hasattr(self._network.options, workers_opts.CosineComputationOptions.name):
            self._dialog = ui.CurrentParametersDialog(self, options=self.network.options)
            self._dialog.open()

    # noinspection PyUnusedLocal
    @debug
    def on_preferences_triggered(self, *args):
        self._dialog = ui.SettingsDialog(self)

        def set_preferences(result):
            if result == QDialog.Accepted:
                self.style = self._dialog.getValues()

        self._dialog.finished.connect(set_preferences)
        self._dialog.open()

    # noinspection PyUnusedLocal
    @debug
    def on_full_screen_triggered(self, *args):
        if not self.isFullScreen():
            self.setWindowFlags(Qt.Window)
            self.showFullScreen()
        else:
            self.setWindowFlags(Qt.Widget)
            self.showNormal()

    # noinspection PyUnusedLocal
    @debug
    def on_show_plugins_manager_triggered(self, *args):
        self._dialog = ui.PluginsManagerDialog(self)
        self._dialog.open()

    # noinspection PyUnusedLocal
    @debug
    def on_process_file_triggered(self, *args):
        reply = self.confirm_save_changes()
        if reply == QMessageBox.Cancel:
            return

        self._dialog = ui.ProcessDataDialog(self._create_network_button.menu(), self,
                                            options=self.network.options)

        def do_process(result):
            if result == QDialog.Accepted:
                def create_compute_scores_worker(worker: workers_core.ReadDataWorker):
                    self.tvNodes.model().setSelection([])
                    self.tvNodes.sourceModel().beginResetModel()
                    self._network.mzs, self._network.spectra = worker.result()
                    self.tvNodes.sourceModel().endResetModel()
                    mzs = self.network.mzs
                    if mzs is None:
                        mzs = np.zeros((len(self.network.spectra),), dtype=int)
                    return self.prepare_compute_scores_worker(mzs, self.network.spectra)

                def store_scores(worker: workers_core.ComputeScoresWorker):
                    self.tvEdges.model().setSelection([])
                    scores = worker.result()
                    if not isinstance(scores, np.ndarray):
                        return

                    self._network.scores = scores

                    self.tvNodes.setColumnHidden(1, self.network.db_results is None
                                                 or len(self.network.db_results) == 0)
                    self.dock_edges.toggleView(True)
                    self.dock_nodes.toggleView(True)

                self.reset_project()

                process_file, use_metadata, metadata_file, metadata_options, options, views = self._dialog.getValues()

                self._network.options = options
                self._workers.append(self.prepare_read_data_worker(process_file))
                self._workers.append(create_compute_scores_worker)
                self._workers.append(store_scores)
                if use_metadata:
                    self._workers.append(self.prepare_read_metadata_worker(metadata_file, metadata_options))

                for id_ in views:
                    try:
                        name = id_.split('_')[0]
                        widget_class = widgets.AVAILABLE_NETWORK_WIDGETS[name]
                    except (KeyError, IndexError):
                        pass
                    else:
                        if widget_class is not None:
                            widget = self.add_network_widget(widget_class, id_=id_)
                            if widget is not None:
                                if widget.name == widgets.NetworkFrame.name:
                                    self._workers.append(lambda _, w=widget: self.prepare_generate_network_worker(w))
                                self._workers.append(lambda _, w=widget: w.create_draw_worker())
                                self._workers.append(lambda _: self.update_status_widgets())

                self._workers.append(self.update_status_widgets)

                self._workers.start()

        self._dialog.finished.connect(do_process)
        self._dialog.open()

    # noinspection PyUnusedLocal
    @debug
    def on_import_metadata_triggered(self, *args):
        self._dialog = ui.ImportMetadataDialog(self)

        def do_import(result):
            if result == QDialog.Accepted:
                metadata_filename, options = self._dialog.getValues()
                worker = self.prepare_read_metadata_worker(metadata_filename, options)
                if worker is not None:
                    self._workers.append(worker)
                    self._workers.start()

        self._dialog.finished.connect(do_import)
        self._dialog.open()

    # noinspection PyUnusedLocal
    @debug
    def on_import_group_mapping_triggered(self, *args):
        self._dialog = QFileDialog(self)
        self._dialog.setFileMode(QFileDialog.ExistingFile)
        self._dialog.setNameFilters(["Text Files (*.txt *.csv *.tsv)", "All files (*)"])

        def do_import(result):
            if result == QDialog.Accepted:
                filename = self._dialog.selectedFiles()[0]
                worker = self.prepare_read_group_mapping_worker(filename)
                if worker is not None:
                    self._workers.append(worker)
                    self._workers.start()

        self._dialog.finished.connect(do_import)
        self._dialog.open()

    # noinspection PyUnusedLocal
    @debug
    def on_add_view_triggered(self, *args):
        if hasattr(self._network, 'scores'):
            action = self.sender()
            widget_class = action.data()
            if widget_class is not None:
                options = self._network.options.get(widget_class.name, {})
                self._dialog = widget_class.dialog_class(self, options=options)

                def add_view(result):
                    if result == QDialog.Accepted:
                        # noinspection PyShadowingNames
                        options = self._dialog.getValues()
                        widget = self.add_network_widget(widget_class)
                        self._network.options[widget.id] = options
                        self.has_unsaved_changes = True

                        if widget is not None:
                            if widget.name == widgets.NetworkFrame.name:
                                self._workers.append(lambda _: self.prepare_generate_network_worker(widget))
                            self._workers.append(lambda _: widget.create_draw_worker())
                            self._workers.append(lambda _: self.update_status_widgets())
                            self._workers.start()

                def error_import_modules(e):
                    if isinstance(e, ImportError):
                        # One or more dependencies could not be loaded, disable action associated with the view
                        actions = list(enumerateMenu(self._create_network_button.menu()))
                        for action in actions:
                            if action.data() == widget_class:
                                action.setEnabled(False)  # Disable action

                                # Set a new default action
                                index = actions.index(action)
                                default = actions[(index+1) % len(actions)]
                                self._create_network_button.setDefaultAction(default)
                                break

                        QMessageBox.warning(self, None,
                            f"{widget_class.title} view can't be added because a requested module can't be loaded.")

                self._dialog.finished.connect(add_view)
                worker = workers_core.ImportModulesWorker(widget_class.worker_class, widget_class.title)
                worker.error.connect(error_import_modules)
                worker.finished.connect(self._dialog.open)
                self._workers.append(worker)
                self._workers.start()

    @debug
    def on_edit_options_triggered(self, widget):
        if hasattr(self.network, 'scores'):
            options = self._network.options.get(widget.id, {})
            self._dialog = widget.dialog_class(self, options=options)

            def do_edit(result):
                if result == QDialog.Accepted:
                    new_options = self._dialog.getValues()
                    if new_options != options:
                        self._network.options[widget.id] = new_options

                        self.has_unsaved_changes = True

                        widget.reset_layout()
                        if widget.name == widgets.NetworkFrame.name:
                            widget.interactions = pd.DataFrame()
                            self._workers.append(lambda _: self.prepare_generate_network_worker(widget,
                                                                                                keep_vertices=True))
                        self._workers.append(lambda _: widget.create_draw_worker())
                        self._workers.append(lambda _: self.update_status_widgets())
                        self._workers.start()
                        self.update_search_menu()

            self._dialog.finished.connect(do_edit)
            self._dialog.open()
        else:
            QMessageBox.information(self, None, "No network found, please open a file first.")

    # noinspection PyUnusedLocal
    @debug
    def on_download_databases_triggered(self, *args):
        self._dialog = ui.DownloadDatabasesDialog(self, base_path=config.DATABASES_PATH)
        self._dialog.open()

    # noinspection PyUnusedLocal
    @debug
    def on_import_user_database_triggered(self, *args):
        self._dialog = ui.ImportUserDatabaseDialog(self, base_path=config.DATABASES_PATH)
        self._dialog.open()

    # noinspection PyUnusedLocal
    @debug
    def on_view_databases_triggered(self, *args):
        path = config.SQL_PATH
        if os.path.exists(path) and os.path.isfile(path) and os.path.getsize(path) > 0:
            try:
                self._dialog = ui.ViewDatabasesDialog(self, base_path=config.DATABASES_PATH)
            except (sqlalchemy.exc.OperationalError, sqlalchemy.exc.DatabaseError) as e:
                QMessageBox.warning(self, None, str(e))
            else:
                self._dialog.open()
        else:
            QMessageBox.information(self, None, "No databases found, please download one or more database first.")

    @debug
    def on_view_details_clicked(self, row: int, selection: dict):
        if selection:
            path = config.SQL_PATH
            if os.path.exists(path) and os.path.isfile(path) and os.path.getsize(path) > 0:
                spectrum = human_readable_data(self._network.spectra[self._network.mzs.index[row]])
                self._dialog = ui.ViewStandardsResultsDialog(self, mz_parent=self._network.mzs.iloc[row],
                                                             spectrum=spectrum, selection=selection,
                                                             base_path=config.DATABASES_PATH)

                def view_details(result):
                    if result == QDialog.Accepted:
                        current = self._dialog.getValues()
                        if current is not None:
                            self._network.db_results[row]['current'] = current
                            self.has_unsaved_changes = True

                self._dialog.finished.connect(view_details)
                self._dialog.open()
            else:
                QMessageBox.information(self, None, "No databases found, please download one or more database first.")

    @debug
    def on_set_annotations_mode(self, mode: int):
        for dock in self.network_docks.values():
            view = dock.widget().view()
            view.setDrawMode(mode)

    @debug
    def on_delete_selected_annotations(self, *args):
        view = self.current_view
        if view is not None:
            self.annotations_widget.beginResetModel()
            view.deleteSelectedAnnotations()
            self.annotations_widget.endResetModel()
            self.has_unsaved_changes = True

    @debug
    def on_clear_annotations(self, *args):
        view = self.current_view
        if view is not None and QMessageBox.question(self, "Clear annotations?",
                "Are you sure you want to clear annotations? This action cannot be undone.",
                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.annotations_widget.beginResetModel()
            view.scene().clearAnnotations()
            self.annotations_widget.endResetModel()
            self.has_unsaved_changes = True

    @debug
    def on_undo_annotations(self, *args):
        view = self.current_view
        if view is not None:
            self.annotations_widget.beginResetModel()
            view.undoStack().undo()
            self.annotations_widget.endResetModel()
            self.has_unsaved_changes = True

    @debug
    def on_redo_annotations(self, *args):
        view = self.current_view
        if view is not None:
            self.annotations_widget.beginResetModel()
            view.undoStack().redo()
            self.annotations_widget.endResetModel()
            self.has_unsaved_changes = True

    @debug
    def on_arrow_edited(self, *args):
        self.annotations_widget.beginResetModel()
        self.annotations_widget.endResetModel()

    @debug
    def on_annotations_added(self, *args):
        self.dock_annotations.toggleView(True)
        self.annotations_widget.beginResetModel()
        self.annotations_widget.endResetModel()

    @debug
    def on_undo_stack_clean_changed(self, clean: bool):
        self.has_unsaved_changes = not clean

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

    # noinspection PyUnusedLocal
    @debug
    def highlight_selected_nodes(self, *args):
        selected = self.nodes_selection()
        for dock in self.network_docks.values():
            scene = dock.widget().scene()
            with SignalBlocker(scene):
                scene.setNodesSelection(list(selected))

    # noinspection PyUnusedLocal
    @debug
    def highlight_selected_edges(self, *args):
        selected = self.edges_selection()
        for dock in self.network_docks.values():
            scene = dock.widget().scene()
            with SignalBlocker(scene):
                scene.setEdgesSelection(list(selected))

    # noinspection PyUnusedLocal
    @debug
    def highlight_nodes_from_selected_edges(self, *args):
        selected = self.edges_selection()
        model = self.tvEdges.sourceModel()
        sel = []
        for row in selected:
            source = model.index(row, 0).data(metadata.ColumnDataRole) - 1
            dest = model.index(row, 1).data(metadata.ColumnDataRole) - 1
            sel.append(source)
            sel.append(dest)

        for dock in self.network_docks.values():
            scene = dock.widget().scene()
            with SignalBlocker(scene):
                scene.setNodesSelection(sel)

    def add_network_widget(self, widget_class, id_=None, graph=None, interactions=None):
        if id_ is None:
            id_ = generate_id(widget_class.name)

        widget = widget_class(id_, self.network, graph, interactions)
        view = widget.view()
        scene = widget.scene()
        if not isinstance(self.style, DefaultStyle):
            scene.setNetworkStyle(self.style)
        scene.selectionChanged.connect(lambda sc=scene: self.on_scene_selection_changed(sc))
        scene.annotationAdded.connect(self.on_annotations_added)
        scene.arrowEdited.connect(self.on_arrow_edited)
        view.focusedIn.connect(lambda sc=scene: self.on_scene_selection_changed(sc, update_view=False))
        view.undoStack().cleanChanged.connect(self.on_undo_stack_clean_changed)
        view.setContextMenuPolicy(Qt.CustomContextMenu)
        view.customContextMenuRequested.connect(self.on_view_contextmenu)
        scene.pieChartsVisibilityChanged.connect(
            lambda visibility: self.actionSetPieChartsVisibility.setChecked(visibility))
        widget.btOptions.clicked.connect(lambda: self.on_edit_options_triggered(widget))

        dock = CDockWidget(f"{widget.title} ({widget.short_id})")
        dock.setFeature(CDockWidget.CustomCloseHandling, True)
        dock.setFeature(CDockWidget.DockWidgetDeleteOnClose, True)
        dock.setFeature(CDockWidget.DockWidgetForceCloseWithArea, True)
        dock.setWidget(widget)
        self.dock_manager.addDockWidget(LeftDockWidgetArea, dock, self.dock_placeholder.dockAreaWidget())
        dock.toggleView(False)
        self.dock_placeholder.toggleView(False)
        dock.closeRequested.connect(self._docks_closed_signals_grouper.accumulate)
        dock.toggleView(True)
        self.dock_manager.addToggleViewActionToMenu(dock.toggleViewAction())
        self.network_docks[widget.id] = dock
        # noinspection PyAttributeOutsideInit
        self._default_state = self.dock_manager.saveState()
        self.btUndoAnnotations.setMenu(widget.view().undoMenu())

        return widget

    @debug
    def on_network_widget_closed(self, docks):
        if not docks:
            return

        num_docks = len(docks)
        if num_docks == 1:
            dock = next(iter(docks))
            message = f"Delete {dock.objectName()} view?"
        else:
            message = f"Delete these {num_docks} views?\n"
            message += ", ".join([dock.widget().id for dock in docks])
        msgbox = QMessageBox(QMessageBox.Question,
                             QCoreApplication.applicationName(),
                             message,
                             QMessageBox.Yes | QMessageBox.Cancel,
                             self)
        msgbox.addButton(f"No, just hide {'it' if num_docks==1 else 'them'}", QMessageBox.NoRole)
        result = msgbox.exec_()
        if result == QMessageBox.Yes:
            for dock in docks:
                self.dock_manager.viewMenu().removeAction(dock.toggleViewAction())
                self.dock_manager.removeDockWidget(dock)
                self.network_docks.pop(dock.widget().id)
                del self._network.options[dock.widget().id]
            self.has_unsaved_changes = True
        elif result != QMessageBox.Cancel:
            for dock in docks:
                dock.toggleView(False)

    @debug
    def set_nodes_label(self, column_id: int = None, column_key: Union[int, str] = None):
        model = self.tvNodes.sourceModel()
        for column in range(model.columnCount()):
            font = model.headerData(column, Qt.Horizontal, role=Qt.FontRole)
            if font is not None and font.overline():
                model.setHeaderData(column, Qt.Horizontal, None, role=Qt.FontRole)

        if column_key is not None:
            if isinstance(column_key, str):
                column_id = model.headerKeysToIndices([column_key])
                column_id = column_id[0] if column_id else None
            else:
                column_id = column_key

        if column_id is not None:
            font = model.headerData(column_id, Qt.Horizontal, role=Qt.FontRole)
            font = font if font is not None else QFont()
            font.setOverline(True)
            model.setHeaderData(column_id, Qt.Horizontal, font, role=Qt.FontRole)

            for dock in self.network_docks.values():
                scene = dock.widget().scene()
                scene.setLabelsFromModel(model, column_id, metadata.LabelRole)
            self._network.columns_mappings['label'] = model.headerData(column_id, Qt.Horizontal,
                                                                      role=metadata.KeyRole)
        else:
            for dock in self.network_docks.values():
                dock.widget().scene().resetLabels()

            try:
                del self._network.columns_mappings['label']
            except KeyError:
                pass

        self.has_unsaved_changes = True

    @debug
    def set_nodes_pie_chart_values(self, column_ids: List[int] = None, colors: List[Union[QColor, str]] = [],
                                   column_keys: List[Union[int, str]] = None):
        model = self.tvNodes.sourceModel()

        if column_keys is not None and len(column_keys) > 0:
            if hasinstance(column_keys, str):
                column_ids = model.headerKeysToIndices(column_keys)
            else:
                column_ids = column_keys

        if column_ids is not None:
            if len(colors) < len(column_ids):
                QMessageBox.critical(self, None, "There is more columns selected than colors available.")
                return

            for column in range(model.columnCount()):
                model.setHeaderData(column, Qt.Horizontal, None, role=metadata.ColorMarkRole)

            # Make sure that colors is a list of QColor
            colors = [QColor(color) for color in colors]

            save_colors = []
            for column, color in zip(column_ids, colors):
                save_colors.append(color)
                model.setHeaderData(column, Qt.Horizontal, color, role=metadata.ColorMarkRole)

            for dock in self.network_docks.values():
                scene = dock.widget().scene()
                scene.setPieColors(colors)
                scene.setPieChartsFromModel(model, column_ids)
                scene.setPieChartsVisibility(True)

            keys = [model.headerData(id_, Qt.Horizontal, role=metadata.KeyRole) for id_ in column_ids]
            self._network.columns_mappings['pies'] = (keys, save_colors)
        else:
            for column in range(model.columnCount()):
                model.setHeaderData(column, Qt.Horizontal, None, role=metadata.ColorMarkRole)

            for dock in self.network_docks.values():
                dock.widget().scene().resetPieCharts()

            try:
                del self._network.columns_mappings['pies']
            except KeyError:
                pass

        self.has_unsaved_changes = True

    @debug
    def set_nodes_sizes_values(self, column_id: int = None, func: Callable = None,
                               column_key: Union[int, str] = None):
        model = self.tvNodes.sourceModel()

        for column in range(model.columnCount()):
            font = model.headerData(column, Qt.Horizontal, role=Qt.FontRole)
            if font is not None and font.underline():
                model.setHeaderData(column, Qt.Horizontal, None, role=Qt.FontRole)

        if column_key is not None:
            if isinstance(column_key, str):
                column_id = model.headerKeysToIndices([column_key])
                column_id = column_id[0] if column_id else None
            else:
                column_id = column_key

        if column_id is not None:
            font = model.headerData(column_id, Qt.Horizontal, role=Qt.FontRole)
            font = font if font is not None else QFont()
            font.setUnderline(True)
            model.setHeaderData(column_id, Qt.Horizontal, font, role=Qt.FontRole)

            for dock in self.network_docks.values():
                dock.widget().scene().setNodesRadiiFromModel(model, column_id, func, Qt.DisplayRole)

            key = model.headerData(column_id, Qt.Horizontal, role=metadata.KeyRole)
            self._network.columns_mappings['size'] = (key, func)
        else:
            for dock in self.network_docks.values():
                dock.widget().scene().resetNodesRadii()

            try:
                del self._network.columns_mappings['size']
            except KeyError:
                pass

        self.has_unsaved_changes = True

    @debug
    def set_nodes_colors_values(self, column_id: int = None,
                                mapping: Union[Dict[str, Tuple[QColor, NodePolygon]],
                                               Tuple[List[float], List[QColor], List[NodePolygon]]] = {},
                                column_key: Union[int, str] = None):
        model = self.tvNodes.sourceModel()
        for column in range(model.columnCount()):
            font = model.headerData(column, Qt.Horizontal, role=Qt.FontRole)
            if font is not None and font.italic():
                model.setHeaderData(column, Qt.Horizontal, None, role=Qt.FontRole)

        if column_key is not None:
            if isinstance(column_key, str):
                column_id = model.headerKeysToIndices([column_key])
                column_id = column_id[0] if column_id else None
            else:
                column_id = column_key

        if column_id is not None:
            font = model.headerData(column_id, Qt.Horizontal, role=Qt.FontRole)
            font = font if font is not None else QFont()
            font.setItalic(True)
            model.setHeaderData(column_id, Qt.Horizontal, font, role=Qt.FontRole)

            key = model.headerData(column_id, Qt.Horizontal, metadata.KeyRole)
            data = model.headerData(column_id, Qt.Horizontal, metadata.ColumnDataRole)
            if data is None:
                return

            if isinstance(mapping, dict):
                color_list, polygon_list, brush_list = zip(*[mapping.get(k, (QColor(), NodePolygon.Circle, Qt.NoBrush))
                                                             for k in data])
                polygon_list = [x.value if isinstance(x, NodePolygon) else x for x in polygon_list]
                brush_list = [QBrush(_) for _ in brush_list]
            elif isinstance(mapping, (tuple, list)):
                try:
                    bins, colors, polygons, styles = mapping
                except TypeError:
                    return

                # noinspection PyShadowingNames
                def r(ranges, colors, polygons, styles, val):
                    if val == ranges[-1]:
                        return colors[-1], polygons[-1], styles[-1]

                    b = bisect.bisect_left(ranges, val)
                    try:
                        return colors[b-1], polygons[b-1], styles[b-1]
                    except IndexError:
                        return QColor(), NodePolygon.Circle, Qt.NoBrush

                color_list, polygon_list, brush_list = [], [], []
                for value in data:
                    c, p, s = r(bins, colors, polygons, styles, value)
                    color_list.append(c)
                    polygon_list.append(p)
                    brush_list.append(QBrush(s))
            else:
                return

            for dock in self.network_docks.values():
                dock.widget().scene().setNodesColors(color_list)
                dock.widget().scene().setNodesPolygons(polygon_list)
                dock.widget().scene().setNodesOverlayBrushes(brush_list)

            self._network.columns_mappings['colors'] = (key, mapping)
        else:
            for dock in self.network_docks.values():
                scene = dock.widget().scene()
                color = scene.networkStyle().nodeBrush().color()
                scene.setNodesColors([color for _ in scene.nodes()])
                scene.setNodesPolygons([NodePolygon.Circle.value for _ in scene.nodes()])
                scene.setNodesOverlayBrushes([QBrush(Qt.NoBrush) for _ in scene.nodes()])

            try:
                del self._network.columns_mappings['colors']
            except KeyError:
                pass

        self.has_unsaved_changes = True

    @debug
    def set_nodes_pixmaps_values(self, column_id: int = None,
                                column_key: Union[int, str] = None,
                                type_: int = widgets.AnnotationsNetworkScene.PixmapsAuto):
        model = self.tvNodes.sourceModel()
        for column in range(model.columnCount()):
            font = model.headerData(column, Qt.Horizontal, role=Qt.FontRole)
            if font is not None and font.bold():
                model.setHeaderData(column, Qt.Horizontal, None, role=Qt.FontRole)

        if column_key is not None:
            if isinstance(column_key, str):
                column_id = model.headerKeysToIndices([column_key])
                column_id = column_id[0] if column_id else None
            else:
                column_id = column_key

        if column_id is not None:
            font = model.headerData(column_id, Qt.Horizontal, role=Qt.FontRole)
            font = font if font is not None else QFont()
            font.setBold(True)
            model.setHeaderData(column_id, Qt.Horizontal, font, role=Qt.FontRole)

            for dock in self.network_docks.values():
                scene = dock.widget().scene()
                scene.setPixmapsFromModel(model, column_id, Qt.DisplayRole, type_)
            self._network.columns_mappings['pixmap'] = (model.headerData(column_id, Qt.Horizontal,
                                                                        role=metadata.KeyRole),
                                                        type_)
        else:
            for dock in self.network_docks.values():
                dock.widget().scene().resetPixmaps()

            try:
                del self._network.columns_mappings['pixmap']
            except KeyError:
                pass

        self.has_unsaved_changes = True

    @debug
    def save_settings(self):
        settings = QSettings()

        settings.beginGroup('MainWindow')
        settings.setValue('Geometry', self.saveGeometry())
        settings.setValue('State', self.saveState())
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
        self.recent_projects = settings.value('RecentProjects')
        if self.recent_projects is None:
            self.recent_projects = []
        self.update_recent_projects()
        settings.endGroup()

        settings.beginGroup('NetworkView')
        setting = settings.value('style', None)
        style = style_from_css(setting)
        if style is not None:
            font_size = settings.value('style_font_size', None)
            if font_size is not None:
                font = style.nodeFont()
                font.setPointSize(font_size)
                style.setNodeFont(font)
        self.style = style

        settings.endGroup()

    @debug
    def check_for_updates(self, could_ignore=True, notify_if_no_update=False):
        def notify_update():
            nonlocal worker
            result = worker.result()

            if result:
                version, release_notes, url = result
                if could_ignore:
                    version_to_ignore = QSettings().value('Updates/ignore')
                    if version == version_to_ignore:
                        return

                self._dialog = ui.UpdatesDialog(self, version, release_notes, url)
                self._dialog.open()
            elif notify_if_no_update:
                QMessageBox.information(self, None,
                                        f"Your version of {QCoreApplication.applicationName()} is already up-to-date.")

        worker = workers_net.CheckUpdatesWorker(current_version=QCoreApplication.applicationVersion(),
                                                track_progress=notify_if_no_update)
        worker.finished.connect(notify_update)
        self._workers.append(worker)
        self._workers.start()

    # noinspection PyUnusedLocal
    @debug
    def reset_layout(self, *args):
        # Move all docks to default areas
        dock_area = None
        for dock in self.dock_manager.dockWidgetsMap().values():
            if dock.objectName() == 'placeholder':
                pass
            elif dock.objectName() == 'jupyter':
                self.dock_manager.addDockWidget(TopDockWidgetArea, dock)
            elif hasattr(dock.widget(), 'view'):
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
    def check_columns_mappings_after_data_changed(self, updated_columns_keys: set):
        # Check if one of the updated columns is in the columns mappings
        # Check only size and colors because these mappings needs data dependent info to be created
        key, _ = self._network.columns_mappings.get('size', (None, None))
        if key in updated_columns_keys:
            try:
                del self._network.columns_mappings['size']
            except KeyError:
                pass
        key, _ = self._network.columns_mappings.get('colors', (None, None))
        if key in updated_columns_keys:
            try:
                del self._network.columns_mappings['colors']
            except KeyError:
                pass

    @debug
    def update_columns_mappings(self, force_reset_mapping=True):
        columns_mappings = getattr(self.network, 'columns_mappings', {})

        try:
            key = columns_mappings.get('label', None)
        except TypeError:
            if force_reset_mapping:
                self.set_nodes_label(None)
        else:
            if key is not None:
                self.set_nodes_label(column_key=key)
            else:
                self.set_nodes_label(None)

        try:
            keys, colors = columns_mappings.get('pies', (None, None))
        except TypeError:
            if force_reset_mapping:
                self.set_nodes_pie_chart_values(None)
        else:
            if keys is not None and colors is not None:
                self.set_nodes_pie_chart_values(column_keys=keys, colors=colors)
            else:
                self.set_nodes_pie_chart_values(None)

        try:
            key, func = columns_mappings.get('size', (None, None))
        except TypeError:
            if force_reset_mapping:
                self.set_nodes_sizes_values(None)
        else:
            if key is not None and func is not None:
                self.set_nodes_sizes_values(column_key=key, func=func)
            elif force_reset_mapping:
                self.set_nodes_sizes_values(None)

        try:
            key, colors = columns_mappings.get('colors', (None, None))
        except TypeError:
            if force_reset_mapping:
                self.set_nodes_colors_values(None)
        else:
            if key is not None and colors is not None:
                self.set_nodes_colors_values(column_key=key, mapping=colors)
            elif force_reset_mapping:
                self.set_nodes_colors_values(None)

        try:
            key, type_ = columns_mappings.get('pixmap', (None, None))
        except TypeError:
            if force_reset_mapping:
                self.set_nodes_pixmaps_values(None)
        else:
            if key is not None and type_ is not None:
                self.set_nodes_pixmaps_values(column_key=key, type_=type_)
            else:
                self.set_nodes_pixmaps_values(None)

    @debug
    def prepare_compute_scores_worker(self, mzs, spectra):
        def error(e):
            if isinstance(e, OSError):
                QMessageBox.warning(self, None, str(e))
            elif isinstance(e, MemoryError):
                QMessageBox.critical(self, None, "Not enough memory was available to compute scores matrix.")
            else:
                raise e

        worker = workers_core.ComputeScoresWorker(mzs, spectra, self._network.options.cosine)
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
            elif isinstance(e, workers_core.FileEmptyError):
                QMessageBox.warning(self, None, "Datafile is empty!")
            elif isinstance(e, workers_core.NoSpectraError):
                QMessageBox.warning(self, None, "No more spectra left after filtering.")
            elif hasattr(e, 'message'):
                QMessageBox.warning(self, None, e.message)
            else:
                QMessageBox.warning(self, None, str(e))

        worker = workers_core.ReadDataWorker(mgf_filename, self._network.options.cosine)
        worker.error.connect(error)

        return worker

    @debug
    def prepare_generate_network_worker(self, widget, keep_vertices=False):
        options = self._network.options.get(widget.id, None)
        if options is None:
            return

        mzs = self._network.mzs
        if mzs is None:
            mzs = np.zeros(self._network.scores.shape[:1], dtype=int)

        worker = workers_core.GenerateNetworkWorker(self._network.scores, mzs, widget.graph,
                                                    options, keep_vertices=keep_vertices)

        if options.max_connected_nodes > 0:
            # noinspection PyShadowingNames
            def create_max_connected_components_worker(worker: workers_core.GenerateNetworkWorker):
                interactions, graph = worker.result()
                widget.interactions = interactions
                return workers_core.MaxConnectedComponentsWorker(graph, options)

            # noinspection PyShadowingNames
            def store_interactions(worker: workers_core.MaxConnectedComponentsWorker):
                widget.graph = worker.result()

            return [worker, create_max_connected_components_worker, store_interactions]
        else:
            # noinspection PyShadowingNames
            def store_interactions(worker: workers_core.GenerateNetworkWorker):
                interactions, graph = worker.result()
                widget.interactions = interactions
                widget.graph = graph
            return [worker, store_interactions]

    @debug
    def prepare_read_metadata_worker(self, filename, options):
        def file_read():
            nonlocal worker
            model = self.tvNodes.sourceModel()
            model.beginResetModel()
            df = self._network.infos
            if df is not None and not df.empty:
                df2 = worker.result()
                df2_columns = set(df2.columns)
                df_columns = set(df.columns)
                new_columns = df2_columns - df_columns
                update_columns = df2_columns.intersection(df_columns)

                do_join = True
                if any(update_columns):
                    num_update_columns = len(update_columns)
                    if num_update_columns == 1:
                        message = f"'{next(iter(update_columns))}' already exists. Would you like to overwrite it?"
                        ret = QMessageBox.question(self, None, message,
                                                   QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
                    else:
                        msg = QMessageBox(self)
                        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
                        msg.setIcon(QMessageBox.Question)
                        msg.setText("Some columns already exist. Would you like to overwrite them?")
                        msg.setDetailedText("\n".join(update_columns))
                        msg.setWindowModality(Qt.ApplicationModal)
                        ret = msg.exec_()

                    if ret == QMessageBox.Yes:
                        df.update(df2[update_columns])
                        self.check_columns_mappings_after_data_changed(update_columns)
                    elif ret == QMessageBox.Cancel:
                        do_join = False

                if do_join and any(new_columns):
                    df = df.join(df2[new_columns])

                self._network.infos = df
            else:
                self._network.infos = worker.result()
            self.has_unsaved_changes = True
            model.endResetModel()

        def error(e):
            message = str(e).strip("\n")
            QMessageBox.warning(self, None, "Metadata were not imported because the following error occurred:\n"
                                            f"\"{message}\".\n"
                                            "Your metadata file might be corrupted/invalid.")

        worker = workers_core.ReadMetadataWorker(filename, options)
        worker.finished.connect(file_read)
        worker.error.connect(error)

        return worker

    @debug
    def prepare_save_project_worker(self, fname):
        """Save current project to a file for future access"""

        if not fname.endswith(config.FILE_EXTENSION):
            fname += config.FILE_EXTENSION

        def process_finished():
            # Save filename and set window title
            self.fname = fname
            self.has_unsaved_changes = False
            for widget in self.network_docks.values():
                if hasattr(widget, 'view'):
                    widget.view().undoStack().setClean()

            # Update list of recent projects
            self.update_recent_projects(fname)

        def error(e):
            if isinstance(e, PermissionError):
                QMessageBox.warning(self, None, str(e))
            else:
                raise e

        model = self.tvNodes.sourceModel()
        header = self.tvNodes.horizontalHeader()
        df = self._network.infos
        columns = [model.headerData(header.visualIndex(i), Qt.Horizontal, metadata.KeyRole)
                   for i in range(model.columnCount())]
        if df is not None:
            columns = [c for c in columns if c in df.columns]
            df = df.reindex(columns=columns)

        worker = workers_core.SaveProjectWorker(fname, self._network,
                                                df, self._network.options,
                                                layouts={d.widget().id: d.widget().get_layout_data() for d in
                                                         self.network_docks.values()},
                                                graphs={d.widget().id: d.widget().get_graph_data() for d in
                                                        self.network_docks.values()},
                                                annotations={d.widget().id: d.widget().get_annotations_data() for d in
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
            elif isinstance(e, workers_core.UnsupportedVersionError):
                QMessageBox.warning(self, None, str(e))
            elif isinstance(e, KeyError):
                QMessageBox.critical(self, None, str(e))
            elif isinstance(e, zipfile.BadZipFile):
                QMessageBox.warning(self, None,
                                    f"Selected file is not a valid {QCoreApplication.applicationName()} file")
            else:
                raise e

        worker = workers_core.LoadProjectWorker(fname)
        worker.error.connect(error)

        return worker

    @debug
    def prepare_query_database_worker(self, indices, options):
        if (getattr(self.network, 'mzs', None) is None or getattr(self.network, 'spectra', None) is None
                or not os.path.exists(config.SQL_PATH)):
            return

        if self._network.mzs is not None:
            mzs = [self.network.mzs.iloc[index] for index in indices]
        else:
            mzs = [0] * len(indices)
        spectra = [self._network.spectra[self._network.mzs.index[index]] for index in indices]
        worker = workers_dbs.QueryDatabasesWorker(indices, mzs, spectra, options)

        def query_finished():
            nonlocal worker
            result = worker.result()
            if result:
                self.tvNodes.sourceModel().beginResetModel()
                type_ = "analogs" if options.analog_search else "standards"
                # Update db_results with these new results
                num_results = 0
                for row in result:
                    if result[row][type_]:
                        num_results += len(result[row][type_])
                        if row in self._network.db_results:
                            self._network.db_results[row][type_] = result[row][type_]
                        else:
                            self._network.db_results[row] = {type_: result[row][type_]}
                    elif row in self._network.db_results and type_ in self._network.db_results[row]:
                        del self._network.db_results[row][type_]
                self.has_unsaved_changes = True
                self.tvNodes.sourceModel().endResetModel()

                # Show column if db_results is not empty
                was_hidden = self.tvNodes.isColumnHidden(1)
                self.tvNodes.setColumnBlinking(1, True)
                self.tvNodes.setColumnHidden(1, self._network.db_results is None or len(self._network.db_results) == 0)
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
        worker = workers_core.ReadGroupMappingWorker(filename)

        def finished():
            nonlocal worker
            result = worker.result()
            self.tvNodes.sourceModel().beginResetModel()
            if hasattr(self._network, 'mappings'):
                self._network.mappings.update(result)
            else:
                self._network.mappings = result
            self.has_unsaved_changes = True
            self.tvNodes.sourceModel().endResetModel()

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
    def prepare_export_metadata_worker(self, filename, model, sep, selected_rows):
        worker = workers_gui.ExportMetadataWorker(filename, model, sep, selected_rows if selected_rows else None)

        def finished():
            nnodes = len(selected_rows) if selected_rows else self.tvNodes.model().rowCount()
            QMessageBox.information(self, None,
                                    f"Metadata of {nnodes} nodes were successfully exported to \"{filename}\".")

        def error(e):
            if isinstance(e, workers_gui.NoDataError):
                QMessageBox.warning(self, None,
                                    "Metadata were not exported because there is nothing to export.")
            else:
                QMessageBox.warning(self, None,
                                    f"Metadata were not exported because the following error occurred: {str(e)})")

        worker.finished.connect(finished)
        worker.error.connect(error)
        return worker

    @debug
    def prepare_export_db_results_worker(self, filename: str, values,
                                         model: QAbstractTableModel, selected_rows) -> workers_gui.ExportDbResultsWorker:
        worker = workers_gui.ExportDbResultsWorker(filename, *values, config.DATABASES_PATH, model, selected_rows)

        def finished():
            nnodes = len(selected_rows) if selected_rows else self.tvNodes.model().rowCount()
            QMessageBox.information(self, None,
                                    f"Database results for {nnodes} nodes were successfully exported to \"{filename}\".")

        def error(e):
            if isinstance(e, workers_gui.NoDataError):
                QMessageBox.warning(self, None,
                                    "Database were not exported because there is nothing to export.")
            else:
                QMessageBox.warning(self, None,
                                    "Database results were not exported because the following error occurred:"
                                    f"{str(e)})")

        worker.finished.connect(finished)
        worker.error.connect(error)
        return worker
