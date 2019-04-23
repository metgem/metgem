#!/usr/bin/env python


def main():
    import os
    import sys
    import argparse

    from version import DOMAIN, ORGANIZATION, APPLICATION, FULLVERSION

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

    from splash import splash

    QCoreApplication.setOrganizationDomain(DOMAIN)
    QCoreApplication.setOrganizationName(ORGANIZATION)
    QCoreApplication.setApplicationName(APPLICATION)
    QCoreApplication.setApplicationVersion(FULLVERSION)

    from lib import config
    config.set_debug_flag(args.debug)
    config.set_jupyter_flag(args.jupyter)
    config.set_use_opengl_flag(not args.disable_opengl)

    from lib.ui import MainWindow
    window = MainWindow()

    from lib.errors import exceptionHandler
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
    main()
