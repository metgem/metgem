from typing import Union

from PyQt5.QtWidgets import QToolButton, QMenu, QAction


def enumerateMenu(menu: QMenu):
    for action in menu.actions():
        if action.menu() is not None:
            yield from enumerateMenu(action.menu())
        elif not action.isSeparator():
            yield action


class ToolBarMenu(QToolButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setPopupMode(QToolButton.MenuButtonPopup)
        self.setMenu(QMenu())
        self.triggered.connect(self.setDefaultAction)

    def addAction(self, action: QAction) -> QAction:
        return self.menu().addAction(action)

    def addMenu(self, *args, **kwargs) -> Union[QAction, QMenu]:
        return self.menu().addMenu(*args, **kwargs)

    def enumerateMenu(self):
        yield from enumerateMenu(self.menu())
