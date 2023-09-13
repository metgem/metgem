import sys

import numpy as np
import igraph as ig
import pandas as pd
from PySide6.QtCore import Signal, Qt, QObject
from PySide6.QtGui import QPen
from PySide6.QtWidgets import QFrame, QMenu, QWidgetAction, QWidget, QGraphicsLineItem

from metgem_app.ui.widgets.annotations import AnnotationsNetworkScene
from metgem_app.ui.edit_options_dialog import (EditNetworkOptionsDialog, EditTSNEOptionsDialog,
                                   EditMDSOptionsDialog, EditIsomapOptionsDialog,
                                   EditUMAPOptionsDialog, EditPHATEOptionsDialog)
from metgem_app import config
from metgem_app.workers import core as workers_core
from metgem_app.workers import options as workers_opts
from metgem_app.ui.widgets.network_ui import Ui_NetworkFrame


def short_id(id_):
    return id_.split('_')[1].split('-')[0]


if sys.hexversion >= 0x03090000:  # Python>=3.9
    def classproperty(func):
        return classmethod(property(func))
else:
    class classproperty(property):

        def __get__(self, obj, objtype=None):
            return super(classproperty, self).__get__(objtype)

        def __set__(self, obj, value):
            super(classproperty, self).__set__(type(obj), value)

        def __delete__(self, obj):
            super(classproperty, self).__delete__(type(obj))


class BaseFrame(QFrame, Ui_NetworkFrame):
    id = None
    title = None
    unlockable = False
    extra = False
    dialog_class = None
    worker_class = None
    options_class = None
    use_edges = True
    editOptionsTriggered = Signal(QWidget)
    workerReady = Signal(QObject)

    @classproperty
    def name(cls):
        return cls.options_class.name

    # noinspection PyUnresolvedReferences
    @classmethod
    def get_subclasses(cls):
        for subclass in cls.__subclasses__():
            if subclass.worker_class is not None and subclass.worker_class.enabled():
                yield subclass
            yield from subclass.get_subclasses()

    def __init__(self, id_: str, network, graph=ig.Graph(), interactions=pd.DataFrame()):
        super().__init__()
        self.setupUi(self)

        self.id = id_
        self._name = None
        self._layout = None
        self._hide_isolated_nodes = False
        self._isolated_nodes = []
        self._network = network
        self._graph = graph if isinstance(graph, ig.Graph) else ig.Graph()
        self._interactions = interactions if isinstance(interactions, pd.DataFrame) else pd.DataFrame()

        # Send Scale sliders to a toolbutton menu
        self._menu = menu = QMenu()
        action = QWidgetAction(self)
        action.setDefaultWidget(self.sliderScale)
        menu.addAction(action)
        self.btRuler.setMenu(menu)

        self.view().setScene(AnnotationsNetworkScene())

        if self.unlockable:
            self.btLock.toggled.connect(lambda x: self.scene().lock(x))
        else:
            self.btLock.hide()
        self.btOptions.clicked.connect(lambda: self.editOptionsTriggered.emit(self))
        self.sliderScale.valueChanged.connect(self.on_scale_changed)

    def view(self):
        return self.gvNetwork

    def scene(self):
        return self.gvNetwork.scene()

    @property
    def short_id(self):
        return short_id(self.id)

    @property
    def graph(self):
        return self._graph

    @graph.setter
    def graph(self, graph):
        self._graph = graph

    @property
    def interactions(self):
        return self._interactions

    @interactions.setter
    def interactions(self, interactions):
        self._interactions = interactions
        
    def apply_layout(self, layout, isolated_nodes=None, hide_isolated_nodes=False):
        self._hide_isolated_nodes = hide_isolated_nodes
        scene = self.scene()
        if layout is not None:
            scene.setLayout(layout, isolated_nodes=isolated_nodes if hide_isolated_nodes else None)
        self._layout = layout
        self._isolated_nodes = isolated_nodes
        scene.lock(self.btLock.isChecked() if self.unlockable else True)
        
    def reset_layout(self):
        self._layout = None

    def show_isolated_nodes(self, show=True):
        if show != self._hide_isolated_nodes:
            self._hide_isolated_nodes = show
            worker = self.create_draw_worker(compute_layouts=False)
            worker.start()

    def hide_isolated_nodes(self):
        self.show_isolated_nodes(False)

    def on_scale_changed(self, scale):
        self.scene().setScale(scale / self.sliderScale.defaultValue())

    def process_graph_before_export(self, g):
        return g

    def get_layout_data(self):
        scene = self.scene()
        return {
                'layout': self._layout,
                'isolated_nodes': self._isolated_nodes,
                'colors': {i: c.name() for i, c in enumerate(scene.nodesColors()) if c.isValid()},
                'radii': np.array(scene.nodesRadii(), dtype=np.uint8)
               }

    def get_graph_data(self):
        return {
                'graph': self._graph,
                'interactions': self._interactions
               }

    def get_annotations_data(self) -> bytes:
        return self.view().saveAnnotations()

    def set_annotations_data(self, buffer: bytes) -> None:
        self.view().loadAnnotations(buffer)

    def create_worker(self):
        raise NotImplementedError

    def set_style(self, style):
        self.scene().setNetworkStyle(style)

    def create_draw_worker(self, compute_layouts=True, colors=[], radii=[], layout=None, isolated_nodes=None):
        scene = self.scene()
        if self.use_edges:
            scene.removeAllEdges()

        # Add nodes
        nodes = scene.nodes()
        if not nodes:
            if self._graph.vs:  # Network views
                nodes = scene.createNodes(self._graph.vs['name'], colors=colors, radii=radii)
            elif self._network.scores.size > 0: # Embedding views
                nodes = scene.createNodes(np.arange(self._network.scores.shape[0]), colors=colors, radii=radii)

        if self.use_edges:
            # Add edges
            edges_attr = [(e.index, nodes[e.source], nodes[e.target], e['__width'])
                          for e in self._graph.es if not e.is_loop()]
            if edges_attr:
                scene.createEdges(*zip(*edges_attr))

        if layout is not None:
            self._layout = layout

        if isolated_nodes is not None:
            self._isolated_nodes = isolated_nodes

        # Create apply layout worker
        if compute_layouts or self._layout is None:
            # Compute layout
            def process_finished(worker):
                computed_layout, self._isolated_nodes = worker.result()
                if computed_layout is not None:
                    self.apply_layout(computed_layout, self._isolated_nodes, self._hide_isolated_nodes)

            return [self.create_worker(), process_finished]
        else:
            return workers_core.GenericWorker(self.apply_layout, self._layout, self._isolated_nodes,
                                              self._hide_isolated_nodes)


class NetworkFrame(BaseFrame):
    title = 'Network'
    extra = False
    unlockable = True
    dialog_class = EditNetworkOptionsDialog
    worker_class = workers_core.NetworkWorker
    options_class = workers_opts.NetworkVisualizationOptions
    use_edges = True

    def process_graph_before_export(self, g):
        g.delete_edges([edge for edge in g.es if edge.is_loop()])
        for attr in g.es.attributes():
            if attr.startswith('__'):
                del g.es[attr]
        return g

    def create_worker(self):
        return self.worker_class(self._graph, self.scene().nodesRadii())


class TSNEFrame(NetworkFrame):
    title = 't-SNE'
    extra = False
    unlockable = False
    dialog_class = EditTSNEOptionsDialog
    worker_class = workers_core.TSNEWorker
    options_class = workers_opts.TSNEVisualizationOptions
    use_edges = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._line = None

    def on_scale_changed(self, scale):
        super().on_scale_changed(scale)
        self.draw_horizontal_line()

    def apply_layout(self, layout, isolated_nodes=None, hide_isolated_nodes=False):
        super().apply_layout(layout, isolated_nodes, hide_isolated_nodes)
        if isolated_nodes is not None:
            self._isolated_nodes = isolated_nodes
        self.draw_horizontal_line()

    def reset_layout(self):
        super().reset_layout()
        self._isolated_nodes = None

    def show_isolated_nodes(self, show=True):
        super().show_isolated_nodes(show)
        self.draw_horizontal_line()

    def draw_horizontal_line(self):
        scene = self.scene()

        # Remove line separating isolated nodes from others
        line = self._line
        if line is not None and isinstance(line, QGraphicsLineItem):
            scene.removeItem(line)

        # Add a new line if needed
        if not self._hide_isolated_nodes and self._isolated_nodes is not None:
            try:
                scale = scene.scale()
                lyt = self._layout[self._isolated_nodes]
                x1 = lyt.min(axis=0)[0] - 5 * config.RADIUS
                x2 = lyt.max(axis=0)[0] + 5 * config.RADIUS
                y = lyt.max(axis=1)[1] - 5 * config.RADIUS
                width = 25 * scale
                pen = QPen(scene.networkStyle().nodeBrush().color(), width, Qt.DotLine)
                self._line = scene.addLine(x1 * scale, y * scale, x2 * scale, y * scale, pen=pen)
            except ValueError:
                pass

    def process_graph_before_export(self, g):
        g.delete_edges(g.es)  # in a t-SNE layout, edges does not makes any sense
        return g

    def create_worker(self):
        return self.worker_class(self._network.scores, self._network.options[self.id])

    def set_style(self, style):
        super().set_style(style)
        self.draw_horizontal_line()


class MDSFrame(TSNEFrame):
    title = 'MDS'
    extra = True
    unlockable = False
    dialog_class = EditMDSOptionsDialog
    worker_class = workers_core.MDSWorker
    options_class = workers_opts.MDSVisualizationOptions
    use_edges = False


class UMAPFrame(TSNEFrame):
    title = 'UMAP'
    extra = True
    unlockable = False
    dialog_class = EditUMAPOptionsDialog
    worker_class = workers_core.UMAPWorker
    options_class = workers_opts.UMAPVisualizationOptions
    use_edges = False


class IsomapFrame(TSNEFrame):
    title = 'Isomap'
    extra = True
    unlockable = False
    dialog_class = EditIsomapOptionsDialog
    worker_class = workers_core.IsomapWorker
    options_class = workers_opts.IsomapVisualizationOptions
    use_edges = False


class PHATEFrame(TSNEFrame):
    title = 'PHATE'
    extra = True
    unlockable = False
    dialog_class = EditPHATEOptionsDialog
    worker_class = workers_core.PHATEWorker
    options_class = workers_opts.PHATEVisualizationOptions
    use_edges = False


AVAILABLE_NETWORK_WIDGETS = {obj.name: obj for obj in BaseFrame.get_subclasses()}
