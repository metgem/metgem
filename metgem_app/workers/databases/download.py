import os
from urllib.parse import urljoin

import requests
from lxml import html

from metgem_app.workers.base import BaseWorker
from metgem_app.utils.qt import Signal


class ListDatabasesWorker(BaseWorker):

    itemReady = Signal(dict)

    def __init__(self, db_sources):
        super().__init__(track_progress=False)
        self.db_sources = db_sources

    def run(self):
        items = []

        for plugin in self.db_sources:
            origin = plugin.name
            if not isinstance(origin, str):
                continue

            try:
                url = plugin.page
                if url is not None:
                    r = requests.get(url, timeout=1)
                    r.raise_for_status()
            except (requests.ConnectionError, requests.HTTPError,
                    requests.exceptions.MissingSchema, requests.exceptions.Timeout):
                pass
            else:
                if url is None or r.status_code == 200:
                    if url is not None:
                        tree = html.fromstring(r.content)
                        gen = plugin.get_items(tree)
                    else:
                        gen = plugin.get_items()

                    try:
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
                    except:  # If a plugin raise an error, continue to next plugin
                        continue

        self._result = items
        self.finished.emit()


class DownloadDatabasesWorker(BaseWorker):

    def __init__(self, ids, path, db_sources):
        super().__init__()
        self.ids = ids
        self.path = path
        self.iterative_update = True
        self.max = 0
        self.desc = 'Downloading databases...'
        self.db_sources = db_sources

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
        for plugin in self.db_sources:
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
        for plugin in self.db_sources:
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
                                    r.raise_for_status()

                                    for chunk in r.iter_content(chunk_size=1024):
                                        if chunk:  # filter out keep-alive new chunks
                                            f.write(chunk)
                                            self.updated.emit(1024)

                                        if self.isStopped():
                                            self.canceled.emit()

                                downloaded[origin].add(name)
                        except (requests.ConnectionError, requests.HTTPError) as e:
                            try:
                                e.name = name
                            except UnboundLocalError:
                                pass
                            self.error.emit(e)
                            return

        return downloaded, unreachable
