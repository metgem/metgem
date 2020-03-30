import re

import requests
from PyQt5.QtCore import QCoreApplication

from .base import BaseWorker


class CheckUpdatesWorker(BaseWorker):

    def __init__(self):
        super().__init__(track_progress=False)

    def run(self):
        if self.isStopped():
            self.canceled.emit()
            return False

        URL = "https://api.github.com/repos/metgem/metgem/releases/latest"

        current_version = QCoreApplication.applicationVersion()
        if not current_version:
            return False

        r = requests.get(URL)
        try:
            r.raise_for_status()
        except requests.HTTPError:
            return False

        if self.isStopped():
            self.canceled.emit()
            return False

        if r:
            json = r.json()
            tag_name = json.get("tag_name")
            if not tag_name:
                return False

            new_version = re.sub("[^0-9.]", "", tag_name)
            if not new_version or new_version <= current_version:
                return False

            release_notes = json.get("body")
            url = json.get("html_url")
            assets = json.get("assets")

            if not self.isStopped():
                if assets:
                    return new_version, release_notes, url
                else:
                    return False
            else:
                self.canceled.emit()
