"""MetGem plugin to download databases from MS-DIAL website"""

__version__ = '1.3'
__description__ = "MetGem plugin to download databases from MS-DIAL website"
__author__ = "Nicolas Elie"
__email__ = "nicolas.elie@cnrs.fr"
__copyright__ = "Copyright 2019-2022, CNRS/ICSN"
__license__ = "GPLv3"


def get_first_xpath_result(element, xpath):
    result = element.xpath(xpath)
    if result:
        return result[0]
    return None


# noinspection PyUnresolvedReferences
class MSDial(DbSource):

    name = "MS-DIAL"
    page = "http://prime.psc.riken.jp/compms/msdial/main.html"
    items_base_url = "http://prime.psc.riken.jp/compms/msdial/"

    def get_items(self, tree):
        items = {}

        for div in tree.xpath("//div[@class='boxMsp']"):
            href = ''
            a = get_first_xpath_result(div, "div[@class='labelDownloadIcon']/a[1]")
            if a is None:
                continue

            if a.tag == 'a':
                href = a.attrib.get('href')
                if not href or not href.endswith('.msp'):
                    continue

            title = get_first_xpath_result(div, "div[@class='labelMspName']")
            if title is None:
                continue
            else:
                title = title.text_content()
                title = title.encode('ascii', 'ignore').decode()
                title = title.strip()

            if title.startswith('All '):
                continue

            desc = ""
            if "(" in title:
                title, desc = title.split('(')
                if title in items:
                    desc = ""
                else:
                    desc = desc.replace(')', '') + "<br/>"

            polarity = get_first_xpath_result(div, "div[@class='labelPolarity']")
            desc += polarity.text_content().strip().encode('ascii', 'ignore').decode() + " "\
                if polarity is not None else ""

            records = get_first_xpath_result(div, "div[@class='labelRecords']")
            desc += records.text + " " if records is not None else ""

            units = get_first_xpath_result(div, "div[@class='labelUnit']")
            desc += units.text + " " if units is not None else ""

            if title in items:
                current_hrefs, current_desc = items[title]
                items[title] = (current_hrefs + [href], f"{current_desc}<br/>{desc}")
            else:
                items[title] = ([href], desc)

        for title, item in items.items():
            yield (title, *item)

        lipidblast_hrefs = []
        lipidblast_desc = []
        for div in tree.xpath("//div[@class='boxFork']"):
            href = ''
            a = get_first_xpath_result(div, "div[@class='labelDownloadIcon']/a[1]")
            if a is None:
                continue

            if a.tag == 'a':
                href = a.attrib.get('href')
                if not href or not href.endswith('.msp'):
                    continue

            lipidblast_hrefs.append(href)

            desc = get_first_xpath_result(div, "div[@class='labelForkName']")
            desc = desc.xpath('node()')[-1].strip()
            if desc is not None:
                try:
                    _, desc = desc.split("These libraries are also available as MSP format.")
                except ValueError:
                    pass
                lipidblast_desc.append(desc)

        yield 'LipidBlast', lipidblast_hrefs, "<br/>".join(lipidblast_desc)
