#!/usr/bin/env python

if __name__ == '__main__':
    import os
    import sys

    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import QCoreApplication

    app = QApplication(sys.argv)

    from lib.splash import splash

    QCoreApplication.setOrganizationDomain("CNRS")
    QCoreApplication.setOrganizationName("ICSN")
    QCoreApplication.setApplicationName("tsne-network")
    QCoreApplication.setApplicationVersion("0.1")

    from lib.ui import MainWindow
    window = MainWindow()

    from lib.errors import exceptionHandler
    sys.excepthook = exceptionHandler

    window.show()
    splash.finish(window)

    # Support for file association
    if len(sys.argv) > 1:
        fname = sys.argv[1]
        if os.path.exists(fname) and os.path.splitext(fname)[1] == '.mnz':
            window.load_project(fname)

    sys.exit(app.exec_())
