"""MetGem plugin to download ISDB"""

__version__ = '1.4'
__description__ = "MetGem plugin to download ISDB"
__author__ = "Nicolas Elie"
__email__ = "nicolas.elie@cnrs.fr"
__copyright__ = "Copyright 2019-2023, CNRS/ICSN"
__license__ = "GPLv3"

import json


def find_element(tree, selector: str, property: str = None, default: str = ''):
    data = tree.find(selector)
    if property is None:
        return data
    if data is None:
        return default
    for p in property.split('__'):
        try:
            data = getattr(data, p)
        except AttributeError:
            try:
                data = data.get(p, None)
            except AttributeError:
                data = None
        if data is None:
            return default
    return data


# noinspection PyUnresolvedReferences
class ISDB(DbSource):

    name = "ISDB"
    page = "https://doi.org/10.5281/zenodo.5607185"
    items_base_url = ""

    def get_items(self, tree):
        json_s = find_element(tree, './/script[@type="application/ld+json"]', 'text')
        json_load = json.loads(json_s)
        description = json_load.get('description',
                                    '\u003cp\u003eAn In Silico spectral DataBase (\u003cstrong\u003eISDB\u003c/strong\u003e) of natural products calculated\u0026nbsp;from structures aggregated in the frame of the LOTUS Initiative (\u003ca href=\"https://doi.org/10.7554/eLife.70780\"\u003ehttps://doi.org/10.7554/eLife.70780)\u003c/a\u003e.\u003cbr\u003e\nFragmented using cfm-predict 4 (\u003ca href=\"https://doi.org/10.1021/acs.analchem.1c01465\"\u003ehttps://doi.org/10.1021/acs.analchem.1c01465\u003c/a\u003e) .\u003c/p\u003e\n\n\u003cp\u003eIn silico spectral database preparation and use for dereplication initially\u0026nbsp;described in\u0026nbsp;\u003cem\u003eIntegration of Molecular Networking and In-Silico MS/MS Fragmentation for Natural Products Dereplication\u003c/em\u003e \u003ca href=\"https://doi.org/10.1021/ACS.ANALCHEM.5B04804\"\u003ehttps://doi.org/10.1021/ACS.ANALCHEM.5B04804\u003c/a\u003e\u003c/p\u003e\n\n\u003cp\u003eSee\u0026nbsp;\u003ca href=\"https://github.com/mandelbrot-project/spectral_lib_builder\"\u003ehttps://github.com/mandelbrot-project/spectral_lib_builder\u003c/a\u003e for associated building scripts.\u003c/p\u003e\n\n\u003cp\u003eSee\u0026nbsp;\u003ca href=\"https://github.com/mandelbrot-project/spectral_lib_matcher\"\u003ehttps://github.com/mandelbrot-project/spectral_lib_matcher\u003c/a\u003e for associated matching scripts.\u003c/p\u003e')
        identifier = json_load.get('identifier', '')
        version = json_load.get('version', '')
        version = f"Version {version}" if version else ''
        date = json_load.get('datePublished', '')
        if identifier:
            description = f"<a href='{identifier}'>{identifier}</a>\n{description}"
        if date:
            description = f"({date}) {description}"
        if version:
            description = f"{version} {description}"

        hrefs = []

        for distrib in tree.findall('.//link[@type="application/octet-stream"]'):
            href = distrib.get('href', '')
            if href and href.endswith('.mgf'):
                hrefs.append(href)
        if hrefs:
            yield "In-Silico Database", hrefs, description
