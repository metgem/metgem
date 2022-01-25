import re
import requests

from ..base import BaseWorker


class CheckUpdatesWorker(BaseWorker):
    URL = "https://api.github.com/repos/metgem/metgem/releases/latest"

    def __init__(self, current_version, **kwargs):
        super().__init__(**kwargs)
        self._current_version = current_version

    def run(self):
        if self.isStopped():
            self.canceled.emit()
            return False

        if not self._current_version:
            return False

        try:
            r = requests.get(CheckUpdatesWorker.URL, timeout=.5)
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            return False

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
            if not new_version or new_version <= self._current_version:
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
