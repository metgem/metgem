# These imports SHOULD be left on top of the file
from .metadata import (CsvDelimiterCombo,
                       NodeTableView, EdgeTableView, NodesWidget, EdgesWidget)
from .annotations.table import AnnotationsWidget, AnnotationsModel
from .options_widgets import (TSNEOptionsWidget, NetworkOptionsWidget, MDSOptionsWidget,
                              UMAPOptionsWidget, IsomapOptionsWidget, PHATEOptionsWidget,
                              CosineOptionsWidget, QueryDatabasesOptionsWidget)

from .color_picker import ColorPicker
from .databases import SpectrumDetailsWidget, PubMedLabel, SpectrumIdLabel, SubmitUserLabel, QualityLabel
from .delegates import AutoToolTipItemDelegate, LibraryQualityDelegate, EnsureStringItemDelegate
from .loading_views import (LoadingListView, LoadingListWidget,
                            LoadingTableView, LoadingTableWidget,
                            LoadingTreeView, LoadingTreeWidget)
from .network import NetworkFrame, TSNEFrame, AVAILABLE_NETWORK_WIDGETS
from .slider import Slider
from .spectrum import (SpectrumCanvas, SpectrumWidget, SpectraComparisonWidget)
from .structure import StructureSvgWidget
from .toolbar_menu import ToolBarMenu
from .welcome_widget import WelcomeWidget
from .annotations import (AnnotationsNetworkView, AnnotationsNetworkScene,
                          MODE_LINE, MODE_ARROW, MODE_RECT, MODE_ELLIPSE, MODE_TEXT)

try:
    from .jupyter import JupyterWidget
except ImportError:
    pass
