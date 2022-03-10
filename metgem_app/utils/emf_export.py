#    Copyright (C) 2009 Jeremy S. Sanders
#    Email: Jeremy Sanders <jeremy@jeremysanders.net>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program; if not, write to the Free Software Foundation, Inc.,
#    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
##############################################################################

# https://github.com/veusz/veusz/blob/master/veusz/document/emf_export.py

try:
    import pyemf
except ImportError:
    HAS_EMF_EXPORT = False
else:
    HAS_EMF_EXPORT = True

import struct

from qtpy.QtCore import QByteArray, QBuffer, QIODevice, Qt, QRectF
from qtpy.QtGui import QPaintEngine, QPainterPath, QPaintDevice

if HAS_EMF_EXPORT:
    inch_mm = 25.4
    scale = 100


    def isStockObject(obj):
        """Is this a stock windows object."""
        return (obj & 0x80000000) != 0


    # noinspection PyProtectedMember
    class _EXTCREATEPEN(pyemf.emr._EXTCREATEPEN):
        """Extended pen creation record with custom line style."""

        typedef = [
            ('i', 'handle', 0),
            ('i', 'offBmi', 0),
            ('i', 'cbBmi', 0),
            ('i', 'offBits', 0),
            ('i', 'cbBits', 0),
            ('i', 'style'),
            ('i', 'penwidth'),
            ('i', 'brushstyle'),
            ('i', 'color'),
            ('i', 'brushhatch', 0),
            ('i', 'numstyleentries')]

        def __init__(self, style=pyemf.PS_SOLID, width=1, color=0,
                     styleentries=[]):
            """Create pen.
            styleentries is a list of dash and space lengths."""

            super().__init__()
            self.style = style
            self.penwidth = width
            self.color = pyemf._normalizeColor(color)
            self.brushstyle = 0x0  # solid

            if style & pyemf.PS_STYLE_MASK != pyemf.PS_USERSTYLE:
                styleentries = []

            self.numstyleentries = len(styleentries)
            if styleentries:
                self.unhandleddata = struct.pack(
                    "i" * self.numstyleentries, *styleentries)

        def hasHandle(self):
            return True


    class EMFPaintEngine(QPaintEngine):
        """Custom EMF paint engine."""

        def __init__(self, rect: QRectF, dpi=75):
            QPaintEngine.__init__(self,
                                  QPaintEngine.Antialiasing |
                                  QPaintEngine.PainterPaths |
                                  QPaintEngine.PrimitiveTransform |
                                  QPaintEngine.PaintOutsidePaintEvent |
                                  QPaintEngine.PatternBrush)
            self.rect = rect
            self.dpi = dpi

        def begin(self, paintdevice):
            self.emf = pyemf.EMF(self.rect.width(), self.rect.height(), int(self.dpi * scale))
            self.emf.dc.setPixelSize([[int(self.rect.x() * self.dpi), int(self.rect.y() * self.dpi)],
                                      [int(self.rect.width() * self.dpi), int(self.rect.height() * self.dpi)]])
            self.pen = self.emf.GetStockObject(pyemf.BLACK_PEN)
            self.pencolor = (0, 0, 0)
            self.brush = self.emf.GetStockObject(pyemf.NULL_BRUSH)

            self.paintdevice = paintdevice
            return True

        def drawLines(self, lines):
            """Draw lines to emf output."""

            for line in lines:
                self.emf.Polyline(
                    [(int(line.x1() * scale), int(line.y1() * scale)),
                     (int(line.x2() * scale), int(line.y2() * scale))])

        def drawPolygon(self, points, mode):
            """Draw polygon on output."""
            pts = [(int(p.x() * scale), int(p.y() * scale)) for p in points]

            if mode == QPaintEngine.PolylineMode:
                self.emf.Polyline(pts)
            else:
                self.emf.SetPolyFillMode({QPaintEngine.WindingMode:
                                              pyemf.WINDING,
                                          QPaintEngine.OddEvenMode:
                                              pyemf.ALTERNATE,
                                          QPaintEngine.ConvexMode:
                                              pyemf.WINDING}.get(mode))
                self.emf.Polygon(pts)

        def drawEllipse(self, rect):
            """Draw an ellipse."""
            args = (int(rect.left() * scale), int(rect.top() * scale),
                    int(rect.right() * scale), int(rect.bottom() * scale),
                    int(rect.left() * scale), int(rect.top() * scale),
                    int(rect.left() * scale), int(rect.top() * scale))
            self.emf.Pie(*args)
            self.emf.Arc(*args)

        def drawPoints(self, points):
            """Draw points."""

            for pt in points:
                x, y = (pt.x() - 0.5) * scale, (pt.y() - 0.5) * scale
                self.emf.Pie(int(x), int(y),
                             int((pt.x() + 0.5) * scale), int((pt.y() + 0.5) * scale),
                             int(x), int(y), int(x), int(y))

        # noinspection PyProtectedMember
        def drawPixmap(self, r, pixmap, sr):
            """Draw pixmap to display."""

            # convert pixmap to BMP format
            bytearr = QByteArray()
            buf = QBuffer(bytearr)
            buf.open(QIODevice.WriteOnly)
            pixmap.save(buf, "BMP")

            # chop off bmp header to get DIB
            bmp = bytes(buf.data())
            dib = bmp[0xe:]
            hdrsize, = struct.unpack('<i', bmp[0xe:0x12])
            dataindex, = struct.unpack('<i', bmp[0xa:0xe])
            datasize, = struct.unpack('<i', bmp[0x22:0x26])

            epix = pyemf.emr._STRETCHDIBITS()
            epix.rclBounds_left = int(r.left() * scale)
            epix.rclBounds_top = int(r.top() * scale)
            epix.rclBounds_right = int(r.right() * scale)
            epix.rclBounds_bottom = int(r.bottom() * scale)
            epix.xDest = int(r.left() * scale)
            epix.yDest = int(r.top() * scale)
            epix.cxDest = int(r.width() * scale)
            epix.cyDest = int(r.height() * scale)
            epix.xSrc = int(sr.left())
            epix.ySrc = int(sr.top())
            epix.cxSrc = int(sr.width())
            epix.cySrc = int(sr.height())

            epix.dwRop = 0xcc0020  # SRCCOPY
            offset = epix.format.minstructsize + 8
            epix.offBmiSrc = offset
            epix.cbBmiSrc = hdrsize
            epix.offBitsSrc = offset + dataindex - 0xe
            epix.cbBitsSrc = datasize
            epix.iUsageSrc = 0x0  # DIB_RGB_COLORS

            epix.unhandleddata = dib

            self.emf._append(epix)

        def _createPath(self, path):
            """Convert qt path to emf path"""
            self.emf.BeginPath()
            count = path.elementCount()
            i = 0

            while i < count:
                e = path.elementAt(i)
                if e.type == QPainterPath.MoveToElement:
                    self.emf.MoveTo(int(e.x * scale), int(e.y * scale))
                elif e.type == QPainterPath.LineToElement:
                    self.emf.LineTo(int(e.x * scale), int(e.y * scale))
                elif e.type == QPainterPath.CurveToElement:
                    e1 = path.elementAt(i + 1)
                    e2 = path.elementAt(i + 2)
                    params = ((int(e.x * scale), int(e.y * scale)),
                              (int(e1.x * scale), int(e1.y * scale)),
                              (int(e2.x * scale), int(e2.y * scale)))
                    self.emf.PolyBezierTo(params)

                    i += 2
                else:
                    assert False

                i += 1

            ef = path.elementAt(0)
            el = path.elementAt(count - 1)
            if ef.x == el.x and ef.y == el.y:
                self.emf.CloseFigure()

            self.emf.EndPath()

        def drawPath(self, path):
            """Draw a path on the output."""

            self._createPath(path)
            self.emf.StrokeAndFillPath()

        def drawTextItem(self, pt, textitem):
            """Convert text to a path and draw it.
            """

            path = QPainterPath()
            path.addText(pt, textitem.font(), textitem.text())

            fill = self.emf.CreateSolidBrush(self.pencolor)
            self.emf.SelectObject(fill)
            self._createPath(path)
            self.emf.FillPath()
            self.emf.SelectObject(self.brush)
            self.emf.DeleteObject(fill)

        def end(self):
            return True

        def saveFile(self, filename):
            self.emf.save(filename)

        # noinspection PyProtectedMember
        def _updatePen(self, pen):
            """Update the pen to the currently selected one."""

            # line style
            style = {Qt.NoPen: pyemf.PS_NULL,
                     Qt.SolidLine: pyemf.PS_SOLID,
                     Qt.DashLine: pyemf.PS_DASH,
                     Qt.DotLine: pyemf.PS_DOT,
                     Qt.DashDotLine: pyemf.PS_DASHDOT,
                     Qt.DashDotDotLine: pyemf.PS_DASHDOTDOT,
                     Qt.CustomDashLine: pyemf.PS_USERSTYLE}[pen.style()]

            if style != pyemf.PS_NULL:
                # set cap style
                style |= {Qt.FlatCap: pyemf.PS_ENDCAP_FLAT,
                          Qt.SquareCap: pyemf.PS_ENDCAP_SQUARE,
                          Qt.RoundCap: pyemf.PS_ENDCAP_ROUND}[pen.capStyle()]

                # set join style
                style |= {Qt.MiterJoin: pyemf.PS_JOIN_MITER,
                          Qt.BevelJoin: pyemf.PS_JOIN_BEVEL,
                          Qt.RoundJoin: pyemf.PS_JOIN_ROUND,
                          Qt.SvgMiterJoin: pyemf.PS_JOIN_MITER}[pen.joinStyle()]

                # use proper widths of lines
                style |= pyemf.PS_GEOMETRIC

            width = int(pen.widthF() * scale)
            qc = pen.color()
            color = (qc.red(), qc.green(), qc.blue())
            self.pencolor = color

            if pen.style() == Qt.CustomDashLine:
                # make an extended pen if we need a custom dash pattern
                dash = [int(pen.widthF() * scale * f) for f in pen.dashPattern()]
                newpen = self.emf._appendHandle(
                    _EXTCREATEPEN(style,
                                  width=width, color=color,
                                  styleentries=dash))
            else:
                # use a standard create pen
                newpen = self.emf.CreatePen(style, width, color)
            self.emf.SelectObject(newpen)

            # delete old pen if it is not a stock object
            if not isStockObject(self.pen):
                self.emf.DeleteObject(self.pen)
            self.pen = newpen

        def _updateBrush(self, brush):
            """Update to selected brush."""

            style = brush.style()
            qc = brush.color()
            color = (qc.red(), qc.green(), qc.blue())
            # print "brush", color
            if style == Qt.SolidPattern:
                newbrush = self.emf.CreateSolidBrush(color)
            elif style == Qt.NoBrush:
                newbrush = self.emf.GetStockObject(pyemf.NULL_BRUSH)
            else:
                try:
                    hatch = {Qt.HorPattern: pyemf.HS_HORIZONTAL,
                             Qt.VerPattern: pyemf.HS_VERTICAL,
                             Qt.CrossPattern: pyemf.HS_CROSS,
                             Qt.BDiagPattern: pyemf.HS_BDIAGONAL,
                             Qt.FDiagPattern: pyemf.HS_FDIAGONAL,
                             Qt.DiagCrossPattern:
                                 pyemf.HS_DIAGCROSS}[brush.style()]
                except KeyError:
                    newbrush = self.emf.CreateSolidBrush(color)
                else:
                    newbrush = self.emf.CreateHatchBrush(hatch, color)
            self.emf.SelectObject(newbrush)

            if not isStockObject(self.brush):
                self.emf.DeleteObject(self.brush)
            self.brush = newbrush

        def _updateClipPath(self, path, operation):
            """Update clipping path."""
            # print "clip"
            if operation != Qt.NoClip:
                self._createPath(path)
                clipmode = {
                    Qt.ReplaceClip: pyemf.RGN_COPY,
                    Qt.IntersectClip: pyemf.RGN_AND,
                }[operation]
            else:
                # is this the only wave to get rid of clipping?
                self.emf.BeginPath()
                self.emf.MoveTo(0, 0)
                w = int(self.rect.width() * self.dpi * scale)
                h = int(self.rect.height() * self.dpi * scale)
                self.emf.LineTo(w, 0)
                self.emf.LineTo(w, h)
                self.emf.LineTo(0, h)
                self.emf.CloseFigure()
                self.emf.EndPath()
                clipmode = pyemf.RGN_COPY

            self.emf.SelectClipPath(mode=clipmode)

        def _updateTransform(self, m):
            """Update transformation."""
            self.emf.SetWorldTransform(m.m11(), m.m12(),
                                       m.m21(), m.m22(),
                                       m.dx() * scale, m.dy() * scale)

        def updateState(self, state):
            """Examine what has changed in state and call apropriate function."""
            ss = state.state()
            if ss & QPaintEngine.DirtyPen:
                self._updatePen(state.pen())
            if ss & QPaintEngine.DirtyBrush:
                self._updateBrush(state.brush())
            if ss & QPaintEngine.DirtyClipPath:
                self._updateClipPath(state.clipPath(), state.clipOperation())
            if ss & QPaintEngine.DirtyClipRegion:
                path = QPainterPath()
                path.addRegion(state.clipRegion())
                self._updateClipPath(path, state.clipOperation())
            if ss & QPaintEngine.DirtyTransform:
                self._updateTransform(state.transform())

        def type(self):
            return QPaintEngine.PostScript


    class EMFPaintDevice(QPaintDevice):
        """Paint device for EMF paint engine."""

        def __init__(self, rect: QRectF, dpi=75):
            super().__init__()
            self.engine = EMFPaintEngine(rect, dpi=dpi)

        def paintEngine(self):
            return self.engine

        def metric(self, m):
            """Return the metrics of the painter."""
            if m == QPaintDevice.PdmWidth:
                return int(self.engine.rect.width() * self.engine.dpi)
            elif m == QPaintDevice.PdmHeight:
                return int(self.engine.rect.height() * self.engine.dpi)
            elif m == QPaintDevice.PdmWidthMM:
                return int(self.engine.rect.width() * inch_mm)
            elif m == QPaintDevice.PdmHeightMM:
                return int(self.engine.rect.height() * inch_mm)
            elif m == QPaintDevice.PdmNumColors:
                return 2147483647
            elif m == QPaintDevice.PdmDepth:
                return 24
            elif m == QPaintDevice.PdmDpiX:
                return int(self.engine.dpi)
            elif m == QPaintDevice.PdmDpiY:
                return int(self.engine.dpi)
            elif m == QPaintDevice.PdmPhysicalDpiX:
                return int(self.engine.dpi)
            elif m == QPaintDevice.PdmPhysicalDpiY:
                return int(self.engine.dpi)
            elif m == QPaintDevice.PdmDevicePixelRatio:
                return 1

            # Qt >= 5.6
            elif m == getattr(QPaintDevice, 'PdmDevicePixelRatioScaled', -1):
                return 1

            else:
                # fall back
                return super().metric(self, m)
