import datetime
import os
import webbrowser

from PyQt5 import uic
from PyQt5.QtCore import QSize, QSettings, Qt
from PyQt5.QtGui import QAbstractTextDocumentLayout, QPalette, QTextDocument
from PyQt5.QtWidgets import QWidget, QListWidgetItem, QStyledItemDelegate, QStyleOptionViewItem, QApplication, QStyle

try:
    import feedparser
except ImportError:
    HAS_FEEDPARSER = False
else:
    HAS_FEEDPARSER = True


# https://stackoverflow.com/questions/53569768
class HTMLDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super(HTMLDelegate, self).__init__(parent)
        self.doc = QTextDocument(self)

    def paint(self, painter, option, index):
        options = QStyleOptionViewItem(option)
        self.initStyleOption(options, index)

        self.doc.setHtml(options.text)
        self.doc.setTextWidth(option.rect.width())

        options.text = ""
        style = QApplication.style() if options.widget is None else options.widget.style()
        style.drawControl(QStyle.CE_ItemViewItem, options, painter)

        ctx = QAbstractTextDocumentLayout.PaintContext()

        if option.state & QStyle.State_Selected:
            ctx.palette.setColor(QPalette.Text, option.palette.color(
                    QPalette.Active, QPalette.HighlightedText))
        else:
            ctx.palette.setColor(QPalette.Text, option.palette.color(
                    QPalette.Active, QPalette.Text))

        text_rect = style.subElementRect(QStyle.SE_ItemViewItemText, options, None)

        painter.save()
        painter.translate(text_rect.topLeft())
        painter.setClipRect(text_rect.translated(-text_rect.topLeft()))
        self.doc.documentLayout().draw(painter, ctx)

        painter.restore()

    def sizeHint(self, option, index):
        options = QStyleOptionViewItem(option)
        self.initStyleOption(options, index)

        self.doc.setHtml(options.text)
        self.doc.setTextWidth(option.rect.width())

        return QSize(self.doc.idealWidth(), self.doc.size().height())


class WelcomeWidget(QWidget):
    URL_NEWS_RSS = "https://metgem.github.io/feed.xml"
    LinkRole = Qt.UserRole

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'welcome_widget.ui'), self)

        self.lstRecentProjects.clear()
        self.lstNews.clear()

        if HAS_FEEDPARSER:
            def on_enable_news_state_changed(state: bool):
                QSettings().setValue('NewsEnabled', state)
                if state:
                    self.update_news()
                else:
                    self.lstNews.clear()

            self.chkEnableNews.stateChanged.connect(on_enable_news_state_changed)
            news_enabled = QSettings().value('NewsEnabled', False, type=bool)
            self.chkEnableNews.setChecked(news_enabled)
            self.lstNews.itemClicked.connect(self.on_news_item_clicked)
        else:
            self.lblNews.setVisible(False)
            self.chkEnableNews.setVisible(False)
            self.lstNews.setVisible(False)

        self.importDataClicked = self.btImportData.clicked
        self.openProjectClicked = self.btOpenProject.clicked
        self.clearRecentProjectsClicked = self.btClearRecentProjects.clicked
        self.recentProjectsItemClicked = self.lstRecentProjects.itemClicked

    def update_news(self):
        self.lstNews.clear()
        if HAS_FEEDPARSER:
            d = feedparser.parse(self.URL_NEWS_RSS)

            delegate = HTMLDelegate(self.lstNews)
            self.lstNews.setItemDelegate(delegate)

            for item in d.get('items', []):
                title = item.get('title', None)
                description = item.get('description', '')
                pub_date = item.get('published_parsed', None)
                pub_date = datetime.datetime(*pub_date[:6])
                pub_date = f'({pub_date:%Y-%m-%d %H:%M})' if pub_date is not None else ''
                link = item.get('link', None)
                if title is not None:
                    text = (f"<span style='font-size: 12pt;'><b>{title}</b></span><br/>"
                            f"<span style='font-size: 8pt;'><i>{pub_date}</i></span><br/>"
                            f"<span style='font-size: 10pt;'>{description}</span>")
                    witem = QListWidgetItem(text)
                    witem.setData(WelcomeWidget.LinkRole, link)

                    self.lstNews.addItem(witem)

    def on_news_item_clicked(self, index):
        link = index.data(WelcomeWidget.LinkRole)
        if link is not None and isinstance(link, str):
            webbrowser.open(link)

    def addRecentProject(self, filename: str):
        self.lstRecentProjects.addItem(filename)

    def clearRecentProjects(self):
        self.lstRecentProjects.clear()

    def recentProjectItem(self, row: int):
        return self.lstRecentProjects.item(row)

    def showEvent(self, event):
        super().showEvent(event)

        count = self.lstRecentProjects.count()
        if count > 0:
            height = self.lstRecentProjects.height() / count
            for i in range(count):
                item = self.lstRecentProjects.item(i)
                item.setSizeHint(QSize(item.sizeHint().width(), height))
