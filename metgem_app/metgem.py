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

    import argparse
    import importlib

    # Make sure decimal separator is dot
    os.environ['LC_NUMERIC'] = 'C'

    # Fix no window shown on Mac OS Big Sur
    # http://www.tiger-222.fr/?d=2020/11/16/11/06/36-macos-big-sur-et-pyqt
    if sys.platform.startswith('darwin'):
        os.environ["QT_MAC_WANTS_LAYER"] = '1'

    from ._version import get_versions
    VERSION = get_versions()['version']

    parser = argparse.ArgumentParser(description=f'Launch {APPLICATION}.')
    parser.add_argument('fname', type=str, nargs='?', help="A project to open")
    parser.add_argument('--debug', action='store_true', help=f"Ease debugging of {APPLICATION}.")
    parser.add_argument('--jupyter', action='store_true',
                        help=(f"Embed a Jupyter console inside {APPLICATION} to programmatically modify "
                              f"some {APPLICATION}'s behavior."))
    parser.add_argument('--disable-opengl', action='store_true', help="Disable use of OpenGL for older computers.")

    args = parser.parse_args()

    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import QCoreApplication

    app = QApplication(sys.argv)

    QCoreApplication.setOrganizationDomain(DOMAIN)
    QCoreApplication.setOrganizationName(ORGANIZATION)
    QCoreApplication.setApplicationName(APPLICATION)
    QCoreApplication.setApplicationVersion(VERSION)

    from .splash import SplashScreen
    splash = SplashScreen()
    splash.setVersion(VERSION)
    splash.show()

    splash.showMessage("Loading numpy library...")
    import numpy
    splash.setValue(5)

    splash.showMessage("Loading numba library...")
    import numba
    splash.setValue(10)

    splash.showMessage("Loading pandas library...")
    import pandas
    splash.setValue(15)

    splash.showMessage("Loading pyarrow library...")
    import pyarrow
    splash.setValue(20)

    splash.showMessage("Loading igraph library...")
    import igraph
    splash.setValue(25)

    splash.showMessage("Loading scipy library...")
    import scipy
    splash.setValue(30)

    splash.showMessage("Loading lxml library...")
    import lxml
    splash.setValue(35)

    splash.showMessage("Loading sklearn library...")
    import sklearn
    splash.setValue(40)

    splash.showMessage("Loading matplotlib library...")
    import matplotlib
    splash.setValue(45)

    splash.showMessage("Loading Configuration module...")
    importlib.import_module('.config', 'metgem_app')
    splash.setValue(50)

    splash.showMessage("Loading Errors modules...")
    importlib.import_module('.errors', 'metgem_app')
    splash.setValue(55)

    splash.showMessage("Loading Logger module...")
    importlib.import_module('.logger', 'metgem_app')
    splash.setValue(60)

    splash.showMessage("Loading GraphML parser module...")
    importlib.import_module('.graphml', 'metgem_app')
    splash.setValue(65)

    splash.showMessage("Loading Databases module...")
    importlib.import_module('.database', 'metgem_app')
    splash.setValue(70)

    splash.showMessage("Loading Workers...")
    importlib.import_module('.workers', 'metgem_app')
    splash.setValue(75)

    splash.showMessage("Loading User interface...")
    importlib.import_module('.ui', 'metgem_app')
    splash.setValue(90)

    splash.showMessage("Loading Project module...")
    importlib.import_module('.save', 'metgem_app')
    splash.setValue(95)

    splash.showMessage("Loading plugins...")
    importlib.import_module('.plugins', 'metgem_app')
    splash.setValue(100)

    splash.showMessage("")

    from .config import set_debug_flag, set_jupyter_flag, set_use_opengl_flag
    set_debug_flag(args.debug)
    set_jupyter_flag(args.jupyter)
    set_use_opengl_flag(not args.disable_opengl)

    from .ui import MainWindow
    window = MainWindow()

    from .errors import exceptionHandler
    sys.excepthook = exceptionHandler

    window.show()
    splash.finish(window)

    # Support for file association
    if args.fname is not None:
        fname = args.fname
        from .config import FILE_EXTENSION
        if os.path.exists(fname) and os.path.splitext(fname)[1] == FILE_EXTENSION:
            window.load_project(fname)

    sys.exit(app.exec_())


if __name__ == '__main__':
    run()
