from PyQt5.QtGui import QColor, QImage, QPixmap
import matplotlib.cm as mplcm
import numpy as np

COLORMAPS = ['auto', 'viridis', 'cividis', 'plasma', 'inferno', 'magma',
             'Pastel1', 'Pastel2', 'Paired', 'Accent',
             'Dark2', 'Set1', 'Set2', 'Set3',
             'tab10', 'tab20', 'tab20b', 'tab20c',
             'jet', 'rainbow', 'terrain', 'CMRmap', 'gnuplot', 'gnuplot2', 'hsv', 'gist_rainbow',
             'spring', 'summer', 'autumn', 'winter', 'cool', 'Wistia', 'hot', 'copper',
             'Greys', 'Purples', 'Blues', 'Greens', 'Oranges', 'Reds']


# https://wiki.qt.io/Color_palette_generator
# https://martin.ankerl.com/2009/12/09/how-to-create-random-colors-programmatically/
# noinspection PyCallByClass,PyTypeChecker
def generate_colors(n):
    """Generate list of `n` colors"""

    golden_ratio = 0.618033988749895  # 1/phi
    step = int(golden_ratio * 360 / n)
    return [QColor.fromHsv(step * i, 254, 254, 255) for i in range(n)]


def get_colors(n, cmap='auto'):
    if cmap == 'auto':
        return generate_colors(n)
    else:
        try:
            cm = mplcm.get_cmap(cmap)
        except ValueError:
            return []
        if isinstance(cm, mplcm.colors.ListedColormap) and cm.N < 256:
            step = 1
        else:
            step = 256 // (n - 1)
        return [QColor(*cm(i * step, bytes=True)) for i in range(n)]


# https://gist.github.com/ChrisBeaumont/4025831
# noinspection PyArgumentList
def cmap2pixmap(cmap, steps=50):
    """Convert a maplotlib colormap into a QPixmap
    :param cmap: The colormap to use
    :type cmap: Matplotlib colormap instance (e.g. matplotlib.cm.gray)
    :param steps: The number of color steps in the output. Default=50
    :type steps: int
    :rtype: QPixmap
    """
    if cmap == 'auto':
        colors = generate_colors(steps)
    else:
        norm = mplcm.colors.Normalize(vmin=0., vmax=1.)
        sm = mplcm.ScalarMappable(norm=norm, cmap=cmap)
        inds = np.linspace(0, 1, steps)
        colors = [QColor(*c) for c in sm.to_rgba(inds, bytes=True)]

    im = QImage(steps, 1, QImage.Format_Indexed8)
    im.setColorTable([c.rgba() for c in colors])
    for i in range(steps):
        im.setPixel(i, 0, i)
    im = im.scaled(72, 18)
    return QPixmap.fromImage(im)
