import builtins
import inspect
import os
from typing import Iterator, List, Tuple

from PyQt5.QtCore import QCoreApplication
from lxml import html
from pluginbase import PluginBase

from ..config import PLUGINS_PATH, APP_PATH


class DbSource:
    """Plugin to download databases from websites using http or https.

    Attributes:
        name (str): Name of the plugin
        page (str): Url of the page to parse in order to find databases. If None, no parsing is done.
        items_base_url (str): Base url of the files to download. If None, `page` will be used instead.

    """

    name = None
    page = None
    items_base_url = None

    def get_items(self, tree: html.HtmlElement=None) -> Iterator[Tuple[str, List[str], str]]:
        """

        Args:
            tree (lxml.html.HtmlElement, optional): Base element of the `page` parsed using `lxml`_'s ElementTree API

        Yields:
            (tuple): tuple containing:
                title (str): Title of the Database
                ids (list): list of files to download to get the database
                desc (str): Description of the database (Plain text or html).

        .. _lxml:
            https://lxml.de/
        """

        raise NotImplementedError


def get_loaded_plugins():
    return __loaded_plugins


def get_db_sources():
    return __db_sources


def register_db_source(obj):
    if isinstance(obj, DbSource):
        try:
            if obj.name != 'User':
                __db_sources.append(obj)
        except AttributeError:
            pass


def load_plugin(source, plugin_name):
    builtins.DbSource = DbSource
    plugin = source.load_plugin(plugin_name)
    # noinspection PyUnresolvedReferences
    del builtins.DbSource

    name = plugin.__name__.split('.')[-1]
    __loaded_plugins[name] = plugin

    return plugin


__db_sources = []
__loaded_plugins = {}
source = None


def reload_plugins():
    global __db_sources, __loaded_plugins, source
    __db_sources = []
    __loaded_plugins = {}

    base = PluginBase(package='lib.plugins')
    if source is not None:
        source = None
    source = base.make_plugin_source(searchpath=[PLUGINS_PATH,
                                                 os.path.join(APP_PATH, 'plugins')],
                                     identifier=QCoreApplication.applicationName())

    for plugin_name in source.list_plugins():
        plugin = load_plugin(source, plugin_name)

        for name, obj in inspect.getmembers(plugin, inspect.isclass):
            if issubclass(obj, DbSource):
                register_db_source(obj())


reload_plugins()
