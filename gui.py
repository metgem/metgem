import sys
import os
import time
import json

import numpy as np
import igraph as ig

from PyQt5.QtWidgets import (QTableWidgetItem, QDialog, QMessageBox, QWidget, 
    QGraphicsRectItem)
from PyQt5.QtCore import QSettings, Qt, QPointF
from PyQt5 import uic

from sklearn.manifold import TSNE
from tqdm import tqdm

from lib import (ui, compute_scores_from_spectra, read_mgf, generate_network)
from lib.workers import TSNEWorker, NetworkWorker

MAIN_UI_FILE = os.path.join('lib', 'ui', 'main_window.ui')
APP_NAME = 'We have to find a name...'
APP_VERSION = 0.1
DEBUG = True

MainWindowUI, MainWindowBase = uic.loadUiType(MAIN_UI_FILE, from_imports='lib.ui', import_from='lib.ui')

class tqdm_qt(tqdm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        
    def update(self, n=1):
        #TODO
        # print('update', n)
        super().update(n)
        

class MainWindow(MainWindowBase, MainWindowUI):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Create graph
        self.graph = ig.Graph()
        
        # Setup User interface
        self.setupUi(self)
        self.setWindowTitle(APP_NAME)

        # Add model to table views
        for table, Model, name in ((self.tvNodes, ui.widgets.network_view.NodesModel, "Nodes"), 
                            (self.tvEdges, ui.widgets.network_view.EdgesModel, "Edges")):
            table.setSortingEnabled(True)
            model = Model(self.graph)
            proxy = ui.widgets.network_view.ProxyModel()
            proxy.setSourceModel(model)
            table.setModel(proxy)
        
        # Move search layout to search toolbar
        w = QWidget()
        self.layoutSearch.setParent(None)
        w.setLayout(self.layoutSearch)
        self.tbSearch.addWidget(w)
        
        # Move progressbar to the statusbar
        self.widgetProgress = QWidget()
        self.layoutProgress.setParent(None)
        self.widgetProgress.setLayout(self.layoutProgress)
        self.statusBar().addPermanentWidget(self.widgetProgress)
        self.widgetProgress.setVisible(False)
        
        # Connect events
        self.gvNetwork.scene().selectionChanged.connect(self.onSelectionChanged)
        self.gvTSNE.scene().selectionChanged.connect(self.onSelectionChanged)
        self.actionQuit.triggered.connect(self.close)
        self.actionAbout.triggered.connect(self.showAbout)
        self.actionAboutQt.triggered.connect(self.showAboutQt)
        self.actionProcessFile.triggered.connect(self.showOpenFileDialog)
        self.actionZoomIn.triggered.connect(lambda: self.currentView.scaleView(1.2))
        self.actionZoomOut.triggered.connect(lambda: self.currentView.scaleView(1/1.2))
        self.actionZoomToFit.triggered.connect(self.currentView.zoomToFit)
        self.actionZoomSelectedRegion.triggered.connect(
            lambda: self.currentView.fitInView(self.currentView.scene().selectionArea().boundingRect(), Qt.KeepAspectRatio))
        self.leSearch.returnPressed.connect(self.doSearch)
        self.btSearch.pressed.connect(self.doSearch)       
        self.actionFullScreen.triggered.connect(self.switchFullScreen)
        self.actionHideSelected.triggered.connect(lambda: self.hideItems(self.currentView.scene().selectedItems()))
        self.actionShowAll.triggered.connect(lambda: self.showItems(self.currentView.scene().items()))
        self.actionNeighbors.triggered.connect(lambda: self.selectFirstNeighbors(self.currentView.scene().selectedItems()))
        self.actionExportToCytoscape.triggered.connect(self.exportToCytoscape)
        self.actionExportAsImage.triggered.connect(self.exportAsImage)
        self.actionShowFileToolbar.triggered.connect(lambda checked: self.tbFile.setVisible(checked))
        self.actionShowViewToolbar.triggered.connect(lambda checked: self.tbView.setVisible(checked))
        self.actionShowNetworkToolbar.triggered.connect(lambda checked: self.tbNetwork.setVisible(checked))
        self.actionShowExportToolbar.triggered.connect(lambda checked: self.tbExport.setVisible(checked))
        self.actionShowSearchToolbar.triggered.connect(lambda checked: self.tbSearch.setVisible(checked))
        
        # Load settings
        # TODO
        # self._settings = QSettings('CNRS', 'spectrum_similarity')
        # database = self._settings.value('database')
        # if database is not None and not os.path.exists(database):
            # self.database = self._settings.value('database')

            
    @property
    def currentView(self):
        for view in (self.gvNetwork, self.gvTSNE):
            if view.hasFocus():
                return view
        return self.gvNetwork
        
        
    def keyPressEvent(self, event):
        key = event.key()

        if key == Qt.Key_M: #Show/hide minimap
            view = self.currentView
            view.minimap.setVisible(not view.minimap.isVisible())
            
            
    def selectFirstNeighbors(self, items):
        view = self.currentView
        for item in items:
            if item.Type == ui.Node.Type:
                for v in self.graph.vs[item.index].neighbors():
                    if view == self.gvNetwork:
                        v['__network_gobj'].setSelected(True)
                    elif view == self.gvTSNE:
                        v['__tsne_gobj'].setSelected(True)
            
            
    def showItems(self, items):
        for item in items:
            item.show()
            
            
    def hideItems(self, items):
        for item in items:
            item.hide()
            
            
    def switchFullScreen(self):
        if not self.isFullScreen():
            self.setWindowFlags(Qt.Window)
            self.showFullScreen()
        else:
            self.setWindowFlags(Qt.Widget)
            self.showNormal()
        
        
    def showAbout(self):
        dialog = QMessageBox(self)
        message = ['Version: {0}'.format(APP_VERSION),
                   '',
                   'Should say something here.']
        dialog.about(self, 'About {0}'.format(APP_NAME),
                    '\n'.join(message))

        
    def showAboutQt(self):
        dialog = QMessageBox(self)
        dialog.aboutQt(self)
        
        
    def closeEvent(self, event):
        if DEBUG:
            reply = QMessageBox.Yes
        else:
            reply = QMessageBox.question(self, APP_NAME, 
                         "Do you really want to exit?",
                         QMessageBox.Yes, QMessageBox.No)
    
        if reply == QMessageBox.Yes:
            event.accept()
            self.saveSettings()
        else:
            event.ignore()

            
    def saveSettings(self):
        pass
        #TODO
        # self._settings.setValue('database', self.database)
        # del self._settings
    

    def drawNetwork(self, view, interactions):    
        view.scene().clear()
    
        nodes_idx = np.unique(np.vstack((interactions['Source'], interactions['Target'])))
        
        widths = np.array(interactions['Cosine'])
        min = max(0, widths.min() - 0.1)
        if min != widths.max():
            widths = (ui.RADIUS-1)*(widths-min)/(widths.max()-min)+1
        else:
            widths = ui.RADIUS
        
        self.graph.es['__weight'] = interactions['Cosine']
        self.graph.es['__width'] = widths
        
        # Add nodes
        group = QGraphicsRectItem() #Create a pseudo-group, QGraphicsItemGroup is not used because it does not let children handle events
        group.setZValue(1) # Draw nodes on top of edges
        for i, n in enumerate(self.graph.vs):
            node = ui.Node(i, n['__label'])
            node.setParentItem(group)
        self.graph.vs['__network_gobj'] = group.childItems()
        view.scene().addItem(group)
        self.nodes_group = group
           
        # Add edges
        group = QGraphicsRectItem()
        group.setZValue(0)
        for i, e in enumerate(self.graph.es):
            edge = ui.Edge(i, self.graph.vs['__network_gobj'][e.source], self.graph.vs['__network_gobj'][e.target], e['__weight'], e['__width'])
            edge.setParentItem(group)
        self.graph.es['__network_gobj'] = group.childItems()
        view.scene().addItem(group)
        self.edges_group = group
         
        # Compute layout
        def apply_layout(layout):
            for coord, node in zip(layout, self.graph.vs):
                node['__network_gobj'].setPos(QPointF(*coord))
                    
            view.zoomToFit()
            view.minimap.zoomToFit()
            
        def update_progress(i):
            self.progressBar.setFormat('TSNE: Iteration {:d} of {:d}'.format(i, self.progressBar.maximum()))
            self.progressBar.setValue(i)
            
        def process_finished():
            layout = self._worker.result()
            self.widgetProgress.setVisible(False)
            apply_layout(layout)
    
        self.widgetProgress.setVisible(True)
        self.progressBar.setMaximum(100)
        self._worker = NetworkWorker(self.graph)
        self._worker.updated.connect(update_progress)
        self._worker.finished.connect(process_finished)
        self.btCancelProcess.pressed.connect(self._worker.stop)
        self._worker.start()
        
        
    def drawTSNE(self, view, scores):
        view.scene().clear()
        
        # Add nodes
        group = QGraphicsRectItem() # Create a pseudo-group, QGraphicsItemGroup is not used because it does not let children handle events
        group.setZValue(1) # Draw nodes on top of edges
        for i, n in enumerate(self.graph.vs):
            node = ui.Node(i, n['__label'])
            node.setParentItem(group)
        self.graph.vs['__tsne_gobj'] = group.childItems()
        view.scene().addItem(group)
        self.nodes_group = group
         
        # Compute layout
        scores[scores<0.65] = 0
        
        mask = scores.sum(axis=0)>1
        layout = np.zeros((scores.shape[0], 2))
        
        def apply_layout(layout):
            bb = ig.Layout(layout.tolist()).bounding_box()
            dx, dy = 0, 0
            for index in np.where(~mask)[0]:
                layout[index] = (bb.left+dx, bb.height+dy)
                dx += 5
                if dx >= bb.width:
                    dx = 0
                    dy += 5
            
            layout = ig.Layout(layout.tolist())
            layout.scale(ui.RADIUS)
            for coord, node in zip(layout, self.graph.vs):
                node['__tsne_gobj'].setPos(QPointF(*coord))
                    
            view.zoomToFit()
            view.minimap.zoomToFit()
        
        if np.any(mask):
            self.widgetProgress.setVisible(True)
            
            def update_progress(i):
                self.progressBar.setFormat('TSNE: Iteration {:d} of {:d}'.format(i, self.progressBar.maximum()))
                self.progressBar.setValue(i)
                
            def process_finished():
                layout[mask] = self._worker.result()
                self.widgetProgress.setVisible(False)
                apply_layout(layout)
        
            self.progressBar.setMaximum(1000) #TODO
            self._worker = TSNEWorker(1 - scores[mask][:,mask])
            self._worker.updated.connect(update_progress)
            self._worker.finished.connect(process_finished)
            self.btCancelProcess.pressed.connect(self._worker.stop)
            self._worker.start()
        else:
            apply_layout(layout)
        
            
    def showOpenFileDialog(self):
        dialog = ui.OpenFileDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            process_file, metadata_file, tsne_options, network_options = dialog.getValues()
                
            multiprocess = False
            spectra = list(read_mgf(process_file, use_multiprocessing=multiprocess))
            scores_matrix = compute_scores_from_spectra(spectra, use_multiprocessing=multiprocess, tqdm=tqdm_qt) #, network_options)
            interactions = generate_network(scores_matrix, spectra, use_self_loops=True)

            infos = np.array([(spectrum.mz_parent,) for spectrum in spectra], dtype=[('m/z parent', np.float32)])

            nodes_idx = np.arange(scores_matrix.shape[0])
            self.createGraph(nodes_idx, infos, interactions, labels=None)
            
            self.draw(scores_matrix, interactions, infos, labels=None)
            
            
    def createGraph(self, nodes_idx, infos, interactions, labels=None):
        # Delete all previously created edges and nodes
        self.graph.delete_edges(self.graph.es)
        self.graph.delete_vertices(self.graph.vs)
        
        self.graph.add_vertices(nodes_idx.tolist())
        self.graph.add_edges(zip(interactions['Source'], interactions['Target']))
        
        if infos is not None:
            for col in infos.dtype.names:
                self.graph.vs[col] = infos[col]
                
        if interactions is not None:
            for col in interactions.dtype.names:
                self.graph.es[col] = interactions[col]

        if labels is not None:
            self.graph.vs['__label'] = labels.astype('str')
        else:
            self.graph.vs['__label'] = nodes_idx.astype('str')
            
                            
    def draw(self, scores, interactions, infos=None, labels=None):
        self.tvNodes.model().sourceModel().beginResetModel()
        self.tvEdges.model().sourceModel().beginResetModel()
            
        self.drawNetwork(self.gvNetwork, interactions)
        self.drawTSNE(self.gvTSNE, scores)
                
        self.tvNodes.model().sourceModel().endResetModel()
        self.tvEdges.model().sourceModel().endResetModel()      
        
        
    def onSelectionChanged(self):
        view = self.currentView
        items = view.scene().selectedItems()
        nodes_idx, edges_idx = [], []
        for item in items:
            if item.Type == ui.Node.Type:
                nodes_idx.append(item.index)
            elif item.Type == ui.Edge.Type:
                edges_idx.append(item.index)
        self.tvNodes.model().setSelection(nodes_idx)
        self.tvEdges.model().setSelection(edges_idx)
        
        if self.actionLinkViews.isChecked():
            if view == self.gvNetwork:
                self.gvTSNE.scene().selectionChanged.disconnect()
                self.gvTSNE.scene().clearSelection()
                for idx in nodes_idx:
                    self.graph.vs['__tsne_gobj'][idx].setSelected(True)
                self.gvTSNE.scene().selectionChanged.connect(self.onSelectionChanged)
            elif view == self.gvTSNE:
                self.gvNetwork.scene().selectionChanged.disconnect()
                self.gvNetwork.scene().clearSelection()
                for idx in nodes_idx:
                    self.graph.vs['__network_gobj'][idx].setSelected(True)
                for idx in edges_idx:
                    self.graph.es['__network_gobj'][idx].setSelected(True)
                self.gvNetwork.scene().selectionChanged.connect(self.onSelectionChanged)
                
        
    def doSearch(self):
        # t0 = time.time()
        
        # num_nodes = 0
        # num_edges = 0
        # search = self.leSearch.text()
        # for item in self.gvNetwork.scene().items():
            # if item.Type == ui.Node.Type:
                # if search in item.label:
                    # num_nodes += 1
                    # item.setSelected(True)
                # else:
                    # item.setSelected(False)
            # elif item.Type == ui.Edge.Type:
                # pass
        # print('Selected {} node(s) and {} edge(s) in {:.1f}ms'.format(num_nodes, num_edges, (time.time()-t0)*1000))
        
        # t0 = time.time()
        self.tvNodes.model().setFilterRegExp(self.leSearch.text())
        # self._tables[0].model().setFilterKeyColumn(0)
        # print('Filtered {} node(s) and {} edge(s) in {:.1f}ms'.format(num_nodes, num_edges, (time.time()-t0)*1000))

        
    def exportToCytoscape(self):
        try:
            from py2cytoscape.data.cyrest_client import CyRestClient
            
            # Create exportable copy of the graph object
            g = self.graph.copy()
            for attr in g.vs.attributes():
                if attr.startswith('__'):
                    del g.vs[attr]
                else:
                    g.vs[attr] = [str(x) for x in g.vs[attr]]
            for attr in g.es.attributes():
                if attr.startswith('__'):
                    del g.es[attr]
                else:
                    g.es[attr] = [str(x) for x in g.es[attr]]
            
            cy = CyRestClient()
            # cy.session.delete()
            g_cy = cy.network.create_from_igraph(g)
            
            # cy.layout.apply(name='force-directed', network=g_cy)
            
            layout = np.empty((g.vcount(), 2))
            for item in self.currentView.scene().items():
                if item.Type == ui.Node.Type:
                    layout[item.index] = (item.x(), item.y())
            positions = [(suid, x, y) for suid, (x, y) in zip(g_cy.get_nodes()[::-1], layout)]
            cy.layout.apply_from_presets(network=g_cy, positions=positions)
            
            with open('styles.json', 'r') as f:
                style_js = json.load(f)
            style = cy.style.create('cyREST style', style_js)
            cy.style.apply(style, g_cy)
        except ConnectionRefusedError:
            print('Please launch Cytoscape before trying to export.')
        except ImportError:
            print('py2tocytoscape is required for this action (https://pypi.python.org/pypi/py2cytoscape).')
        except FileNotFoundError:
            print('styles.json not found...')
            
        # for c in g_cy.get_view(g_cy.get_views()[0])['elements']['nodes']:
            # pos = c['position']
            # id_ = int(c['data']['id_original'])
            # nodes[id_].setPos(QPointF(pos['x'], pos['y']))
    
    
    def exportAsImage(self):
        filename, filter = QFileDialog.getSaveFileName(self, "Save image", filter="SVG Files (*.svg);;BMP Files (*.bmp);;JPEG (*.JPEG);;PNG (*.png)")
        if filename:
            if filter == 'SVG Files (*.svg)':
                try:
                    from PyQt5.QtSvg import QSvgGenerator
                except ImportError:
                    print('QtSvg was not found on your system. It is needed for SVG export.')
                else:
                    svg_gen = QSvgGenerator()

                    svg_gen.setFileName(filename)
                    svg_gen.setSize(self.size())
                    svg_gen.setViewBox(self.scene().sceneRect())
                    svg_gen.setTitle("SVG Generator Example Drawing")
                    svg_gen.setDescription("An SVG drawing created by the SVG Generator.")

                    painter = QPainter(svg_gen)
                    self.currentView.scene().render(painter)
                    painter.end()
            else:
                image = QImage(self.view.scene().sceneRect().size().toSize(), QImage.Format_ARGB32)
                image.fill(Qt.transparent)

                painter = QPainter(image)
                self.currentView.scene().render(painter);
                image.save(filename)

if __name__ == '__main__':
        from PyQt5.QtWidgets import QApplication, QMainWindow
        
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        sys.exit(app.exec_())
