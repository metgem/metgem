import os
from io import BytesIO
from zipfile import ZipFile

import requests

from .base import BaseWorker


class DownloadPluginsWorker(BaseWorker):

    def __init__(self, path, plugins):
        super().__init__()
        self.path = path
        self.plugins = plugins
        self.max = len(plugins)

    def run(self):
        downloaded = set()
        unreachable = set()

        for i, plugin in enumerate(self.plugins):
            url = plugin.get('url')
            if not url:
                continue

            try:
                with BytesIO() as bytes_io:
                    # Download zip file of plugin
                    with requests.get(url, stream=True) as r:
                        r.raise_for_status()

                        for chunk in r.iter_content(chunk_size=1024):
                            if chunk:  # filter out keep-alive new chunks
                                bytes_io.write(chunk)
                                self.updated.emit(1024)

                            if self.isStopped():
                                self.canceled.emit()

                    # Extract plugin script from zip
                    with ZipFile(bytes_io) as zf:
                        name = plugin['name']
                        version = plugin['version']

                        with zf.open(f"plugins-{name}-{version}/{name}.py") as pfile:
                            with open(os.path.join(self.path, f"{name}.py"), "wb") as out:
                                out.write(pfile.read())

                    downloaded.add(plugin['name'])
            except (requests.ConnectionError, requests.HTTPError) as e:
                unreachable.add(plugin['name'])
            finally:
                self.updated.emit(i)

            return downloaded, unreachable
