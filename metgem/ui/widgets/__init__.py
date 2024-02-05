# These imports SHOULD be left on top of the file
from metgem.ui.widgets.metadata import (CsvDelimiterCombo,
                                        NodesWidget, EdgesWidget,
                                        NodeTableView, EdgeTableView)
from metgem.ui.widgets.annotations.table import AnnotationsWidget, AnnotationsModel
from metgem.ui.widgets.options_widgets import (TSNEOptionsWidget, ForceDirectedOptionsWidget, MDSOptionsWidget,
                                               UMAPOptionsWidget, IsomapOptionsWidget, PHATEOptionsWidget,
                                               CosineOptionsWidget, QueryDatabasesOptionsWidget)

from metgem.ui.widgets.color_picker import ColorPicker
from metgem.ui.widgets.databases import SpectrumDetailsWidget, PubMedLabel, SpectrumIdLabel, SubmitUserLabel, QualityLabel
from metgem.ui.widgets.delegates import AutoToolTipItemDelegate, LibraryQualityDelegate, EnsureStringItemDelegate
from metgem.ui.widgets.loading_views import (LoadingListView, LoadingListWidget,
                                             LoadingTableView, LoadingTableWidget,
                                             LoadingTreeView, LoadingTreeWidget)
from metgem.ui.widgets.network import ForceDirectedFrame, TSNEFrame, AVAILABLE_NETWORK_WIDGETS
from metgem.ui.widgets.slider import Slider
from metgem.ui.widgets.spectrum import (SpectrumCanvas, SpectrumWidget, SpectraComparisonWidget)
from metgem.ui.widgets.structure import StructureSvgWidget
from metgem.ui.widgets.toolbar_menu import ToolBarMenu
from metgem.ui.widgets.welcome_widget import WelcomeWidget
from metgem.ui.widgets.annotations import (AnnotationsNetworkView, AnnotationsNetworkScene,
                                           MODE_LINE, MODE_ARROW, MODE_RECT, MODE_ELLIPSE, MODE_TEXT)

try:
    from metgem.ui.widgets.jupyter import JupyterWidget
except ImportError:
    pass
