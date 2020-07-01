#!/usr/bin/env python


############################################################################
#
# Copyright (C) 2013 Riverbank Computing Limited
# Copyright (C) 2010 Hans-Peter Jansen <hpj@urpla.net>.
# Copyright (C) 2010 Nokia Corporation and/or its subsidiary(-ies).
# All rights reserved.
#
# This file is part of the examples of PyQt.
#
# $QT_BEGIN_LICENSE:BSD$
# You may use this file under the terms of the BSD license as follows:
#
# "Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#   * Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in
#     the documentation and/or other materials provided with the
#     distribution.
#   * Neither the name of Nokia Corporation and its Subsidiary(-ies) nor
#     the names of its contributors may be used to endorse or promote
#     products derived from this software without specific prior written
#     permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."
# $QT_END_LICENSE$
#
############################################################################

import math

from PyQt5.QtCore import QPointF, QSize, Qt
from PyQt5.QtGui import QPainter, QPolygonF, QColor
from PyQt5.QtWidgets import (QAbstractItemView, QApplication, QStyle,
                             QStyledItemDelegate, QTableWidget, QTableWidgetItem)


class StarRating:

    PAINTING_SCALE_FACTOR = 20

    def __init__(self):
        super().__init__()

        self._max_rating = 3

        self.__polygon = QPolygonF([QPointF(1.0, 0.5)])
        for i in range(5):
            self.__polygon << QPointF(0.5 + 0.5 * math.cos(0.8 * i * math.pi),
                                      0.5 + 0.5 * math.sin(0.8 * i * math.pi))

    def paint(self, painter, rect, value):
        painter.save()

        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(Qt.NoPen)

        if value == 1:
            painter.setBrush(QColor(255, 215, 0))
        elif value == 2:
            painter.setBrush(QColor(192, 192, 192))
        elif value == 3:
            painter.setBrush(QColor(205, 127, 50))

        y_offset = (rect.height() - self.PAINTING_SCALE_FACTOR) / 2
        painter.translate(rect.x(), rect.y() + y_offset)
        painter.scale(self.PAINTING_SCALE_FACTOR, self.PAINTING_SCALE_FACTOR)

        for i in range(self._max_rating):
            if i < self._max_rating - value + 1 and self.__polygon.boundingRect().width() * (i+1) \
                                                    * self.PAINTING_SCALE_FACTOR < rect.width():
                painter.drawPolygon(self.__polygon, Qt.WindingFill)

            painter.translate(1.0, 0.0)

        painter.restore()

    def sizeHint(self):
        return self.PAINTING_SCALE_FACTOR * QSize(self._max_rating, 1)


class LibraryQualityDelegate(QStyledItemDelegate):

    def __init__(self):
        super().__init__()

        self._star_rating = StarRating()

    # noinspection PyShadowingNames
    def paint(self, painter, option, index):
        rating = index.data()

        try:
            rating = int(rating)
        except (ValueError, TypeError):
            super().paint(painter, option, index)
        else:
            if option.state & QStyle.State_Selected:
                painter.fillRect(option.rect, option.palette.highlight())

            self._star_rating.paint(painter, option.rect, rating)

    def sizeHint(self, option, index):
        return self._star_rating.sizeHint()

    def minimumSizeHint(self, option, index):
        return self.sizeHint(option, index)


if __name__ == '__main__':

    import sys

    app = QApplication(sys.argv)

    w = QTableWidget(3, 2)
    w.setItemDelegateForColumn(1, LibraryQualityDelegate())
    w.setSelectionBehavior(QAbstractItemView.SelectRows)

    headerLabels = ("Molecule", "Quality")
    w.setHorizontalHeaderLabels(headerLabels)

    data = (("Theophyllin", 1),
            ("Etamycin", 3),
            ("Antanapeptin", 2))

    for row, (mol, rating) in enumerate(data):
        item0 = QTableWidgetItem(mol)
        item1 = QTableWidgetItem(rating)
        item1.setData(0, rating)
        w.setItem(row, 0, item0)
        w.setItem(row, 1, item1)

    w.resizeColumnsToContents()
    w.resize(500, 300)
    w.show()

    sys.exit(app.exec_())
