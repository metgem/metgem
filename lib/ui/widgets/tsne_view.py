#!/usr/bin/env python
      
from sklearn.manifold import TSNE

from network_view import *        
        
if __name__ == '__main__':
    import sys
    import pandas as pd
    
    from PyQt5.QtWidgets import (QVBoxLayout, QLineEdit, QWidget, QTableView,
        QTabWidget, QSplitter, QFileDialog)
        
    class MainWindow(QWidget):

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            
            self._show_help = False
            self.scores = None
            self.label = None
            
            self.graph = ig.Graph()
            
            layout = QVBoxLayout()
            self.setLayout(layout)
            
            edit = QLineEdit()
            layout.addWidget(edit)
            
            splitter = QSplitter(Qt.Vertical)
            layout.addWidget(splitter)
            
            self.view = NetworkView()
            self.view._drawForeground = self.view.drawForeground
            self.view.drawForeground = self.drawForeground
            splitter.addWidget(self.view)

            tab = QTabWidget()
            splitter.addWidget(tab)
            self._tables = []
            for Model, name in ((NodesModel, "Nodes"), 
                                (EdgesModel, "Edges")):
                table = QTableView()
                table.setSortingEnabled(True)
                model = Model(self.graph)
                proxy = ProxyModel()
                proxy.setSourceModel(model)
                table.setModel(proxy)
                tab.addTab(table, name)
                self._tables.append(table)

            # Connect Events
            edit.returnPressed.connect(self.filter_by_label)
            self.view.scene().selectionChanged.connect(self.on_selection_changed)
            
        
        
        def exportToCytoscape(self):
            pass
        
        
        def exportAsImage(self):
            pass
            
            
        def drawForeground(self, painter, rect):
            self.view._drawForeground(painter, rect)
            
            if self._show_help:
                painter.resetTransform()
                help_text = '''
                Help
                
                C:   Export network to Cytoscape (it should be opened)
                F:   Switch to fullscreen/normal mode
                H:   Show this help text
                M:   Show/hide minimap
                P:   Show/hide pie (randomly choosen)
                S:   Save image as...
                Z:   Zoom to fit window
                +:   Zoom int
                -:   Zoom out
                Esc: Quit
                F5:  Recalculate layout
                '''
                painter.drawText(self.rect(), Qt.AlignLeft | Qt.AlignTop, help_text)

                
        def keyPressEvent(self, event):
            key = event.key()

            if key == Qt.Key_Plus:
                self.view.scaleView(1.2)
            elif key == Qt.Key_Minus:
                self.view.scaleView(1 / 1.2)
            elif key == Qt.Key_Escape:
                    self.close()
            elif key == Qt.Key_F5:
                if self.interactions is not None:
                    if self.infos is not None:
                        self.draw(self.interactions, self.infos)
                    else:
                        self.draw(self.interactions)
            elif key == Qt.Key_C:
                self.exportToCytoscape()
            elif key == Qt.Key_M:
                self.view.minimap.setVisible(not self.view.minimap.isVisible())
            elif key == Qt.Key_Z:
                self.view.zoomToFit()
            elif key == Qt.Key_F:
                if not self.isFullScreen():
                    self.setWindowFlags(Qt.Window)
                    self.showFullScreen()
                    # self.activateOpenGL()
                else:
                    self.setWindowFlags(Qt.Widget)
                    self.showNormal()
                    # self.actfivateOpenGL()
            elif key == Qt.Key_P:
                if not hasattr(self, '_pie_used'):
                    self._pie_used = False
                    
                if self._pie_used == False:
                    self._pie_used = True
                    for node in self.nodes_group.childItems():
                        pie = [random.random()/x for x in range(1, random.randint(1, 4))]
                        if len(pie) > 0:
                            pie.append(1-sum(pie))
                        node.setPie(pie)
                        node.update()
                else:
                    self._pie_used = False
                    for node in self.nodes_group.childItems():
                        node.setPie([])
                        node.update()
            elif key == Qt.Key_H:
                self._show_help = not self._show_help
                self.view.viewport().update()
            elif key == Qt.Key_S:
                self.exportAsImage()
            else:
                super().keyPressEvent(event)
                
                
        def drawNetwork(self, scores, infos=None, labels=None):
            self.scores = scores
            self.infos = infos
            self.labels = labels
        
            self.view.scene().clear()
            
            nodes_idx = np.unique(list(range(scores.shape[0])))
            
            # widths = np.array(interactions['Cosine'])
            # min = max(0, widths.min() - 0.1)
            # if min != widths.max():
                # widths = (RADIUS-1)*(widths-min)/(widths.max()-min)+1
            # else:
                # widths = RADIUS
            
            print('Creating graph...')
            g = self.graph
            g.delete_vertices(g.vs) # Delete all previously created nodes
            g.add_vertices(nodes_idx.tolist()) #[int(x) for x in nodes_idx])
            # print(interactions['Source'])
            # print(interactions['Source']-1)
            # g.add_edges(zip(interactions['Source']-1, interactions['Target']-1))
            # g.add_edges([(int(x['Source']-1), int(x['Target']-1)) for x in interactions])
            # g.es['__weight'] = interactions['Cosine']
            # g.es['__width'] = widths
            
            # if interactions is not None:
                # for col in interactions.dtype.names:
                    # g.es[col] = interactions[col]
                    
            if infos is not None:
                for col in infos.dtype.names:
                    g.vs[col] = infos[col]

            if labels is not None:
                g.vs['__label'] = labels.astype('str')
            else:
                g.vs['__label'] = nodes_idx.astype('str')
            
            print('Adding nodes...')
            group = QGraphicsRectItem() #Create a pseudo-group, QGraphicsItemGroup is not used because it does not let children handle events
            group.setZValue(1) # Draw nodes on top of edges
            for i, n in enumerate(tqdm(g.vs)):
                node = Node(i, n['__label'])
                node.setParentItem(group)
            g.vs['__gobj'] = group.childItems()
            self.view.scene().addItem(group)
            self.nodes_group = group
               
            print('Adding edges...')
            group = QGraphicsRectItem()
            group.setZValue(0)
            for e in tqdm(g.es):
                edge = Edge(g.vs['__gobj'][e.source], g.vs['__gobj'][e.target], e['__weight'], e['__width'])
                edge.setParentItem(group)
            g.es['__gobj'] = group.childItems()
            self.view.scene().addItem(group)
            self.edges_group = group
             
            print('Computing layout...') 
            scores[scores<0.65] = 0
            
            f = scores.sum(axis=0)>1
            # scores = scores[f][:,f]
            # infos = infos[f]
            X_tsne = TSNE(learning_rate=200, early_exaggeration=12, perplexity=6, verbose=2, random_state=0, metric='precomputed', method='exact').fit_transform(1 - scores[f][:,f])
            
            l = np.zeros((scores.shape[0], 2))
            l[f] = X_tsne
            
            bb = ig.Layout(l.tolist()).bounding_box()
            dx, dy = 0, 0
            for index in np.where(~f)[0]:
                l[index] = (bb.left+dx, bb.height+dy)
                dx += 5
                if dx >= bb.width:
                    dx = 0
                    dy += 5
            
            l = ig.Layout(l.tolist())
            l.scale(RADIUS)
            # print(g.vs[np.where(f)])
            for coord, node in zip(l, g.vs):
                node['__gobj'].setPos(QPointF(*coord))
                # node['__gobj'].setColor(color)
            # for x in enumerate(scores):
                # .translate(dx-bb.left, dy-bb.top)
                    
            self.view.zoomToFit()
            self.view.minimap.zoomToFit()
            
            
        def on_selection_changed(self):
            items = self.view.scene().selectedItems()
            nodes, edges = [], []
            for item in items:
                if item.Type == Node.Type:
                    nodes.append(item)
                elif item.Type == Edge.Type:
                    edges.append(item)
            self._tables[0].model().setSelectedItems(nodes)
            self._tables[1].model().setSelectedItems(edges)
            

        def filter_by_label(self):
            import time
            t0 = time.time()
            num_nodes = 0
            num_edges = 0
            search = edit.text()
            for item in self.view.scene().items():
                if item.Type == Node.Type:
                    if search in item.label:
                        num_nodes += 1
                        item.setSelected(True)
                    else:
                        item.setSelected(False)
                elif item.Type == Edge.Type:
                    pass
            print('Selected {} node(s) and {} edge(s) in {:.1f}ms'.format(num_nodes, num_edges, (time.time()-t0)*1000))
            
            t0 = time.time()
            self._tables[0].model().setFilterRegExp(edit.text())
            # self._tables[0].model().setFilterKeyColumn(0)
            print('Filtered {} node(s) and {} edge(s) in {:.1f}ms'.format(num_nodes, num_edges, (time.time()-t0)*1000))
            
            
        def draw(self, interactions, infos, labels=None):
            for table in self._tables:
                table.model().sourceModel().beginResetModel()
                
            self.drawNetwork(interactions, infos, labels)
            
            for table in self._tables:
                table.model().sourceModel().endResetModel()
                
    
    COLORS = [Qt.GlobalColor(x) for x in range(4, 19) if x != Qt.yellow]
    def get_color(index):
        return COLORS[index % len(COLORS)]
    
    app = QApplication(sys.argv)
    
    win = MainWindow()

    scores = np.array([[1.000000, 	0.891845,	0.315764,	0.554127,	0.000000],
                       [0.891845,	1.000000,	0.340032,	0.000000,	0.000000],
                       [0.315764,	0.340032,	1.000000,	0.265877,	0.000000],
                       [0.554127,	0.000000,	0.265877,	1.000000,	0.097667],
                       [0.000000,	0.000000,	0.000000,	0.097667,	1.000000]])


    infos = pd.DataFrame({'Source': [1, 2, 3, 4, 5],
                          'parent mass': [621.307, 593.276, 609.270, 545.272, 447.274]}).to_records()
    
    win.draw(scores, infos)
    
    win.show()

    sys.exit(app.exec_())