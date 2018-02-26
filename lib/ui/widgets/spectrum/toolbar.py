import os

from matplotlib.backend_bases import key_press_handler
from matplotlib import rcParams
from matplotlib.patches import Rectangle
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

from PyQt5.QtCore import QPropertyAnimation, QEasingCurve, Qt, QPoint
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import QWidgetAction

KEYMAP = {k.replace('keymap.', ''): v for k, v in rcParams.items() if k.startswith('keymap.')}
KEYMAP['pan_left'] = ['shift+left']
KEYMAP['pan_right'] = ['shift+right']
KEYMAP['zoom_in'] = ['ctrl+up']
KEYMAP['zoom_out'] = ['ctrl+down']
KEYMAP['pan_temp'] = ['shift']
KEYMAP['zoom_temp'] = ['control']


class SpectrumNavigationToolbar(NavigationToolbar):                 
    
    def __init__(self, *args, **kwargs):
    
        self._idPick = None
        self._idWheel = None
        self._ids_exclude_range = []
        
        # Initialize NavigationToolbar
        super().__init__(*args, coordinates=True, **kwargs)
        
        # Initialize timers for step pan/zoom
        self._step_pan_timer = self.canvas.new_timer(interval=400)
        self._step_pan_timer.add_callback(self.push_current)
        self._step_pan_timer.single_shot = True
        self._step_zoom_timer = self.canvas.new_timer(interval=400)
        self._step_zoom_timer.add_callback(self.push_current)
        self._step_zoom_timer.single_shot = True
        
        # Tune toolbar a bit
        self.setStyleSheet('''
            QToolBar
            {
                background: #fff;
                border: 1px solid #ccc;
                border-top: none;
                border-bottom-left-radius: 6px;
                border-bottom-right-radius: 6px;
                spacing: 2px;
                padding: 8px;
            }''')
        
        # Resize toolbar with canvas
        self.canvas.mpl_connect('resize_event', self.on_resize)
        
        # Connect MPL events
        self.canvas.mpl_connect('key_press_event', self.on_key_press)
        self.canvas.mpl_connect('key_release_event', self.on_key_release)
        self.canvas.mpl_connect('button_press_event', self.on_button_press)
        self.canvas.mpl_connect('button_release_event', self.on_button_release)
        self.canvas.mpl_connect('scroll_event', self.on_wheel_scroll)
        self.canvas.mpl_connect('figure_leave_event', lambda e: self.fold())
        
        # Connect Qt events
        self.canvas.dataLoaded.connect(self.onDataLoaded)

        # Add rectangle on canvas for mass range exclusion
        self.mass_excl_rect = Rectangle([0, 0], 0, 0, facecolor='r', alpha=0.1)
        
        # Define fold/unfold animations
        self.unfold_anim = QPropertyAnimation(self, b'pos')
        self.unfold_anim.setDuration(250)
        self.unfold_anim.setEasingCurve(QEasingCurve.InCubic)
        self.fold_anim = QPropertyAnimation(self, b'pos')
        self.fold_anim.setDuration(1000)
        self.fold_anim.setEasingCurve(QEasingCurve.OutCubic)
        
        # Set toolbar initial folded state
        self._folded = True
        
        # Initialize picked state
        self._xaxis_picked = False
        self._mass_range_picked = [False, False]
        self._threshold_picked = False
        
    def _init_toolbar(self):
        self.custom_basedir = os.path.join(os.path.realpath(os.path.dirname(__file__)), 'images')

        self.toolitems = [t for t in self.toolitems if
                 t[0] in ('Home', 'Back', 'Forward', None, 'Pan', 'Zoom')]
        
        for i, item in enumerate(self.toolitems):
            if item[-1] is None:
                continue
            
            if item[-1] in KEYMAP:
                shortcuts = ', '.join(KEYMAP[item[-1]])
                if item[-1] + '_temp' in KEYMAP:
                    shortcuts_temp = ', '.join([x.title() for x in KEYMAP[item[-1] + '_temp']])
                    self.toolitems[i] = (*item[:1], item[1] + ' [{}, <i>{}</i>]'.format(shortcuts, shortcuts_temp), *item[2:])
                else:
                    self.toolitems[i] = (*item[:1], item[1] + ' [{}]'.format(shortcuts), *item[2:])
        
        if self.toolitems[-1][0] == None:
            self.toolitems = self.toolitems[:-1]
            
        super()._init_toolbar()

        for action in self.actions():
            if isinstance(action, QWidgetAction) and action.defaultWidget() == self.locLabel:
                self.removeAction(action)
        self.locLabel.setParent(self.canvas)
        self.locLabel.setAlignment(Qt.AlignLeft)
        self.locLabel.show()
        
    def isFolded(self):
        return self._folded
        
    def unfold(self, start=None):
        if self.isFolded():
            pos = self.pos()
            if start is None:
                start = QPoint(pos.x(), 5-self.height())
            stop = QPoint(pos.x(), 0)
            
            self.unfold_anim.setStartValue(start)
            self.unfold_anim.setEndValue(stop)
            
            self.move(start)
            super().show()
            
            self.fold_anim.stop()
            self.unfold_anim.start()
            
            self._folded = False
        
    def fold(self):
        if not self.isFolded() and self.fold_anim.state() != QPropertyAnimation.Running:
            pos = self.pos()
            start = QPoint(pos.x(), 0)
            stop = QPoint(pos.x(), 5-self.height())
            
            self.fold_anim.setStartValue(start)
            self.fold_anim.setKeyValueAt(0.75, start)
            self.fold_anim.setEndValue(stop)
            
            self.move(start)
            
            self.unfold_anim.stop()
            self.fold_anim.start()
            
            self._folded = True
        
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
        
        # If panning, adjust line threshold width
        if self._xaxis_picked and hasattr(self.canvas.axes, '_pan_start'):
            self.canvas.axes.drag_pan(event.button, 'x', event.x, event.y) # pretend key=='x' to prevent Y axis range to change
            self.draw()
           
        # Event is in axes
        elif event.inaxes:
            # If threshold selector is picked, set threshold
            if self._threshold_picked:
                self.canvas.threshold = event.ydata

            # If mass range selector is picked, set mass range
            if self._mass_range_picked[0]:
                self.canvas.massRange = (event.xdata, self.canvas._mass_range[1])
            elif self._mass_range_picked[1]:
                self.canvas.massRange = (self.canvas._mass_range[0], event.xdata)
        
        
        # Mouse is inside toolbar region but toolbar is folded, so unfold it
        if (not event.inaxes
          and event.y > self.canvas.height() - self.height()/2
          and self.x() < event.x < self.x() + self.width()):
            self.unfold()
            
        # Fold toolbar
        else:
            self.fold()
            
    def on_button_press(self, event):
        # If X axis is pressed, start panning
        if self.canvas.axes.get_xaxis().contains(event)[0]: # can't use pick event because, in pan/zoom mode, canvas is locked
            if self._views.empty():
                self.push_current()
            self.canvas.axes.start_pan(event.x, event.y, event.button)
            self._xaxis_picked = True
    
    def on_button_release(self, event):
        # X axis was released, end panning
        if self._xaxis_picked and self.canvas.axes.get_xaxis().contains(event) and hasattr(self.canvas.axes, '_pan_start') and self._active != 'PAN':
            self.canvas.axes.end_pan()
            self.push_current()
           
        self._xaxis_picked = False
        self._mass_range_picked = [False, False]
        self._threshold_picked = False
        
    def on_wheel_scroll(self, event):
        if event.inaxes:
            if self._active == 'PAN':
                self.step_pan(event, keypress=False)
            elif self._active == 'ZOOM':
                self.step_zoom(event, keypress=False)
    
    def on_resize(self, event):
        cwidth = self.canvas.width()
        size_hint = self.sizeHint()
        min_width = min(cwidth, size_hint.width())
        
        self.fold_anim.stop()
        self.unfold_anim.stop()
        
        size_hint.setWidth(min_width)
        self.setFixedSize(size_hint)
        
        x = (cwidth-min_width)/2
        y = 5 - self.height() if self.isFolded() else 0
        self.move(x, y)
        
        lheight = self.locLabel.sizeHint().height()
        self.locLabel.setFixedSize(cwidth, lheight)
        bbox = self.canvas.axes.get_window_extent()
        dpi_ratio = self.canvas._dpi_ratio
        x = bbox.xmin + 5
        y = self.canvas.figure.bbox.height / dpi_ratio - bbox.ymax - lheight
        self.locLabel.move(x*dpi_ratio, y*dpi_ratio)
        
    def onDataLoaded(self):
        self.locLabel.show()

    def _icon(self, name):
        icon = super()._icon(name)
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
        
        if self._views.empty():
            self.push_current()
        
        xlim = self.canvas.axes.get_xlim()
        
        if keypress:
            delta = -100 if event.key in KEYMAP['pan_left'] else +100
        else:
            self._step_pan_timer.stop()
            delta = -100 if event.button=='down' else +100
            
        self.canvas.axes.set_xlim(xlim[0]+delta, xlim[1]+delta)
        self.draw()

        if not keypress:
            self._step_pan_timer.start()
    
    def drag_pan(self, event):
        event.key = 'x' # pretend key=='x' to prevent Y axis range to change
        super().drag_pan(event)
        
    def release_zoom(self, event):
        event.key = 'x' # pretend key=='x' to prevent Y axis range to change
        super().release_zoom(event)
        self.canvas.autoAdjustYLim()
        
    def drag_zoom(self, event):
        event.key = 'x' # pretend key=='x' to prevent Y axis range to change
        super().drag_zoom(event)
        
    def step_zoom(self, event, keypress=False):
        """zoom on X axis with arrow keys or mouse wheel"""
        
        if self._views.empty():
            self.push_current()
        
        xlim = self.canvas.axes.get_xlim()

        if keypress:
            delta = -50 if event.key in KEYMAP['zoom_in'] else +50
            xlim = (xlim[0] - delta, xlim[1] + delta)
        else:
            self._step_zoom_timer.stop()

            delta = 50
            if event.button == 'up': # If we are zooming in, try to keep centered the peak under mouse
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
        event.key = 'x' # pretend key=='x' to prevent Y axis range to change
        super().press_zoom(event)
        
    def _switch_on_zoom_mode(self, event):
        self._zoom_mode = 'x' # pretend key=='x' to prevent Y axis range to change
        self.mouse_move(event)
        
    def close_file(self):
        self.canvas.closeFile()
            
    def enterEvent(self, event):
        super().enterEvent(event)
        self.unfold(start=self.pos())
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
        elif (self.canvas.axes.get_xaxis().contains(event)[0]
            and not self._threshold_picked and not True in self._mass_range_picked):
            
            self.setCursor(Qt.SizeHorCursor)
        
        # Nothing special, use default cursor
        else:
            self.setCursor(Qt.ArrowCursor)
