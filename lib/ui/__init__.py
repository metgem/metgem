from .main_window import MainWindow
from .process_data_dialog import ProcessDataDialog
from .edit_options_dialog import (EditTSNEOptionsDialog, EditNetworkOptionsDialog, EditMDSOptionsDialog,
                                  EditIsomapOptionsDialog, HAS_UMAP)
if HAS_UMAP:
    from .edit_options_dialog import EditUMAPOptionsDialog
from .current_parameters_dialog import CurrentParametersDialog
from .download_databases_dialog import DownloadDatabasesDialog
from .view_databases_dialog import ViewDatabasesDialog
from .progress_dialog import ProgressDialog
from .import_metadata_dialog import ImportMetadataDialog
from .settings_dialog import SettingsDialog
from .query_databases_dialog import QueryDatabasesDialog
from .view_standards_results_dialog import ViewStandardsResultsDialog
from .import_user_database_dialog import ImportUserDatabaseDialog
from .about_dialog import AboutDialog
from .color_mapping_dialog import PieColorMappingDialog, ColorMappingDialog
from .size_mapping_dialog import SizeMappingDialog
from .edit_group_mapping import EditGroupMappingsDialog
from .clusterize_dialog import ClusterizeDialog
