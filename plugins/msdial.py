"""MetGem plugin to download databases from MS-DIAL website"""

__version__ = '1.1'
__description__ = "MetGem plugin to download databases from MS-DIAL website"
__author__ = "Nicolas Elie"
__email__ = "nicolas.elie@cnrs.fr"
__copyright__ = "Copyright 2019-2020, CNRS/ICSN"
__license__ = "GPLv3"


class MSDial(DbSource):

    name = "MS-DIAL"
    page = "http://prime.psc.riken.jp/compms/msdial/main.html"
    items_base_url = "http://prime.psc.riken.jp/compms/msdial/"

    def get_items(self, tree):
        for base in tree.xpath("//h3[@class='title-bg']"):
            if base.text.startswith("MSDIAL metabolomics MSP"):
                for br in base.getnext().findall('br'):
                    a = br.getnext()
                    tail = br.tail
                    if tail is None:
                        continue
                    tail = tail.strip()
                    if not tail or tail.startswith('All'):
                        continue

                    if a.tag == 'a':
                        href = a.attrib.get('href')
                        if not href or not href.endswith('.msp'):
                            continue

                        title = tail.split(' (')[0]
                        yield title, [href], tail
                    else:
                        break
            elif base.text.startswith("LipidBlast fork"):
                ids = []
                desc = "In silico MS/MS spectra for lipid identifications.<br>"
                for a in base.getnext().findall('a'):
                    href = a.attrib.get('href')
                    if not href or not href.endswith('.msp'):
                        continue

                    ids.append(href)
                    desc += a.text + '<br>'
                yield 'LipidBlast', ids, desc
