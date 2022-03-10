import os

from matplotlib import rcParams
rcParams["toolbar"] = "toolmanager"

from matplotlib.backend_tools import ToolBase
from matplotlib.backends.backend_qt5agg import FigureManagerQT as FigureManager

# noinspection PyUnresolvedReferences
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QWidget, QHBoxLayout, QSizePolicy, QVBoxLayout, QLabel

from .canvas import SpectrumCanvas

KEYMAP = {k.replace('keymap.', ''): v for k, v in rcParams.items() if k.startswith('keymap.')}
KEYMAP['pan_left'] = ['shift+left']
KEYMAP['pan_right'] = ['shift+right']
KEYMAP['zoom_in'] = ['ctrl+up']
KEYMAP['zoom_out'] = ['ctrl+down']
KEYMAP['pan_temp'] = ['shift']
KEYMAP['zoom_temp'] = ['control']


class ResetTool(ToolBase):
    image = os.path.join(os.path.realpath(os.path.dirname(__file__)), 'images', 'reset.png')

    def trigger(self, sender, event, data=None):
        self.canvas.spectrum1 = None
        self.canvas.spectrum1_index = None
        self.canvas.spectrum1_parent = None
        self.canvas.spectrum2 = None
        self.canvas.spectrum2_index = None
        self.canvas.spectrum2_parent = None
        self.canvas.score = None
        self.canvas.title = None


class SpectrumWidget(QWidget):

    def __init__(self, *args, extended_mode=False, orientation=Qt.Horizontal, **kwargs):
        super().__init__(*args, **kwargs)

        self.canvas = SpectrumCanvas(self)
        self.manager = FigureManager(self.canvas, 0)
        self.toolbar = self.manager.toolbar
        if extended_mode:
            self.manager.toolmanager.add_tool('reset', ResetTool)
            self.toolbar.add_tool('reset', 'io', -1)
        self.tools = self.manager.toolmanager.tools

        self.toolbar.setOrientation(orientation)
        self.toolbar.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.toolbar.layout().setSpacing(0)

        # Move message label inside the canvas
        self.locLabel = QLabel(self.canvas)
        self.locLabel.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.locLabel.setSizePolicy(
            QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Ignored))
        self.toolbar.set_message = lambda _: None
        self.toolbar.toolmanager.toolmanager_connect('tool_message_event',
                                                     lambda e: self.locLabel.setText(e.message))

        layout = QHBoxLayout() if orientation == Qt.Vertical else QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.setAlignment(self.toolbar, Qt.AlignHCenter)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        # Initialize timers for step pan/zoom
        self._step_pan_timer = self.canvas.new_timer(interval=400)
        self._step_pan_timer.add_callback(self.tools['viewpos'].push_current)
        self._step_pan_timer.single_shot = True
        self._step_zoom_timer = self.canvas.new_timer(interval=400)
        self._step_zoom_timer.add_callback(self.tools['viewpos'].push_current)
        self._step_zoom_timer.single_shot = True

        # Resize toolbar with canvas
        self.canvas.mpl_connect('resize_event', self.on_resize)

        # Connect MPL events
        self.canvas.mpl_connect('key_press_event', self.on_key_press)
        self.canvas.mpl_connect('key_release_event', self.on_key_release)
        self.canvas.mpl_connect('button_press_event', self.on_button_press)
        self.canvas.mpl_connect('button_release_event', self.on_button_release)
        self.canvas.mpl_connect('scroll_event', self.on_wheel_scroll)
        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)

        # Initialize picked state
        self._xaxis_picked = False

    def on_key_press(self, event):
        # Custom shortcuts
        active = self.toolbar.toolmanager.active_toggle['default']
        if event.key in KEYMAP['pan_temp']:
            if not active:
                self.toolbar.toolmanager.trigger_tool('pan')
        elif event.key in KEYMAP['zoom_temp']:
            if not active:
                self.toolbar.toolmanager.trigger_tool('zoom')
        elif event.key in KEYMAP['pan_left'] or event.key in KEYMAP['pan_right']:
            self.step_pan(event, keypress=True)
        elif event.key in KEYMAP['zoom_in'] or event.key in KEYMAP['zoom_out']:
            self.step_zoom(event, keypress=True)

    def on_key_release(self, event):
        active = self.toolbar.toolmanager.active_toggle['default']
        if event.key in KEYMAP['pan_temp'] or event.key in KEYMAP['zoom_temp']:
            if active == 'pan':
                self.toolbar.toolmanager.trigger_tool('pan')
            elif active == 'zoom':
                self.toolbar.toolmanager.trigger_tool('zoom')
        elif event.key in KEYMAP['pan_left'] or event.key in KEYMAP['pan_right']:
            self.push_current()
        elif event.key in KEYMAP['zoom_in'] or event.key in KEYMAP['zoom_out']:
            self.push_current()

    def on_mouse_move(self, event):
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
        active = self.toolbar.toolmanager.active_toggle['default']
        if self._xaxis_picked and self.canvas.axes.get_xaxis().contains(event) \
                and hasattr(self.canvas.axes, '_pan_start') and active != 'pan':
            self.canvas.axes.end_pan()
            self.push_current()

        self._xaxis_picked = False

    def on_wheel_scroll(self, event):
        if event.inaxes:
            active = self.toolbar.toolmanager.active_toggle['default']
            if active == 'pan':
                self.step_pan(event, keypress=False)
            elif active == 'zoom':
                self.step_zoom(event, keypress=False)

    # noinspection PyUnusedLocal,PyProtectedMember
    def on_resize(self, event):
        cwidth = self.canvas.width()
        lheight = self.locLabel.sizeHint().height()
        self.locLabel.setFixedSize(cwidth, lheight)
        bbox = self.canvas.axes.get_window_extent()
        dpi_ratio = self.canvas.device_pixel_ratio
        x = bbox.xmin + 5
        y = self.canvas.figure.bbox.height / dpi_ratio - bbox.ymax - lheight
        self.locLabel.move(x*dpi_ratio, y*dpi_ratio)

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

    @property
    def spectrum1_parent(self):
        # noinspection PyPropertyAccess
        return self.canvas.spectrum1_parent

    @spectrum1_parent.setter
    def spectrum1_parent(self, mz):
        self.canvas.spectrum1_parent = mz

    def set_spectrum1(self, data, idx=None, parent=None):
        if data is not None:
            self.canvas.spectrum1_index = idx
            self.canvas.spectrum1_parent = parent
            self.canvas.spectrum1 = data
        else:
            self.canvas.spectrum1_index = None
            self.canvas.spectrum1_parent = None
            self.canvas.spectrum1 = None

    def set_spectrum2(self, data, idx=None, parent=None):
        if data is not None:
            self.canvas.spectrum2_index = idx
            self.canvas.spectrum2_parent = parent
            self.canvas.spectrum2 = data
        else:
            self.canvas.spectrum2_index = None
            self.canvas.spectrum2_parent = None
            self.canvas.spectrum2 = None

    def set_title(self, title):
        self.canvas.title = title

    def __getattr__(self, item):
        return getattr(self.canvas, item)


class ExtendedSpectrumWidget(SpectrumWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, extended_mode=True, orientation=Qt.Horizontal, **kwargs)
