#!/usr/bin/env python


def main():
    import os
    import sys

    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import QCoreApplication

    app = QApplication(sys.argv)

    from version import DOMAIN, ORGANIZATION, APPLICATION, FULLVERSION
    from splash import splash

    QCoreApplication.setOrganizationDomain(DOMAIN)
    QCoreApplication.setOrganizationName(ORGANIZATION)
    QCoreApplication.setApplicationName(APPLICATION)
    QCoreApplication.setApplicationVersion(FULLVERSION)

    from lib.ui import MainWindow
    window = MainWindow()

    from lib.errors import exceptionHandler
    sys.excepthook = exceptionHandler

    window.show()
    splash.finish(window)

    from lib.config import FILE_EXTENSION

    # Support for file association
    if len(sys.argv) > 1:
        fname = sys.argv[1]
        if os.path.exists(fname) and os.path.splitext(fname)[1] == FILE_EXTENSION:
            window.load_project(fname)

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
