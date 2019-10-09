import os
import ftplib
from datetime import datetime

import requests
from urllib.parse import urljoin
from lxml import html, etree

from PyQt5.QtCore import pyqtSignal

from ..base import BaseWorker
from ...plugins import get_db_sources

GNPS_LIB_URL = "https://gnps.ucsd.edu/ProteoSAFe/libraries.jsp"
GNPS_FTP_URL = "ccms-ftp.ucsd.edu"


class ListDatabasesWorker(BaseWorker):

    itemReady = pyqtSignal(dict)

    def __init__(self):
        super().__init__(track_progress=False)

    def run(self):
        items = []

        # Find available databases on GNPS libraries page
        try:
            r = requests.get(GNPS_LIB_URL)
        except requests.exceptions.ConnectionError as e:
            self.error.emit(e)
            return False
        else:
            if r.status_code == 200:
                tree = html.fromstring(r.content)
                for base in tree.xpath("//table[@class='result']/tr"):
                    tds = base.findall('td')
                    if tds is not None and len(tds) == 3:
                        name = tds[0].text if tds[0].text is not None else ''
                        ids = tds[1].findall('a')
                        if ids is None:
                            continue
                        ids = [id_.attrib['href'].split('=')[1].split('#')[0] + '.mgf' for id_ in ids
                               if 'href' in id_.attrib and '=' in id_.attrib['href']]
                        desc = tds[2].text if tds[2].text is not None else ''
                        desc += ''.join([etree.tostring(child).decode() for child in tds[2].iterdescendants()])

                        if len(ids) > 0 and not ids[0] == 'all.mgf':
                            item = {'name': name, 'ids': ids, 'desc': desc, 'origin': 'GNPS'}
                            items.append(item)
                            self.itemReady.emit(item)

        # Plugins
        for plugin in get_db_sources():
            origin = plugin.name
            if not isinstance(origin, str):
                continue

            try:
                url = plugin.page
                if url is not None:
                    r = requests.get(url)
            except (requests.exceptions.ConnectionError, requests.exceptions.MissingSchema) as e:
                self.error.emit(e)
                return False
            else:
                if url is None or r.status_code == 200:
                    if url is not None:
                        tree = html.fromstring(r.content)
                        gen = plugin.get_items(tree)
                    else:
                        gen = plugin.get_items()

                    for item in gen:
                        try:
                            title, ids, desc = item
                        except (ValueError, AssertionError):
                            pass
                        else:
                            if not isinstance(title, str) or not isinstance(ids, list) or not isinstance(desc, str):
                                continue

                            for id_ in ids:
                                if not isinstance(id_, str):
                                    continue

                            item = {'name': title, 'ids': ids, 'desc': desc, 'origin': origin}
                            self.itemReady.emit(item)

        self._result = items
        self.finished.emit()


class GetGNPSDatabasesMtimeWorker(BaseWorker):

    def __init__(self, ids):
        super().__init__(track_progress=False)
        self.ids = ids

    def run(self):
        mtimes = {}
        try:
            with ftplib.FTP(GNPS_FTP_URL) as ftp:
                ftp.login()
                ftp.cwd('Spectral_Libraries')

                # Then try to download files
                for i, id_ in enumerate(self.ids):
                    if self.isStopped():
                        self.canceled.emit()
                        return False

                    rd = ftp.sendcmd(f'MDTM {id_}')
                    mtimes[id_] = datetime.strptime(rd[4:], '%Y%m%d%H%M%S')
        except ftplib.all_errors as e:
            self.error.emit(e)
            return False
        else:
            self._result = mtimes
            self.finished.emit()


class DownloadDatabasesWorker(BaseWorker):

    def __init__(self, ids, path):
        super().__init__()
        self.ids = ids
        self.path = path
        self.iterative_update = True
        self.max = 0
        self.desc = 'Downloading databases...'

    def run(self):
        downloaded = {}
        unreachable = {}
        filesizes = {}
        for k in self.ids.keys():
            downloaded[k] = set()
            unreachable[k] = set()
            filesizes[k] = {}

        # First step, get file sizes
        # ---------------------------

        # GNPS
        gnps_ids = self.ids.get('GNPS', [])
        if gnps_ids:
            try:
                with ftplib.FTP(GNPS_FTP_URL) as ftp:
                    ftp.login()
                    ftp.cwd('Spectral_Libraries')

                    for name in gnps_ids:
                        for id_ in gnps_ids[name]:
                            filesizes['GNPS'][name] = 0
                            try:
                                size = ftp.size(f'{id_}')
                            except ftplib.error_perm:
                                unreachable['GNPS'].add(name)
                            else:
                                filesizes['GNPS'][name] += size
            except ftplib.all_errors as e:
                try:
                    e.name = name
                except UnboundLocalError:
                    pass
                self.error.emit(e)
                return

        # Plugins
        for plugin in get_db_sources():
            origin = plugin.name
            url = plugin.page
            items_base_url = plugin.items_base_url

            if not isinstance(origin, str) or (url is not None and not isinstance(url, str)):
                continue

            if items_base_url is None:
                items_base_url = url + '/'
            else:
                items_base_url += '/'

            ids = self.ids.get(origin, [])
            if not ids:
                continue

            for name in ids:
                for id_ in ids[name]:
                    try:
                        filesizes[origin][name] = 0

                        with requests.head(urljoin(items_base_url, id_)) as r:
                            filesizes[origin][name] += int(r.headers['content-length'])

                        if r.status_code != 200:
                            raise requests.ConnectionError
                    except (requests.ConnectionError, KeyError):
                        filesizes[origin][name] = 0
                        unreachable[origin].add(name)

        self.max = sum([v for f in filesizes.values() for v in f.values()])

        # Second step, download files
        # ---------------------------

        # GNPS
        if gnps_ids:
            try:
                with ftplib.FTP(GNPS_FTP_URL) as ftp:
                    ftp.login()
                    ftp.cwd('Spectral_Libraries')

                    for name in gnps_ids:
                        for i, id_ in enumerate(gnps_ids[name]):
                            if self.isStopped():
                                self.canceled.emit()
                                return

                            if filesizes['GNPS'][name] == 0:
                                continue

                            path = os.path.join(self.path, f'{id_}')

                            with open(path, 'wb') as f:
                                def write_callback(chunk):
                                    f.write(chunk)
                                    self.updated.emit(len(chunk))

                                    if self.isStopped():
                                        ftp.abort()
                                        self.canceled.emit()

                                ftp.retrbinary(f'RETR {id_}', write_callback)
                                downloaded['GNPS'].add(name)

            except ftplib.all_errors as e:
                try:
                    e.name = name
                except UnboundLocalError:
                    pass
                self.error.emit(e)
                return

        # Plugins
        for plugin in get_db_sources():
            origin = plugin.name
            url = plugin.page
            items_base_url = plugin.items_base_url

            if not isinstance(origin, str) or (url is not None and not isinstance(url, str)):
                continue

            if items_base_url is None:
                items_base_url = url + '/'
            else:
                items_base_url += '/'

            ids = self.ids.get(origin, [])
            if not ids:
                continue

            for name in ids:
                for id_ in ids[name]:
                    if id_ not in unreachable[origin]:
                        path = os.path.join(self.path, os.path.basename(id_))
                        try:
                            with open(path, 'wb') as f:
                                with requests.get(urljoin(items_base_url, id_), stream=True) as r:
                                    for chunk in r.iter_content(chunk_size=1024):
                                        if chunk:  # filter out keep-alive new chunks
                                            f.write(chunk)
                                            self.updated.emit(1024)

                                        if self.isStopped():
                                            self.canceled.emit()

                                downloaded[origin].add(name)
                        except requests.ConnectionError as e:
                            try:
                                e.name = name
                            except UnboundLocalError:
                                pass
                            self.error.emit(e)
                            return

        return downloaded, unreachable
