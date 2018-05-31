from PyQt5.QtWidgets import QToolButton, QMenu, QAction


class ToolBarMenu(QToolButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setPopupMode(QToolButton.MenuButtonPopup)
        self.setMenu(QMenu())
        self.triggered.connect(self.setDefaultAction)

    def addAction(self, action: QAction):
        self.menu().addAction(action)
