import os
import ftplib
from datetime import datetime

import requests
from lxml import html, etree

from PyQt5.QtCore import pyqtSignal

from .base_worker import BaseWorker

LIB_URL = "https://gnps.ucsd.edu/ProteoSAFe/libraries.jsp"
FTP_URL = "ccms-ftp.ucsd.edu"


class ListGNPSDatabasesWorker(BaseWorker):

    updated = pyqtSignal(dict)

    def __init__(self):
        super().__init__(track_progress=False)

    def run(self):
        items = []

        try:
            r = requests.get(LIB_URL)
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
                            item = {'name': name, 'ids': ids, 'desc': desc}
                            items.append(item)
                            self.updated.emit(item)

            self._result = items
            self.finished.emit()


class GetGNPSDatabasesMtimeWorker(BaseWorker):

    def __init__(self, ids):
        super().__init__(track_progress=False)
        self.ids = ids

    def run(self):
        mtimes = {}
        try:
            with ftplib.FTP(FTP_URL) as ftp:
                ftp.login()
                ftp.cwd('Spectral_Libraries')

                # Then try to download files
                for i, id_ in enumerate(self.ids):
                    if self._should_stop:
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


class DownloadGNPSDatabasesWorker(BaseWorker):
    filesizes_ready = pyqtSignal(dict)

    def __init__(self, ids, path):
        super().__init__()
        self.ids = ids
        self.path = path
        self._filesizes = {}

    def run(self):
        try:
            with ftplib.FTP(FTP_URL) as ftp:
                ftp.login()
                ftp.cwd('Spectral_Libraries')

                # First, get files' sizes
                for i, id_ in enumerate(self.ids):
                    try:
                        size = ftp.size(f'{id_}.mgf')
                    except ftplib.error_perm:
                        self._filesizes[id_] = 0
                    else:
                        self._filesizes[id_] = size
                self.filesizes_ready.emit(self._filesizes)

                # Then try to download files
                for i, id_ in enumerate(self.ids):
                    if self._should_stop:
                        self.canceled.emit()
                        return False

                    path = os.path.join(self.path, f'{id_}.mgf')
                    offset = 0
                    if os.path.exists(path):
                        offset = os.path.getsize(path)
                        self.updated.emit(offset)
                        #
                        # try:
                        #     rd = ftp.sendcmd(f'MDTM {id_}.mgf')
                        #     rd = datetime.strptime(rd[4:], '%Y%m%d%H%M%S')
                        #     if rd <= datetime.fromtimestamp(os.path.getmtime(path)):
                        #         self.updated.emit(self._filesizes[id_])
                        #         continue
                        # except error_perm:
                        #     self.updated.emit(self._filesizes[id_])
                        #     continue

                    if offset < self._filesizes[id_]:
                        with open(path, 'ab') as f:
                            def write_callback(chunk):
                                f.write(chunk)
                                self.updated.emit(len(chunk))

                                if self._should_stop:
                                    ftp.abort()
                                    self.canceled.emit()

                            ftp.retrbinary(f'RETR {id_}.mgf', write_callback, rest=offset)
        except ftplib.all_errors as e:
            self.error.emit(e)
            return False
        else:
            self.finished.emit()
