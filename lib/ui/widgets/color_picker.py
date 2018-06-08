from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QIcon, QPainter, QPixmap, QBrush
from PyQt5.QtWidgets import QToolButton, QWidgetAction, QColorDialog, QMenu, QAction


class ColorPicker(QToolButton):
    def __init__(self, action: QAction = None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._last_color = None
        last_color_action = action if action is not None else QAction(self)
        self._default_icon = last_color_action.icon()

        dialog_action = QWidgetAction(self)
        dialog = QColorDialog()
        dialog.setWindowFlags(Qt.Widget)
        dialog_action.setDefaultWidget(dialog)

        menu = QMenu()
        menu.addAction(dialog_action)

        self.setMenu(menu)
        self.setPopupMode(QToolButton.MenuButtonPopup)
        self.setDefaultAction(last_color_action)

        # Connect events
        self.colorSelected = dialog.colorSelected
        self.currentColorChanged = dialog.currentColorChanged
        menu.aboutToShow.connect(dialog.show)
        dialog.rejected.connect(menu.hide)
        dialog.colorSelected.connect(menu.hide)
        dialog.colorSelected.connect(self.on_color_selected)
        last_color_action.triggered.connect(self.on_use_last_color)

    def setIcon(self, icon: QIcon):
        self._default_icon = icon
        super().setIcon(icon)

    def on_color_selected(self, color):
        self._last_color = color

        icon = QIcon()
        for size in self._default_icon.availableSizes():
            pixmap = self._default_icon.pixmap(size)
            painter = QPainter(pixmap)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(color))
            painter.drawEllipse(0, 0, size.width()/4, size.height()/4)
            painter.end()
            icon.addPixmap(pixmap)
        super().setIcon(icon)

    def on_use_last_color(self):
        if self._last_color is not None:
            self.colorSelected.emit(self._last_color)
