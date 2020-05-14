#!/usr/bin/env python


def run():
    import os
    import sys
    import argparse
    import importlib

    # Make sure decimal separator is dot
    os.environ['LC_NUMERIC'] = 'C'

    from .version import DOMAIN, ORGANIZATION, APPLICATION, FULLVERSION

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

    from .splash import SplashScreen
    #sys.path.insert(0, os.path.dirname(__file__))
    splash = SplashScreen()
    splash.show()

    splash.showMessage("Loading numpy library...")
    import numpy
    splash.setValue(5)

    splash.showMessage("Loading pandas library...")
    import pandas
    splash.setValue(10)

    splash.showMessage("Loading pyarrow library...")
    import pyarrow
    splash.setValue(15)

    splash.showMessage("Loading igraph library...")
    import igraph
    splash.setValue(20)

    splash.showMessage("Loading scipy library...")
    import scipy
    splash.setValue(25)

    splash.showMessage("Loading lxml library...")
    import lxml
    splash.setValue(30)

    splash.showMessage("Loading sklearn library...")
    import sklearn
    splash.setValue(40)

    splash.showMessage("Loading matplotlib library...")
    import matplotlib
    splash.setValue(50)

    splash.showMessage("Loading Configuration module...")
    importlib.import_module('.config', 'metgem')
    splash.setValue(55)

    splash.showMessage("Loading Errors modules...")
    importlib.import_module('.errors', 'metgem')
    splash.setValue(60)

    splash.showMessage("Loading Logger module...")
    importlib.import_module('.logger', 'metgem')
    splash.setValue(65)

    splash.showMessage("Loading GraphML parser module...")
    importlib.import_module('.graphml', 'metgem')
    splash.setValue(70)

    splash.showMessage("Loading Databases module...")
    importlib.import_module('.database', 'metgem')
    splash.setValue(75)

    splash.showMessage("Loading User interface module...")
    importlib.import_module('.ui', 'metgem')
    splash.setValue(80)

    splash.showMessage("Loading Workers module...")
    importlib.import_module('.workers', 'metgem')
    splash.setValue(85)

    splash.showMessage("Loading Project module...")
    importlib.import_module('.save', 'metgem')
    splash.setValue(90)

    splash.showMessage("Loading plugins...")
    importlib.import_module('.plugins', 'metgem')
    splash.setValue(100)

    splash.showMessage("")

    QCoreApplication.setOrganizationDomain(DOMAIN)
    QCoreApplication.setOrganizationName(ORGANIZATION)
    QCoreApplication.setApplicationName(APPLICATION)
    QCoreApplication.setApplicationVersion(FULLVERSION)

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
        if os.path.exists(fname) and os.path.splitext(fname)[1] == config.FILE_EXTENSION:
            window.load_project(fname)

    sys.exit(app.exec_())


if __name__ == '__main__':
    run()
