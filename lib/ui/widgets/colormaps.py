from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel


class ColorMapFrame(QFrame):
    def __init__(self, text, pixmap, **kwargs):
        super().__init__(**kwargs)

        hbox = QHBoxLayout()
        hbox.addWidget(QLabel(text, self))
        px_label = QLabel(self)
        px_label.setPixmap(pixmap)
        hbox.addWidget(px_label)
        self.setLayout(hbox)
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
        self.setStyleSheet("QFrame::hover {background-color:palette(highlight);}")
