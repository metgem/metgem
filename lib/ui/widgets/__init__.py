# These two imports SHOULD be left on top of the file
from .metadata import (NodesModel, EdgesModel, ProxyModel, CsvDelimiterCombo,
                       NodeTableView, EdgeTableView, LabelRole,
                       NodesWidget, EdgesWidget)
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
from .spectrum import (SpectrumCanvas, SpectrumNavigationToolbar, SpectrumWidget,
                       SpectraComparisonWidget)
from .structure import StructureSvgWidget
from .toolbar_menu import ToolBarMenu
from .welcome_widget import WelcomeWidget

try:
    from .jupyter import JupyterWidget
except ImportError:
    pass
