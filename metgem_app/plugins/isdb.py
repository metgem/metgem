"""MetGem plugin to download ISDB"""

__version__ = '1.1'
__description__ = "MetGem plugin to download ISDB"
__author__ = "Nicolas Elie"
__email__ = "nicolas.elie@cnrs.fr"
__copyright__ = "Copyright 2019-2022, CNRS/ICSN"
__license__ = "GPLv3"

import json


# noinspection PyUnresolvedReferences
class ISDB(DbSource):

    name = "ISDB"
    page = "https://doi.org/10.5281/zenodo.5607185"
    items_base_url = ""

    def get_items(self, tree):
        json_s = tree.find('.//script[@type="application/ld+json"]').text
        json_load = json.loads(json_s)
        description = json_load['description']
        identifier = json_load['identifier']
        version = json_load['version']
        date = json_load['datePublished']

        hrefs = []

        for distrib in json_load['distribution']:
            if distrib['@type'] == 'DataDownload':
                href = distrib['contentUrl']
            hrefs.append(href)
        yield "In-Silico Database", hrefs,\
              f"Version {version} ({date}) <a href='{identifier}'>{identifier}</a>\n{description}"
