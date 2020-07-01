import os

from matplotlib.backend_bases import key_press_handler
from matplotlib import rcParams
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import QToolBar, QWidgetAction


KEYMAP = {k.replace('keymap.', ''): v for k, v in rcParams.items() if k.startswith('keymap.')}
KEYMAP['pan_left'] = ['shift+left']
KEYMAP['pan_right'] = ['shift+right']
KEYMAP['zoom_in'] = ['ctrl+up']
KEYMAP['zoom_out'] = ['ctrl+down']
KEYMAP['pan_temp'] = ['shift']
KEYMAP['zoom_temp'] = ['control']


class SpectrumNavigationToolbar(NavigationToolbar):

    def __init__(self, canvas, parent=None, coordinates=True, extended_mode=False, **kwargs):
        self._extended_mode = extended_mode

        super().__init__(canvas, parent=parent, coordinates=coordinates, **kwargs)
        self.layout().setSpacing(0)

        # Initialize timers for step pan/zoom
        self._step_pan_timer = self.canvas.new_timer(interval=400)
        self._step_pan_timer.add_callback(self.push_current)
        self._step_pan_timer.single_shot = True
        self._step_zoom_timer = self.canvas.new_timer(interval=400)
        self._step_zoom_timer.add_callback(self.push_current)
        self._step_zoom_timer.single_shot = True

        # Resize toolbar with canvas
        self.canvas.mpl_connect('resize_event', self.on_resize)

        # Connect MPL events
        self.canvas.mpl_connect('key_press_event', self.on_key_press)
        self.canvas.mpl_connect('key_release_event', self.on_key_release)
        self.canvas.mpl_connect('button_press_event', self.on_button_press)
        self.canvas.mpl_connect('button_release_event', self.on_button_release)
        self.canvas.mpl_connect('scroll_event', self.on_wheel_scroll)

        # Initialize picked state
        self._xaxis_picked = False

    # noinspection PyCallByClass
    def sizeHint(self):
        return QToolBar.sizeHint(self)

    def _init_toolbar(self, *args, **kwargs):
        self.custom_basedir = os.path.join(os.path.realpath(os.path.dirname(__file__)), 'images')

        self.toolitems = [t for t in self.toolitems if
                          t[0] in ('Home', 'Back', 'Forward', None, 'Pan', 'Zoom', 'Save')]

        if self._extended_mode:
            self.toolitems.extend([('Reset', 'Reset data', 'reset', 'reset_data')])

        for i, item in enumerate(self.toolitems):
            if item[-1] is None:
                continue

            if item[-1] in KEYMAP:
                shortcuts = ', '.join(KEYMAP[item[-1]])
                if item[-1] + '_temp' in KEYMAP:
                    shortcuts_temp = ', '.join([x.title() for x in KEYMAP[item[-1] + '_temp']])
                    self.toolitems[i] = (*item[:1], f'{item[1]} [{shortcuts}, <i>{shortcuts_temp}</i>]', *item[2:])
                else:
                    self.toolitems[i] = (*item[:1], f'{item[1]} [{shortcuts}]', *item[2:])

        if self.toolitems[-1][0] is None:
            self.toolitems = self.toolitems[:-1]

        super()._init_toolbar(*args, **kwargs)

        for action in self.actions():
            if isinstance(action, QWidgetAction) and action.defaultWidget() == self.locLabel:
                self.removeAction(action)
        self.locLabel.setParent(self.canvas)
        self.locLabel.setAlignment(Qt.AlignLeft)
        self.locLabel.show()

    def on_key_press(self, event):
        # Custom shortcuts                
        if event.key in KEYMAP['pan_temp']:
            if not self._active:
                self.pan()
                self._set_cursor(event)
        elif event.key in KEYMAP['zoom_temp']:
            if not self._active:
                self.zoom()
                self._set_cursor(event)
        elif event.key in KEYMAP['pan_left'] or event.key in KEYMAP['pan_right']:
            self.step_pan(event, keypress=True)
        elif event.key in KEYMAP['zoom_in'] or event.key in KEYMAP['zoom_out']:
            self.step_zoom(event, keypress=True)

        # Handle default matplotlib shortcuts
        else:
            key_press_handler(event, self.canvas, self)

    def on_key_release(self, event):
        if event.key in KEYMAP['pan_temp'] or event.key in KEYMAP['zoom_temp']:
            if self._active == 'PAN':
                self.pan()
                self._xypress = []
                self.release_pan(event)
                self._set_cursor(event)
            elif self._active == 'ZOOM':
                self.zoom()
                self._xypress = None
                self.release_zoom(event)
                self._set_cursor(event)
        elif event.key in KEYMAP['pan_left'] or event.key in KEYMAP['pan_right']:
            self.push_current()
        elif event.key in KEYMAP['zoom_in'] or event.key in KEYMAP['zoom_out']:
            self.push_current()

    def mouse_move(self, event):
        super().mouse_move(event)

        if self._xaxis_picked and hasattr(self.canvas.axes, '_pan_start'):
            self.canvas.axes.drag_pan(event.button, 'x', event.x,
                                      event.y)  # pretend key=='x' to prevent Y axis range to change
            self.draw()

    def on_button_press(self, event):
        # If X axis is pressed, start panning
        # can't use pick event because, in pan/zoom mode, canvas is locked
        if self.canvas.axes.get_xaxis().contains(event)[0]:
            if (hasattr(self, '_views') and self._views.empty())\
                    or (hasattr(self, '_nav_stack') and self._nav_stack.empty()):
                self.push_current()
            self.canvas.axes.start_pan(event.x, event.y, event.button)
            self._xaxis_picked = True

    def on_button_release(self, event):
        # X axis was released, end panning
        if self._xaxis_picked and self.canvas.axes.get_xaxis().contains(event) \
                and hasattr(self.canvas.axes, '_pan_start') and self._active != 'PAN':
            self.canvas.axes.end_pan()
            self.push_current()

        self._xaxis_picked = False

    def on_wheel_scroll(self, event):
        if event.inaxes:
            if self._active == 'PAN':
                self.step_pan(event, keypress=False)
            elif self._active == 'ZOOM':
                self.step_zoom(event, keypress=False)

    # noinspection PyUnusedLocal,PyProtectedMember
    def on_resize(self, event):
        cwidth = self.canvas.width()
        lheight = self.locLabel.sizeHint().height()
        self.locLabel.setFixedSize(cwidth, lheight)
        bbox = self.canvas.axes.get_window_extent()
        dpi_ratio = self.canvas._dpi_ratio
        x = bbox.xmin + 5
        y = self.canvas.figure.bbox.height / dpi_ratio - bbox.ymax - lheight
        self.locLabel.move(x*dpi_ratio, y*dpi_ratio)

    # noinspection PyProtectedMember
    def _icon(self, name, *args, **kwargs):
        icon = super()._icon(name, *args, **kwargs)
        if icon.isNull():
            name = name.replace('.png', '_large.png')
            pm = QPixmap(os.path.join(self.custom_basedir, name))
            if hasattr(pm, 'setDevicePixelRatio'):
                pm.setDevicePixelRatio(self.canvas._dpi_ratio)
            return QIcon(pm)
        else:
            return icon

    def step_pan(self, event, keypress=False):
        """pan X axis with arrow keys or mouse wheel"""

        if (hasattr(self, '_views') and self._views.empty())\
                or (hasattr(self, '_nav_stack') and self._nav_stack.empty()):
            self.push_current()

        xlim = self.canvas.axes.get_xlim()

        if keypress:
            delta = -100 if event.key in KEYMAP['pan_left'] else +100
        else:
            self._step_pan_timer.stop()
            delta = -100 if event.button == 'down' else +100

        self.canvas.axes.set_xlim(xlim[0] + delta, xlim[1] + delta)
        self.draw()

        if not keypress:
            self._step_pan_timer.start()

    def drag_pan(self, event):
        event.key = 'x'  # pretend key=='x' to prevent Y axis range to change
        super().drag_pan(event)

    def release_zoom(self, event):
        event.key = 'x'  # pretend key=='x' to prevent Y axis range to change
        super().release_zoom(event)
        self.canvas.auto_adjust_ylim()

    def drag_zoom(self, event):
        event.key = 'x'  # pretend key=='x' to prevent Y axis range to change
        super().drag_zoom(event)

    def step_zoom(self, event, keypress=False):
        """zoom on X axis with arrow keys or mouse wheel"""

        if (hasattr(self, '_views') and self._views.empty())\
                or (hasattr(self, '_nav_stack') and self._nav_stack.empty()):
            self.push_current()

        xlim = self.canvas.axes.get_xlim()

        if keypress:
            delta = -50 if event.key in KEYMAP['zoom_in'] else +50
            xlim = (xlim[0] - delta, xlim[1] + delta)
        else:
            self._step_zoom_timer.stop()

            delta = 50
            if event.button == 'up':  # If we are zooming in, try to keep centered the peak under mouse
                full_range = (xlim[1] - xlim[0])
                mouse_range = event.xdata - xlim[0]
                delta_left = mouse_range - mouse_range / full_range * (full_range - 2 * delta)
                delta_right = 2 * delta - delta_left
                xlim = (xlim[0] + delta_left, xlim[1] - delta_right)
            else:
                xlim = (xlim[0] - delta, xlim[1] + delta)

        if xlim[1] > xlim[0]:
            self.canvas.axes.set_xlim(xlim)
            self.draw()

            if not keypress:
                self._step_zoom_timer.start()

    def press_zoom(self, event):
        event.key = 'x'  # pretend key=='x' to prevent Y axis range to change
        super().press_zoom(event)

    def _switch_on_zoom_mode(self, event):
        self._zoom_mode = 'x'  # pretend key=='x' to prevent Y axis range to change
        self.mouse_move(event)

    def reset_data(self):
        self.canvas.spectrum1 = None
        self.canvas.spectrum1_index = None
        self.canvas.spectrum1_parent = None
        self.canvas.spectrum2 = None
        self.canvas.spectrum2_index = None
        self.canvas.spectrum2_parent = None
        self.canvas.score = None
        self.canvas.title = None

    def enterEvent(self, event):
        super().enterEvent(event)
        self.setCursor(Qt.ArrowCursor)

    def setCursor(self, cursor):
        if self._lastCursor != cursor:
            self.canvas.setCursor(cursor)
            self._lastCursor = cursor

    def _set_cursor(self, event):
        # Mouse is over axes
        if event.inaxes:
            if self._active == 'EXCLUDE':
                self.setCursor(Qt.DragCopyCursor)
            elif self._active == 'ZOOM':
                self.setCursor(Qt.CrossCursor)
            elif self._active == 'PAN':
                self.setCursor(Qt.SizeHorCursor)
            else:
                self.setCursor(Qt.ArrowCursor)

        # Mouse is over X axis, change cursor to let user know he can pan
        elif self.canvas.axes.get_xaxis().contains(event)[0]:
            self.setCursor(Qt.SizeHorCursor)

        # Nothing special, use default cursor
        else:
            self.setCursor(Qt.ArrowCursor)
