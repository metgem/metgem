import os
import ftplib
from datetime import datetime

import requests
from lxml import html, etree

from PyQt5.QtCore import pyqtSignal

from ..base import BaseWorker

GNPS_LIB_URL = "https://gnps.ucsd.edu/ProteoSAFe/libraries.jsp"
GNPS_FTP_URL = "ccms-ftp.ucsd.edu"

ISDB_HTTP_FMT = "https://raw.githubusercontent.com/oolonek/ISDB/master/Data/dbs/{name}.mgf"
ISDB_NAME_FMT = "UNPD_ISDB_R_p0{}"
ISDB_ID = "UNPD_ISDB_R"


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
                        ids = [id_.attrib['href'].split('=')[1].split('#')[0] for id_ in ids
                               if 'href' in id_.attrib and '=' in id_.attrib['href']]
                        desc = tds[2].text if tds[2].text is not None else ''
                        desc += ''.join([etree.tostring(child).decode() for child in tds[2].iterdescendants()])

                        if len(ids) > 0 and not ids[0] == 'all':
                            item = {'name': name, 'ids': ids, 'desc': desc, 'origin': 'GNPS'}
                            items.append(item)
                            self.itemReady.emit(item)

        # Add ISDB
        item = {'name': 'ISDB', 'ids': [ISDB_ID],
                'desc': 'A database of In-Silico predicted MS/MS spectrum of Natural Products',
                'origin': 'ISDB'}
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

                    rd = ftp.sendcmd(f'MDTM {id_}.mgf')
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
        self._filesizes = {}
        self.iterative_update = True
        self.max = 0
        self.desc = 'Downloading databases...'

    def run(self):
        id_ = None
        downloaded_ids = []
        unreachable_ids = []

        gnps_ids = [id_ for id_ in self.ids if id_ != ISDB_ID]

        # First step, get file sizes
        # ---------------------------

        # ISDB
        if ISDB_ID in self.ids:
            try:
                self._filesizes[ISDB_ID] = 0
                for i in range(1, 10):
                    name = ISDB_NAME_FMT.format(i)
                    url = ISDB_HTTP_FMT.format(name=name)

                    with requests.head(url) as r:
                        self._filesizes[ISDB_ID] += int(r.headers['content-length'])
            except requests.ConnectionError:
                unreachable_ids.append(ISDB_ID)

        # GNPS
        if gnps_ids:
            try:
                with ftplib.FTP(GNPS_FTP_URL) as ftp:
                    ftp.login()
                    ftp.cwd('Spectral_Libraries')

                    # First, get files' sizes
                    for i, id_ in enumerate(gnps_ids):
                        try:
                            size = ftp.size(f'{id_}.mgf')
                        except ftplib.error_perm:
                            unreachable_ids.append(id_)
                            self._filesizes[id_] = 0
                        else:
                            self._filesizes[id_] = size
            except ftplib.all_errors as e:
                e.id = id_
                self.error.emit(e)
                return

        self.max = sum(self._filesizes.values())

        # Second step, download files
        # ---------------------------

        # ISDB
        if ISDB_ID in self.ids and ISDB_ID not in unreachable_ids:
            path = os.path.join(self.path, f'{ISDB_ID}.mgf')
            try:
                with open(path, 'wb') as f:
                    for i in range(1, 10):
                        name = ISDB_NAME_FMT.format(i)
                        url = ISDB_HTTP_FMT.format(name=name)

                        with requests.get(url, stream=True) as r:
                            for chunk in r.iter_content(chunk_size=1024):
                                if chunk:  # filter out keep-alive new chunks
                                    f.write(chunk)
                                    self.updated.emit(1024)

                                if self.isStopped():
                                    self.canceled.emit()

                    downloaded_ids.append(ISDB_ID)
            except requests.ConnectionError as e:
                e.id = id_
                self.error.emit(e)
                return

        # GNPS
        if gnps_ids:
            try:
                with ftplib.FTP(GNPS_FTP_URL) as ftp:
                    ftp.login()
                    ftp.cwd('Spectral_Libraries')

                    # Then try to download files
                    for i, id_ in enumerate(gnps_ids):
                        if self.isStopped():
                            self.canceled.emit()
                            return

                        if self._filesizes[id_] == 0:
                            continue

                        path = os.path.join(self.path, f'{id_}.mgf')

                        with open(path, 'wb') as f:
                            def write_callback(chunk):
                                f.write(chunk)
                                self.updated.emit(len(chunk))

                                if self.isStopped():
                                    ftp.abort()
                                    self.canceled.emit()

                            ftp.retrbinary(f'RETR {id_}.mgf', write_callback)
                            downloaded_ids.append(id_)

            except ftplib.all_errors as e:
                e.id = id_
                self.error.emit(e)
                return

        return downloaded_ids, unreachable_ids