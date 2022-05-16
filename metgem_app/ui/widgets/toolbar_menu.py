from typing import Union

from qtpy.QtWidgets import QToolButton, QMenu, QAction


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
