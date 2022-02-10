import requests

from ..base import BaseWorker


class CheckPluginsVersionsWorker(BaseWorker):
    URL = "https://metgem.github.io/plugins.json"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def run(self):
        if self.isStopped():
            self.canceled.emit()
            return False

        try:
            r = requests.get(CheckPluginsVersionsWorker.URL, timeout=.5)
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
            plugins = {}
            for plugin in json:
                name = plugin.get("name")
                version = plugin.get("version")
                url = plugin.get("url")

                if not name or not version or not url:
                    continue

                plugins[name] = plugin

            if not self.isStopped():
                if plugins:
                    return plugins
                else:
                    return False
            else:
                self.canceled.emit()

        # if r:
        #     json = r.json()
        #     plugins_to_update = {}
        #     for plugin in json:
        #         name = plugin.get("name")
        #         version = plugin.get("version")
        #         url = plugin.get("url")
        #
        #         if not name or not version or not url:
        #             continue
        #
        #         if name in loaded_plugins:
        #             if version > loaded_plugins[name]:
        #                 plugins_to_update[name] = plugin
        #
        #     if not self.isStopped():
        #         if plugins_to_update:
        #             return plugins_to_update
        #         else:
        #             return False
        #     else:
        #         self.canceled.emit()
