# These imports SHOULD be left on top of the file
from metgem_app.ui.widgets.metadata import (CsvDelimiterCombo,
                       NodesWidget, EdgesWidget,
                       NodeTableView, EdgeTableView)
from metgem_app.ui.widgets.annotations.table import AnnotationsWidget, AnnotationsModel
from metgem_app.ui.widgets.options_widgets import (TSNEOptionsWidget, NetworkOptionsWidget, MDSOptionsWidget,
                              UMAPOptionsWidget, IsomapOptionsWidget, PHATEOptionsWidget,
                              CosineOptionsWidget, QueryDatabasesOptionsWidget)

from metgem_app.ui.widgets.color_picker import ColorPicker
from metgem_app.ui.widgets.databases import SpectrumDetailsWidget, PubMedLabel, SpectrumIdLabel, SubmitUserLabel, QualityLabel
from metgem_app.ui.widgets.delegates import AutoToolTipItemDelegate, LibraryQualityDelegate, EnsureStringItemDelegate
from metgem_app.ui.widgets.loading_views import (LoadingListView, LoadingListWidget,
                            LoadingTableView, LoadingTableWidget,
                            LoadingTreeView, LoadingTreeWidget)
from metgem_app.ui.widgets.network import NetworkFrame, TSNEFrame, AVAILABLE_NETWORK_WIDGETS
from metgem_app.ui.widgets.slider import Slider
from metgem_app.ui.widgets.spectrum import (SpectrumCanvas, SpectrumWidget, SpectraComparisonWidget)
from metgem_app.ui.widgets.structure import StructureSvgWidget
from metgem_app.ui.widgets.toolbar_menu import ToolBarMenu
from metgem_app.ui.widgets.welcome_widget import WelcomeWidget
from metgem_app.ui.widgets.annotations import (AnnotationsNetworkView, AnnotationsNetworkScene,
                          MODE_LINE, MODE_ARROW, MODE_RECT, MODE_ELLIPSE, MODE_TEXT)

try:
    from metgem_app.ui.widgets.jupyter import JupyterWidget
except ImportError:
    pass
