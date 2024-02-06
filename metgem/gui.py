#!/usr/bin/env python

DOMAIN = "CNRS"
ORGANIZATION = "ICSN"
APPLICATION = "MetGem"


# noinspection PyUnresolvedReferences
def run():
    import sys
    import os

    # pytest switch: pass next arguments to pytest
    # https://docs.pytest.org/en/stable/example/simple.html?highlight=pyinstaller#freezing-pytest
    if len(sys.argv) > 1:
        if sys.argv[1] == "--pytest":
            import pytest
            import pytestqt
            import pytest_mock

            sys.exit(pytest.main(sys.argv[2:], plugins=[pytestqt, pytest_mock]))
        elif sys.argv[1] == "--python-console":
            from IPython import embed

            sys.exit(embed())
        elif sys.argv[1] == "-sS" and sys.argv[2] == "-c":
            # Workaround for mac version detection in 'packaging'
            # https://github.com/pypa/packaging/blob/4d8534061364e3cbfee582192ab81a095ec2db51/src/packaging/tags.py#L413
            import platform
            print(platform.mac_ver()[0])
            sys.exit()

    import argparse
    import importlib

    # Make sure decimal separator is dot
    os.environ['LC_NUMERIC'] = 'C'

    # Add ui folder to path to be able to load ui_rc from ui generated files
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ui'))

    # Fix no window shown on Mac OS Big Sur
    # http://www.tiger-222.fr/?d=2020/11/16/11/06/36-macos-big-sur-et-pyqt
    if sys.platform.startswith('darwin'):
        os.environ["QT_MAC_WANTS_LAYER"] = '1'

    from metgem._version import get_versions
    VERSION = get_versions()['version']

    parser = argparse.ArgumentParser(description=f'Launch {APPLICATION}.')
    parser.add_argument('fname', type=str, nargs='?', help="A project to open")
    parser.add_argument('--debug', action='store_true', help=f"Ease debugging of {APPLICATION}.")
    parser.add_argument('--jupyter', action='store_true',
                        help=(f"Embed a Jupyter console inside {APPLICATION} to programmatically modify "
                              f"some {APPLICATION}'s behavior."))
    parser.add_argument('--disable-opengl', action='store_true', help="Disable use of OpenGL for older computers.")
    parser.add_argument('--python-rendering', action='store_true',
                        help="Force use of slower Python rendering for networks.")
    parser.add_argument('--no-exception-handler', action='store_true', help="Disable Graphical Exception Handler.")

    args = parser.parse_args()

    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QCoreApplication, Qt
    # QtWebEngineWidgets must be imported before a QApplication is created
    # TODO: from PySide6.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineProfile

    app = QApplication(sys.argv)

    # PyInstaller hack for qt to find plugins
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        QApplication.addLibraryPath(os.path.join(sys._MEIPASS, "PySide6", "plugins"))

    QCoreApplication.setOrganizationDomain(DOMAIN)
    QCoreApplication.setOrganizationName(ORGANIZATION)
    QCoreApplication.setApplicationName(APPLICATION)
    QCoreApplication.setApplicationVersion(VERSION)

    from metgem.splash import SplashScreen
    splash = SplashScreen()
    splash.setVersion(VERSION)
    splash.show()

    splash.showMessage("Loading numpy library...")
    import numpy
    splash.setValue(10)

    splash.showMessage("Loading numba library...")
    # import numba
    splash.setValue(20)

    splash.showMessage("Loading pandas library...")
    import pandas
    splash.setValue(30)

    splash.showMessage("Loading pyarrow library...")
    import pyarrow
    splash.setValue(40)

    splash.showMessage("Loading igraph library...")
    import igraph
    splash.setValue(50)

    splash.showMessage("Loading scipy library...")
    import scipy
    splash.setValue(60)

    splash.showMessage("Loading lxml library...")
    import lxml
    splash.setValue(70)

    splash.showMessage("Loading sklearn library...")
    import sklearn
    splash.setValue(80)

    splash.showMessage("Loading matplotlib library...")
    import matplotlib
    splash.setValue(90)

    splash.showMessage("Loading Configuration module...")
    importlib.import_module('.config', 'metgem')
    splash.setValue(91)

    splash.showMessage("Loading Errors modules...")
    importlib.import_module('.errors', 'metgem')
    splash.setValue(92)

    splash.showMessage("Loading Logger module...")
    importlib.import_module('.logger', 'metgem')
    splash.setValue(93)

    splash.showMessage("Loading Databases module...")
    importlib.import_module('.database', 'metgem')
    splash.setValue(94)

    splash.showMessage("Loading Workers...")
    importlib.import_module('.workers.options', 'metgem')
    importlib.import_module('.workers.base', 'metgem')
    importlib.import_module('.workers.databases', 'metgem')
    importlib.import_module('.workers.core', 'metgem')
    importlib.import_module('.workers.net', 'metgem')
    importlib.import_module('.workers.gui', 'metgem')
    splash.setValue(96)

    from metgem.config import set_python_rendering_flag
    set_python_rendering_flag(args.python_rendering)

    splash.showMessage("Loading User interface...")
    importlib.import_module('.ui', 'metgem')
    splash.setValue(98)

    splash.showMessage("Loading plugins...")
    importlib.import_module('.plugins', 'metgem')
    splash.setValue(100)

    splash.showMessage("")

    from metgem.config import set_debug_flag, set_jupyter_flag, set_use_opengl_flag
    set_debug_flag(args.debug)
    set_jupyter_flag(args.jupyter)
    set_use_opengl_flag(not args.disable_opengl)

    from metgem.ui import MainWindow
    window = MainWindow()

    if not args.no_exception_handler:
        from metgem.errors import exceptionHandler
        sys.excepthook = exceptionHandler

    window.show()
    splash.finish(window)

    # Support for file association
    if args.fname is not None:
        fname = args.fname
        from metgem.config import FILE_EXTENSION
        if os.path.exists(fname) and os.path.splitext(fname)[1] == FILE_EXTENSION:
            window.load_project(fname)

    sys.exit(app.exec_())


if __name__ == '__main__':
    run()
