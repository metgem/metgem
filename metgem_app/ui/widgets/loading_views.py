import os

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QMovie, QPainter
from PySide6.QtWidgets import QListView, QListWidget, QTableView, QTableWidget, QTreeView, QTreeWidget

LOADING_MOVIE = os.path.join(os.path.dirname(__file__), 'images', 'loading.gif')


class LoadingViewMixin:

    def __init__(self, parent=None, loading_text='Loading...',
                 loading_flags=Qt.AlignCenter, movie=LOADING_MOVIE):
        super().__init__(parent)
        self._movie = QMovie(movie)
        self._movie.setScaledSize(QSize(12, 12))
        self._movie.frameChanged.connect(self.viewport().update)

        self._loading = False
        self._loading_text = loading_text
        self._loading_flags = loading_flags
        self._scroll_policy = self.verticalScrollBarPolicy()

    def loading(self):
        return self._loading

    def setLoading(self, value):
        self._loading = bool(value)
        if self._loading:
            self.blockSignals(True)
            self._movie.start()
            super().setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        else:
            self._movie.stop()
            super().setVerticalScrollBarPolicy(self._scroll_policy)
            self.viewport().update()
            self.blockSignals(False)

    def setVerticalScrollBarPolicy(self, policy):
        self._scroll_policy = self.verticalScrollBarPolicy()
        super().setVerticalScrollBarPolicy(policy)

    def loadingText(self):
        return self._loading_text

    def setLoadingText(self, value):
        self._loading_text = value

    def paintEvent(self, event):
        # If loading flag is set, model is being populated, show a waiting animation
        if self._loading:
            painter = QPainter(self.viewport())
            pixmap = self._movie.currentPixmap()

            fm = self.fontMetrics()
            if self._loading_flags == Qt.AlignLeft:
                pix_pos = self.rect().translated(
                    self.width() / 2 - fm.width(self._loading_text) / 2 - pixmap.width() - 3,
                    self.height() / 2 - pixmap.height() / 2).topLeft()
                text_rect = self.rect()
            else:
                pix_pos = self.rect().translated(-pixmap.width() / 2, pixmap.height() / 2).center()
                text_rect = self.rect().translated(0, -fm.height() / 2)
            painter.drawPixmap(pix_pos, pixmap)
            painter.drawText(text_rect, Qt.AlignCenter, self._loading_text)

        # If model is empty, show a placeholder text
        elif self.model() is None or self.model().rowCount() == 0:
            painter = QPainter(self.viewport())

            painter.drawText(self.rect(), Qt.AlignCenter, 'No data')

        else:
            super().paintEvent(event)

    def keyPressEvent(self, event):
        # No keypress event allowed when loading flag is set
        if not self._loading:
            super().keyPressEvent(event)

    def wheelEvent(self, event):
        # No wheel event allowed when loading flag is set
        if not self._loading:
            super().wheelEvent(event)


class LoadingListView(LoadingViewMixin, QListView):
    pass


class LoadingListWidget(LoadingViewMixin, QListWidget):
    pass


class LoadingTableView(LoadingViewMixin, QTableView):
    pass


class LoadingTableWidget(LoadingViewMixin, QTableWidget):
    pass


class LoadingTreeView(LoadingViewMixin, QTreeView):
    pass


class LoadingTreeWidget(LoadingViewMixin, QTreeWidget):
    pass
