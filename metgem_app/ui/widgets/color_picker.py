from qtpy.QtCore import Qt, QSettings, Signal
from qtpy.QtGui import QIcon, QPainter, QBrush, QColor
from qtpy.QtWidgets import QToolButton, QWidgetAction, QColorDialog, QMenu, QAction, QAbstractButton, QDialogButtonBox


class ColorPicker(QToolButton):
    colorReset = Signal()

    def __init__(self, action: QAction = None, color_group=None, default_color=Qt.blue, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.last_color_action = action if action is not None else QAction(self)
        self._color_group = color_group

        dialog_action = QWidgetAction(self)
        self._dialog = QColorDialog(self)

        self.btReset = None
        button_box = self._dialog.findChild(QDialogButtonBox, "")
        if button_box is not None:
            self.btReset = button_box.addButton(QDialogButtonBox.Reset)

        self._dialog.setWindowFlags(Qt.Widget)
        self._dialog.setOptions(self._dialog.options() | QColorDialog.DontUseNativeDialog)
        dialog_action.setDefaultWidget(self._dialog)

        # Hide pick screen color button
        button = self._dialog.findChild(QAbstractButton)
        if button:
            button.hide()

        # Load custom colors
        settings = QSettings()
        settings.beginGroup("Colors")
        custom_colors = settings.value("Custom", [])
        for i, color in enumerate(custom_colors):
            self._dialog.setCustomColor(i, color)
        current_color = QColor(default_color) if color_group is None\
            else settings.value(f"{color_group}/Current", QColor(default_color))
        if current_color.isValid():
            self._dialog.setCurrentColor(current_color)
            self.on_color_selected(current_color)
        settings.endGroup()

        self._menu = menu = QMenu()
        menu.addAction(dialog_action)

        self.setMenu(menu)
        self.setPopupMode(QToolButton.MenuButtonPopup)
        self.setDefaultAction(self.last_color_action)

        # Connect events
        self.colorSelected = self._dialog.colorSelected
        if self.btReset is not None:
            self.btReset.clicked.connect(self.colorReset.emit)
        self.currentColorChanged = self._dialog.currentColorChanged
        menu.aboutToShow.connect(self._dialog.show)
        self._dialog.rejected.connect(menu.hide)
        self._dialog.colorSelected.connect(menu.hide)
        self._dialog.colorSelected.connect(self.on_color_selected)
        self.last_color_action.triggered.connect(self.on_use_last_color)

    def setIcon(self, icon: QIcon):
        super().setIcon(icon)
        self.update_icon()

    def showEvent(self, *args, **kwargs):
        self.update_icon()
        super().showEvent(*args, **kwargs)

    # noinspection PyUnusedLocal
    def on_color_selected(self, color):
        self.update_icon()
        self.save_settings()

    def save_settings(self):
        settings = QSettings()
        settings.beginGroup("Colors")
        custom_colors = [self._dialog.customColor(i) for i in range(self._dialog.customCount())]
        settings.setValue('Custom', custom_colors)
        if self._color_group is not None:
            settings.setValue(f"{self._color_group}/Current", self._dialog.currentColor())

    def update_icon(self):
        """Show selected color on top-left edge of icon"""

        current_icon = self.icon()
        icon = QIcon()
        for size in current_icon.availableSizes():
            pixmap = current_icon.pixmap(size)
            painter = QPainter(pixmap)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(self._dialog.currentColor()))
            painter.drawEllipse(0, 0, int(size.width() / 4), int(size.height() / 4))
            painter.end()
            icon.addPixmap(pixmap)
        super().setIcon(icon)

    def on_use_last_color(self):
        self.colorSelected.emit(self._dialog.currentColor())
