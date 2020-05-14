"""MetGem plugin to download ISDB"""

__version__ = '1.0'
__description__ = "MetGem plugin to download ISDB"
__author__ = "Nicolas Elie"
__email__ = "nicolas.elie@cnrs.fr"
__copyright__ = "Copyright 2019, CNRS/ICSN"
__license__ = "GPLv3"


class ISDB(DbSource):

    name = "ISDB"
    items_base_url = "https://raw.githubusercontent.com/oolonek/ISDB/master/Data/dbs/"

    def get_items(self):
        yield "In-Silico Database", [f'UNPD_ISDB_R_p0{i}.mgf' for i in range(1, 10)],\
              'A database of In-Silico predicted MS/MS spectrum of Natural Products'
