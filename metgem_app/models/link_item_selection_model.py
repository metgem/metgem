#     Copyright (C) 2010 Klarälvdalens Datakonsult AB,
#         a KDAB Group company, info@kdab.net,
#         author Stephen Kelly <stephen@kdab.com>
#     Copyright (c) 2016 Ableton AG <info@ableton.com>
#         Author Stephen Kelly <stephen.kelly@ableton.com>
#     This library is free software; you can redistribute it and/or modify it
#     under the terms of the GNU Library General Public License as published by
#     the Free Software Foundation; either version 2 of the License, or (at your
#     option) any later version.
#     This library is distributed in the hope that it will be useful, but WITHOUT
#     ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
#     FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Library General Public
#     License for more details.
#     You should have received a copy of the GNU Library General Public License
#     along with this library; see the file COPYING.LIB.  If not, write to the
#     Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
#     02110-1301, USA.

# Python Port of KLinkItemSelectionModel and KModelIndexProxyMapper from KDAB

from PySide6.QtCore import (QModelIndex, Signal, QItemSelectionModel, QItemSelection, QObject,
                          QAbstractItemModel, QAbstractProxyModel)

from typing import Union


# https://github.com/KDAB/GammaRay/blob/master/3rdparty/kde/kmodelindexproxymapper.cpp
class ModelIndexProxyMapper(QObject):
    isConnectedChanged = Signal()

    def __init__(self, leftModel: QAbstractItemModel, rightModel: QAbstractItemModel, parent: QObject):
        super().__init__(parent)
        self._left_model = leftModel
        self._right_model = rightModel
        self._proxy_chain_down = []
        self._proxy_chain_up = []
        self.connected = False
        self.createProxyChain()

    # def assertSelectionValid(self, selection: QItemSelection) -> bool:
    #     for r in selection:
    #         if not r.isValid():
    #             print(selection, self._left_model, self._right_model, self._proxy_chain_down, self._proxy_chain_up)
    #         assert r.isValid()
    #     return True

    # The idea here is that this selection model and proxySelectionModel might be in different parts of the
    # proxy chain. We need to build up to two chains of proxy models to create mappings between them.
    #
    #  Example 1:
    #
    #     Root model
    #        |
    #      /    \
    #  Proxy 1   Proxy 3
    #     |       |
    #  Proxy 2   Proxy 4
    #
    # Need Proxy 1 and Proxy 2 in one chain, and Proxy 3 and 4 in the other.
    #
    #  Example 2:
    #
    #   Root model
    #       |
    #      Proxy 1
    #        |
    #      Proxy 2
    #      /     \
    #  Proxy 3   Proxy 6
    #     |       |
    #  Proxy 4   Proxy 7
    #     |
    #  Proxy 5
    #
    #  We first build the chain from 1 to 5, then start building the chain from 7 to 1.
    #  We stop when we find that proxy 2 is already in the first chain.
    #
    #   Stephen Kelly, 30 March 2010.
    #
    def createProxyChain(self):
        for proxy in self._proxy_chain_up:
            # noinspection PyArgumentList
            proxy.disconnect(self)
        for proxy in self._proxy_chain_down:
            # noinspection PyArgumentList
            proxy.disconnect(self)

        self._proxy_chain_up = []
        self._proxy_chain_down = []

        proxy_chain_down = []
        selection_target_proxy_model = self._right_model
        while selection_target_proxy_model is not None:
            proxy_chain_down.insert(0, selection_target_proxy_model)

            if isinstance(selection_target_proxy_model, QAbstractProxyModel):
                # noinspection PyUnresolvedReferences
                selection_target_proxy_model.sourceModelChanged.connect(self.createProxyChain)
                selection_target_proxy_model = selection_target_proxy_model.sourceModel()
            else:
                selection_target_proxy_model = None

            if selection_target_proxy_model == self._left_model:
                self._proxy_chain_down = proxy_chain_down
                self.checkConnected()
                return

        source_proxy_model = self._left_model
        while source_proxy_model is not None:
            self._proxy_chain_up.append(source_proxy_model)

            if isinstance(source_proxy_model, QAbstractProxyModel):
                # noinspection PyUnresolvedReferences
                source_proxy_model.sourceModelChanged.connect(self.createProxyChain)
                source_proxy_model = source_proxy_model.sourceModel()
            else:
                source_proxy_model = None

            try:
                target_index = proxy_chain_down.index(source_proxy_model)
            except ValueError:
                pass
            else:
                self._proxy_chain_down = proxy_chain_down[target_index + 1:]
                self.checkConnected()
                return

        self._proxy_chain_down = proxy_chain_down
        self.checkConnected()

    def checkConnected(self):
        konami_right = self._left_model if not self._proxy_chain_up else self._proxy_chain_up[-1].sourceModel()
        konami_left = self._right_model if not self._proxy_chain_down else self._proxy_chain_down[0].sourceModel()
        self.setConnected(konami_left and (konami_left == konami_right))

    def setConnected(self, connected: bool):
        if self.connected != connected:
            self.connected = connected
            self.isConnectedChanged.emit()

    def isConnected(self):
        return self.connected

    def mapLeftToRight(self, index: QModelIndex) -> QModelIndex:
        selection = self.mapSelectionLeftToRight(QItemSelection(index, index))
        if not selection.indexes():
            return QModelIndex()
        return selection.indexes()[0]

    def mapRightToLeft(self, index: QModelIndex) -> QModelIndex:
        selection = self.mapSelectionRightToLeft(QItemSelection(index, index))
        if not selection.indexes():
            return QModelIndex()
        return selection.indexes()[0]

    def mapSelectionLeftToRight(self, selection: QItemSelection) -> QItemSelection:
        if not selection.indexes() or not self.connected:
            return QItemSelection()

        if selection[0].model() != self._left_model:
            print("FAIL", selection[0].model(), self._left_model, self._right_model)
        # assert selection[0].model() == self._left_model

        seek_selection = selection
        # assert self.assertSelectionValid(seek_selection)
        for proxy in self._proxy_chain_up:
            if not proxy:
                return QItemSelection()
            # assert seek_selection.isEmpty() or seek_selection[0].model() == proxy
            seek_selection = proxy.mapSelectionToSource(seek_selection)
            # assert seek_selection.isEmpty() or seek_selection[0].model() == proxy.sourceModel()

            # assert self.assertSelectionValid(seek_selection)

        for proxy in self._proxy_chain_down:
            if not proxy:
                return QItemSelection()

            # assert seek_selection.isEmpty() or seek_selection[0].model() == proxy.sourceModel()
            seek_selection = proxy.mapSelectionFromSource(seek_selection)
            # assert seek_selection.isEmpty() or seek_selection[0].model() == proxy

            # assert self.assertSelectionValid(seek_selection)

        return seek_selection

    def mapSelectionRightToLeft(self, selection: QItemSelection) -> QItemSelection:
        if not selection.indexes() or not self.connected:
            return QItemSelection()

        if selection[0].model() != self._right_model:
            print("FAIL", selection[0].model(), self._left_model, self._right_model)
        # assert selection[0].model() == self._right_model

        seek_selection = selection
        # assert self.assertSelectionValid(seek_selection)

        for proxy in self._proxy_chain_down[::-1]:
            if not proxy:
                return QItemSelection()
            seek_selection = proxy.mapSelectionToSource(seek_selection)
            # assert self.assertSelectionValid(seek_selection)

        for proxy in self._proxy_chain_up[::-1]:
            if not proxy:
                return QItemSelection()
            seek_selection = proxy.mapSelectionFromSource(seek_selection)
            # assert self.assertSelectionValid(seek_selection)

        return seek_selection


# https://github.com/KDAB/GammaRay/blob/master/3rdparty/kde/klinkitemselectionmodel.cpp
class LinkItemSelectionModel(QItemSelectionModel):
    linkedItemSelectionModelChanged = Signal()

    # noinspection PyUnresolvedReferences
    def __init__(self, model: QAbstractItemModel, proxy_selector: QItemSelectionModel, parent: QObject = None):
        self._index_mapper = None
        self._linked_item_selection_model = None
        self._ignore_current_changed = False

        super().__init__(model, parent)
        self.setLinkedItemSelectionModel(proxy_selector)

        self.currentChanged.connect(self.slotCurrentChanged)
        self.modelChanged.connect(self.reinitializeIndexMapper)

    # def assertSelectionValid(selection: QItemSelection) -> bool:
    #     for r in selection:
    #         if not r.isValid():
    #             print(selection)
    #         assert r.isValid()
    #     return True

    def reinitializeIndexMapper(self):
        self._index_mapper = None

        if not self.model() or not self._linked_item_selection_model or not self._linked_item_selection_model.model():
            return

        self._index_mapper = ModelIndexProxyMapper(self.model(), self._linked_item_selection_model.model(), self)
        mapped_selection = self._index_mapper.mapSelectionRightToLeft(self._linked_item_selection_model.selection())
        self.select(mapped_selection, QItemSelectionModel.ClearAndSelect)

    def linkedItemSelectionModel(self) -> QItemSelectionModel:
        return self._linked_item_selection_model

    # noinspection PyUnresolvedReferences
    def setLinkedItemSelectionModel(self, selection_model: QItemSelectionModel):
        if self._linked_item_selection_model != selection_model:
            if self._linked_item_selection_model:
                self._linked_item_selection_model.disconnect()

            self._linked_item_selection_model = selection_model

            if self._linked_item_selection_model:
                self._linked_item_selection_model.selectionChanged.connect(self.sourceSelectionChanged)
                self._linked_item_selection_model.currentChanged.connect(self.sourceCurrentChanged)
                self._linked_item_selection_model.modelChanged.connect(self.reinitializeIndexMapper)
            self.reinitializeIndexMapper()
            self.linkedItemSelectionModelChanged.emit()

    def select(self, index_or_selection: Union[QModelIndex, QItemSelection],
               command: QItemSelectionModel.SelectionFlags):

        if isinstance(index_or_selection, QModelIndex):
            index = index_or_selection

            # When an item is removed, the current index is set to the top index in the model.
            # That causes a selectionChanged signal with a selection which we do not want.
            if self._ignore_current_changed:
                return

            # Do *not* replace next line with: super().select(index, command)
            #
            # Doing so would end up calling
            # LinkItemSelectionModel.select(QItemSelection, QItemSelectionModel.SelectionFlags)
            #
            # This is because the code for
            # QItemSelectionModel.select(QModelIndex, QItemSelectionModel.SelectionFlags) looks like this:
            # {
            #     QItemSelection selection(index, index);
            #     select(selection, command);
            # }
            # So it calls LinkItemSelectionModel overload of
            # select(QItemSelection, QItemSelectionModel.SelectionFlags)
            #
            # When this happens and the selection flags include Toggle, it causes the
            # selection to be toggled twice.
            super().select(QItemSelection(index, index), command)
            if index.isValid():
                self._linked_item_selection_model.select(
                    self._index_mapper.mapSelectionLeftToRight(QItemSelection(index, index)), command)
            else:
                self._linked_item_selection_model.clearSelection()

        elif isinstance(index_or_selection, QItemSelection):
            selection = index_or_selection
            self._ignore_current_changed = True
            super().select(selection, command)
            # assert self.assertSelectionValid(selection)
            mapped_selection = self._index_mapper.mapSelectionLeftToRight(selection)
            # assert self.assertSelectionValid(mapped_selection)
            self._linked_item_selection_model.select(mapped_selection, command)
            self._ignore_current_changed = False

    def slotCurrentChanged(self, current: QModelIndex):
        mapped_current = self._index_mapper.mapLeftToRight(current)
        if not mapped_current.isValid():
            return
        self._linked_item_selection_model.setCurrentIndex(mapped_current, QItemSelectionModel.NoUpdate)

    def sourceSelectionChanged(self, selected: QItemSelection, deselected: QItemSelection):
        # assert self.assertSelectionValid(selected)
        # assert self.assertSelectionValid(deselected)
        mapped_deselection = self._index_mapper.mapSelectionRightToLeft(deselected)
        mapped_selection = self._index_mapper.mapSelectionRightToLeft(selected)

        self.select(mapped_deselection, QItemSelectionModel.Deselect)
        self.select(mapped_selection, QItemSelectionModel.Select)

    def sourceCurrentChanged(self, current: QModelIndex):
        mapped_current = self._index_mapper.mapRightToLeft(current)
        if not mapped_current.isValid():
            return
        self.setCurrentIndex(mapped_current, QItemSelectionModel.NoUpdate)
