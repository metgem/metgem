from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QLabel

from metgem_app.ui.widgets.delegates import StarRating


class HTMLLabel(QLabel):
    LINK = '{}'

    def setProperty(self, name, value):
        if name == 'text':
            value = self.LINK.format(value)

        super().setProperty(name, value)

    def setText(self, value):
        self.setProperty('text', value)


class PubMedLabel(HTMLLabel):
    LINK = "<a href='http://www.ncbi.nlm.nih.gov/pubmed/?term={0}'>{0}</a>"


class SpectrumIdLabel(HTMLLabel):
    LINK = "<a href='https://gnps.ucsd.edu/ProteoSAFe/gnpslibraryspectrum.jsp?SpectrumID={0}'>{0}</a>"


class SubmitUserLabel(HTMLLabel):
    LINK = "<a href='https://gnps.ucsd.edu/ProteoSAFe/user/summary.jsp?user={0}'>{0}</a>"


class QualityLabel(QLabel):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._star_rating = StarRating()

    def paintEvent(self, event):
        try:
            rating = int(self.text())
        except (ValueError, TypeError):
            super().paintEvent(event)
        else:
            painter = QPainter(self)
            self._star_rating.paint(painter, self.rect(), rating)

    def sizeHint(self):
        return self._star_rating.sizeHint()

    def minimumSize(self):
        return self.sizeHint()