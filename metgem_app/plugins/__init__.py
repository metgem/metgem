import builtins
import inspect
import os
from typing import Iterator, List, Tuple

from PyQt5.QtCore import QCoreApplication
from lxml import html
from pluginbase import PluginBase

from ..config import PLUGINS_PATH, APP_PATH
from ..logger import logger

__all__ = ('get_loaded_plugins', 'reload_plugins', 'get_db_sources')


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

    def get_items(self, tree: html.HtmlElement = None) -> Iterator[Tuple[str, List[str], str]]:
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


# noinspection PyShadowingNames
def load_plugin(source, plugin_name):
    builtins.DbSource = DbSource
    try:
        plugin = source.load_plugin(plugin_name)
    except (IndentationError, ImportError, SyntaxError) as e:
        logger.error(str(e))
        return

    # noinspection PyUnresolvedReferences
    del builtins.DbSource

    return plugin


__db_sources = []
__loaded_plugins = {}
source = None
builtins_source = None


def reload_plugins():
    global __db_sources, __loaded_plugins, source, builtins_source
    __db_sources = []
    __loaded_plugins = {}

    base = PluginBase(package='metgem_app.plugins')
    if source is not None:
        source = None
    source = base.make_plugin_source(searchpath=[PLUGINS_PATH],
                                     identifier=QCoreApplication.applicationName())
    if builtins_source is None:
        builtins_source = base.make_plugin_source(searchpath=[os.path.join(APP_PATH,
                                                                           'metgem_app',
                                                                           'plugins')],
                                                  identifier=f"{QCoreApplication.applicationName()}_builtins")

    for plugin_name in builtins_source.list_plugins():
        plugin = load_plugin(builtins_source, plugin_name)
        if plugin is not None:
            __loaded_plugins[plugin_name] = plugin

    for plugin_name in source.list_plugins():
        plugin = load_plugin(source, plugin_name)
        if plugin_name in __loaded_plugins:
            if plugin.__version__ >= __loaded_plugins[plugin_name].__version__:
                __loaded_plugins[plugin_name] = plugin

    for plugin in __loaded_plugins.values():
        for name, obj in inspect.getmembers(plugin, inspect.isclass):
            if issubclass(obj, DbSource):
                register_db_source(obj())


reload_plugins()
