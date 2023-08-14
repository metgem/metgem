from typing import Union

from PySide6.QtWidgets import QToolButton, QMenu
from PySide6.QtGui import QAction


class ToolBarMenu(QToolButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        self._menu = QMenu()
        self.setMenu(self._menu)
        self.triggered.connect(self.setDefaultAction)

    def addAction(self, action: QAction) -> QAction:
        return self.menu().addAction(action)

    def addMenu(self, *args, **kwargs) -> Union[QAction, QMenu]:
        return self.menu().addMenu(*args, **kwargs)
