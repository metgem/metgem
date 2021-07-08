"""MetGem plugin to download databases from GNPS website"""

__version__ = '1.0'
__description__ = "MetGem plugin to download databases from GNPS website"
__author__ = "Nicolas Elie"
__email__ = "nicolas.elie@cnrs.fr"
__copyright__ = "Copyright 2021, CNRS/ICSN"
__license__ = "GPLv3"

from lxml import etree

class GNPS(DbSource):

    name = "GNPS"
    page = "https://gnps.ucsd.edu/ProteoSAFe/libraries.jsp"
    items_base_url = "https://gnps-external.ucsd.edu/gnpslibrary/"

    def get_items(self, tree):
        for base in tree.xpath("//table[@class='result']/tr"):
            tds = base.findall('td')
            if tds is not None and len(tds) == 3:
                name = tds[0].text if tds[0].text is not None else ''
                files = tds[1].findall('a')
                if files is None:
                    continue
                files = [f.attrib['href'].split('=')[1].split('#')[0] + '.mgf' for f in files
                         if 'href' in f.attrib and '=' in f.attrib['href']]
                desc = tds[2].text if tds[2].text is not None else ''
                desc += ''.join([etree.tostring(child).decode() for child in tds[2].iterdescendants()])

                if len(files) > 0 and not files[0] == 'all.mgf':
                    yield name, files, desc
