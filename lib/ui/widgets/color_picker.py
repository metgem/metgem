from PyQt5.QtCore import Qt, QSettings, pyqtSignal
from PyQt5.QtGui import QIcon, QPainter, QBrush, QColor
from PyQt5.QtWidgets import QToolButton, QWidgetAction, QColorDialog, QMenu, QAction, QAbstractButton, QDialogButtonBox


class ColorPicker(QToolButton):
    colorReset = pyqtSignal()

    def __init__(self, action: QAction = None, color_group=None, default_color=Qt.blue, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.last_color_action = action if action is not None else QAction(self)
        self._color_group = color_group

        dialog_action = QWidgetAction(self)
        self.dialog = QColorDialog()

        self.btReset = None
        button_box = self.dialog.findChild(QDialogButtonBox, "")
        if button_box is not None:
            self.btReset = button_box.addButton(QDialogButtonBox.Reset)

        self.dialog.setWindowFlags(Qt.Widget)
        self.dialog.setOptions(self.dialog.options() | QColorDialog.DontUseNativeDialog)
        dialog_action.setDefaultWidget(self.dialog)

        # Hide pick screen color button
        button = self.dialog.findChild(QAbstractButton)
        if button:
            button.hide()

        # Load custom colors
        settings = QSettings()
        settings.beginGroup("Colors")
        custom_colors = settings.value("Custom", [])
        for i, color in enumerate(custom_colors):
            self.dialog.setCustomColor(i, color)
        current_color = QColor(default_color) if color_group is None\
            else settings.value(f"{color_group}/Current", QColor(default_color), type=QColor)
        if current_color.isValid():
            self.dialog.setCurrentColor(current_color)
            self.on_color_selected(current_color)
        settings.endGroup()

        menu = QMenu()
        menu.addAction(dialog_action)

        self.setMenu(menu)
        self.setPopupMode(QToolButton.MenuButtonPopup)
        self.setDefaultAction(self.last_color_action)

        # Connect events
        self.colorSelected = self.dialog.colorSelected
        if self.btReset is not None:
            self.btReset.clicked.connect(self.colorReset.emit)
        self.currentColorChanged = self.dialog.currentColorChanged
        menu.aboutToShow.connect(self.dialog.show)
        self.dialog.rejected.connect(menu.hide)
        self.dialog.colorSelected.connect(menu.hide)
        self.dialog.colorSelected.connect(self.on_color_selected)
        self.last_color_action.triggered.connect(self.on_use_last_color)

    def setIcon(self, icon: QIcon):
        super().setIcon(icon)
        self.update_icon()

    def showEvent(self, *args, **kwargs):
        self.update_icon()
        super().showEvent(*args, **kwargs)

    def on_color_selected(self, color):
        self.update_icon()
        self.save_settings()

    def save_settings(self):
        settings = QSettings()
        settings.beginGroup("Colors")
        custom_colors = [self.dialog.customColor(i) for i in range(self.dialog.customCount())]
        settings.setValue('Custom', custom_colors)
        if self._color_group is not None:
            settings.setValue(f"{self._color_group}/Current", self.dialog.currentColor())

    def update_icon(self):
        """Show selected color on top-left edge of icon"""

        current_icon = self.icon()
        icon = QIcon()
        for size in current_icon.availableSizes():
            pixmap = current_icon.pixmap(size)
            painter = QPainter(pixmap)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(self.dialog.currentColor()))
            painter.drawEllipse(0, 0, int(size.width() / 4), int(size.height() / 4))
            painter.end()
            icon.addPixmap(pixmap)
        super().setIcon(icon)

    def on_use_last_color(self):
        self.colorSelected.emit(self.dialog.currentColor())
