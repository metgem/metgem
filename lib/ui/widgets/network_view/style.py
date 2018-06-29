try:
    import tinycss2
except ImportError:
    HAS_TINYCSS2 = False
else:
    HAS_TINYCSS2 = True

from PyQt5.QtCore import Qt, QCoreApplication
from PyQt5.QtGui import QColor, QFont, QPen, QBrush

from ....config import RADIUS

try:
    from .NetworkView import NetworkStyle, DefaultStyle

except ImportError:
    class NetworkStyle:
        name = ""
        node = {}
        edge = {}
        scene = {}

        def __init__(self, name=None, node=None, edge=None, scene=None):
            if name is not None:
                self.name = name
            if node is not None:
                self.node = node
            if edge is not None:
                self.edge = edge
            if scene is not None:
                self.scene = scene

        def styleName(self):
            return self.name

        def nodeBrush(self, state='normal') -> QBrush:
            try:
                return self.node['bgcolor'][state]
            except KeyError:
                return None if state == 'selected' else QBrush(QColor(Qt.lightGray))

        def nodeTextColor(self, state='normal') -> QColor:
            try:
                return self.node['txtcolor'][state]
            except KeyError:
                return None if state == 'selected' else QColor(Qt.black)

        def nodePen(self, state='normal') -> QPen:
            try:
                return self.node['border'][state]
            except KeyError:
                return QPen(Qt.black, 1)

        def nodeFont(self, state='normal') -> QFont:
            try:
                return self.node['font'][state]
            except KeyError:
                return QFont()

        def edgePen(self, state='normal') -> QPen:
            try:
                return self.edge['color'][state]
            except KeyError:
                return QPen(Qt.red) if state == 'selected' else QPen(Qt.darkGray)

        def backgroundBrush(self) -> QBrush:
            try:
                return self.scene['color']
            except KeyError:
                return QBrush(QColor(Qt.white))


    class DefaultStyle(NetworkStyle):
        name = "default"
        node = {'bgcolor': {'normal': QBrush(Qt.lightGray),
                            'selected': QBrush(Qt.yellow)},
                'txtcolor': {'normal': QColor(Qt.black),
                             'selected': QColor(Qt.black)},
                'border': {'normal': QPen(Qt.black, 1, Qt.SolidLine),
                           'selected': QPen(Qt.black, 1, Qt.SolidLine)},
                'font': {'normal': QFont('Arial', 10),
                         'selected': QFont('Arial', 10)},
                }
        edge = {'color': {'normal': QPen(QColor(Qt.darkGray)),
                          'selected': QPen(QColor(Qt.red))}}
        scene = {'color': QBrush(Qt.white)}

# Code to load theme from css
CSS_FONT_WEIGHTS_TO_QT = {100: 0, 200: 12, 300: 25, 400: 50, 500: 57, 600: 63, 700: 75, 800: 81, 900: 87, 1000: 99,
                          'bold': QFont.Bold, 'bolder': QFont.ExtraBold, 'lighter': QFont.Light}
CSS_FONT_STYLES_TO_QT = {'normal': QFont.StyleNormal, 'italic': QFont.StyleItalic, 'oblique': QFont.StyleOblique}
CSS_FONT_VARIANTS_TO_QT = {'normal': QFont.MixedCase, 'small-caps': QFont.SmallCaps,
                           'capitalize': QFont.Capitalize, 'upper': QFont.AllUppercase,
                           'lower': QFont.AllLowercase}
CSS_BORDER_STYLES_TO_QT = {'solid': Qt.SolidLine, 'dashed': Qt.DashLine, 'dotted': Qt.DotLine, 'none': Qt.NoPen}


def parse_rule(rule):
    name, state = None, 'normal'

    try:
        declaration = tinycss2.parse_one_declaration(rule.prelude, skip_comments=True)
        for token in declaration.value:
            if token.type == 'ident':
                name, state = declaration.name, token.value
    except (ValueError, TypeError, AttributeError):
        for token in rule.prelude:
            if token.type == 'ident':
                name = token.value

    if name is not None:
        for token in tinycss2.parse_declaration_list(rule.content, skip_comments=True, skip_whitespace=True):
            if token.type == 'declaration':
                for t in token.value:
                    yield name, state, token.name, t


def css_font_weight_to_qt(weight):
    try:
        weight = round(int(weight), -2)
    except ValueError:
        pass

    try:
        return CSS_FONT_WEIGHTS_TO_QT[weight]
    except KeyError:
        return


def css_font_style_to_qt(style):
    try:
        return CSS_FONT_STYLES_TO_QT[style]
    except KeyError:
        return


def css_font_variant_to_qt(style):
    try:
        return CSS_FONT_VARIANTS_TO_QT[style]
    except KeyError:
        return


def css_border_style_to_qt(style):
    try:
        return CSS_BORDER_STYLES_TO_QT[style]
    except KeyError:
        return


def style_from_css(css):
    if not HAS_TINYCSS2 or css is None:
        return DefaultStyle()

    try:
        with open(css, 'r') as f:
            sheet = tinycss2.parse_stylesheet(''.join(f.readlines()))
    except FileNotFoundError:
        return DefaultStyle()

    stylename = None
    node = {'bgcolor': {'normal': Qt.lightGray,
                        'selected': QColor()},
            'txtcolor': {'normal': Qt.black,
                         'selected': QColor()},
            'border': {'normal': {'style': Qt.SolidLine, 'width': 1, 'color': 'black'},
                       'selected': {'style': Qt.SolidLine, 'width': 1, 'color': 'black'}},
            'font': {'normal': {'family': 'Arial', 'variant': QFont.MixedCase, 'size': 10, 'unit': 'pt',
                                'style': QFont.StyleNormal, 'weight': QFont.Normal},
                     'selected': {'family': 'Arial', 'variant': QFont.MixedCase, 'size': 10, 'unit': 'pt',
                                  'style': QFont.StyleNormal, 'weight': QFont.Normal}}
            }
    edge = {'color': {'normal': Qt.darkGray, 'selected': Qt.red}}
    scene = {'color': Qt.white}

    for rule in sheet:
        if rule.type == 'comment' and stylename is None:
            try:
                stylename = rule.value.split('name: ')[1].strip()
            except IndexError:
                stylename = ""
        elif rule.type == 'qualified-rule':
            for name, state, prop, token in parse_rule(rule):
                if name == 'node':
                    if token.type == 'ident':
                        if prop == 'background-color':
                            node['bgcolor'][state] = token.value
                        elif prop == 'color':
                            node['txtcolor'][state] = token.value
                        elif prop == 'font-family':
                            node['font'][state]['family'] = token.value
                        elif prop == 'font-weight':
                            weight = css_font_weight_to_qt(token.value)
                            if weight is not None:
                                node['font'][state]['weight'] = weight
                        elif prop == 'font-style':
                            style = css_font_style_to_qt(token.value)
                            if style is not None:
                                node['font'][state]['style'] = style
                        elif prop == 'font-variant':
                            variant = css_font_variant_to_qt(token.value)
                            node['font'][state]['variant'] = variant
                        elif prop == 'font':
                            style = css_font_style_to_qt(token.value)
                            if style is not None:
                                node['font'][state]['style'] = style
                            else:
                                variant = css_font_variant_to_qt(token.value)
                                if variant is not None:
                                    node['font'][state]['variant'] = variant
                                else:
                                    weight = css_font_weight_to_qt(token.value)
                                    if weight is not None:
                                        node['font'][state]['weight'] = weight
                                    else:
                                        node['font'][state]['family'] = token.value
                        elif prop == 'border-style':
                            style = css_border_style_to_qt(token.value)
                            node['border'][state]['style'] = style
                        elif prop == 'border-color':
                            node['border'][state]['color'] = token.value
                        elif prop == 'border':
                            style = css_border_style_to_qt(token.value)
                            if style is not None:
                                node['border'][state]['style'] = style
                            else:
                                node['border'][state]['color'] = token.value
                    elif token.type == 'dimension':
                        if prop in ('font', 'font-size'):
                            node['font'][state]['size'] = token.value
                            node['font'][state]['unit'] = token.unit
                        elif prop in ('border', 'border-width'):
                            node['border'][state]['width'] = token.value
                    elif token.type == 'hash':
                        if prop == 'background-color':
                            node['bgcolor'][state] = token.serialize()
                        elif prop == 'color':
                            node['txtcolor'][state] = token.serialize()
                        elif prop == 'border-color':
                            node['border'][state] = token.serialize()
                elif name == 'edge':
                    if token.type == 'ident':
                        if prop == 'background-color':
                            edge['color'][state] = token.value
                    elif token.type == 'hash':
                        if prop == 'background-color':
                            edge['color'][state] = token.serialize()
                elif name == 'scene':
                    if token.type == 'ident':
                        if prop == 'background-color':
                            scene['color'] = token.value
                    elif token.type == 'hash':
                        if prop == 'background-color':
                            scene['color'] = token.serialize()

    for state in ('normal', 'selected'):
        node['bgcolor'][state] = QBrush(QColor(node['bgcolor'][state]))
        node['txtcolor'][state] = QColor(node['txtcolor'][state])
        node['border'][state] = QPen(QBrush(QColor(node['border'][state]['color'])),
                                     node['border'][state]['width'],
                                     node['border'][state]['style'])
        f = QFont(node['font'][state]['family'])
        if node['font'][state]['unit'] == 'px':
            f.setPixelSize(node['font'][state]['size'])
        else:
            f.setPointSize(node['font'][state]['size'])
        f.setCapitalization(node['font'][state]['variant'])
        f.setWeight(node['font'][state]['weight'])
        f.setStyle(node['font'][state]['style'])
        node['font'][state] = f
        edge['color'][state] = QPen(QColor(edge['color'][state]))
    scene['color'] = QColor(scene['color'])

    return NetworkStyle(stylename, node, edge, scene)


def style_to_json(style: NetworkStyle):
    style_dict = {"format_version": 1.0,
                  "generated_by": f"{QCoreApplication.applicationName()}-{QCoreApplication.applicationVersion()}",
                  "target_cytoscapejs_version": "~2.1",
                  "title": style.styleName(),
                  "style": [{
                      "selector": "node",
                      "css": {
                          "text-opacity": 1.0,
                          "background-color": style.nodeBrush().color().name(),
                          "text-valign": "center",
                          "text-halign": "center",
                          "border-width": style.nodePen().width(),
                          "font-size": style.nodeFont().pointSize(),
                          "width": RADIUS * 2,
                          "shape": "ellipse",
                          "color": style.nodeTextColor(),
                          "border-opacity": 1.0,
                          "height": RADIUS * 2,
                          "background-opacity": 1.0,
                          "border-color": style.nodePen().color().name(),
                          "font-family": style.nodeFont().family(),
                          "font-weight": style.nodeFont().weight(),
                          "content": "data(name)"
                      }
                  }, {
                      "selector": "node:selected",
                      "css": {
                          "background-color": style.nodeBrush('selected').color().name(),
                          "border-width": style.nodePen('selected').width(),
                          "font-size": style.nodeFont('selected').pointSize(),
                          "width": RADIUS * 2,
                          "color": style.nodeTextColor('selected'),
                          "height": RADIUS * 2,
                          "border-color": style.nodePen('selected').color().name(),
                          "font-family": style.nodeFont('selected').family(),
                          "font-weight": style.nodeFont('selected').weight()
                      }
                  }, {
                      "selector": "edge",
                      "css": {
                          "line-color": style.edgePen().color().name(),
                          "opacity": 1.0,
                          "line-style": style.edgePen().style(),
                          "text-opacity": 1.0,
                          "content": "data(interaction)"
                      }
                  }, {
                      "selector": "edge:selected",
                      "css": {
                          "line-color": style.edgePen('selected').color().name(),
                          "line-style": style.edgePen().style()
                      }
                  }]
                  }
    return style_dict


def style_to_cytoscape(style: NetworkStyle):
    style_dict = {'title': QCoreApplication.applicationName() + "-" + style.styleName(),
                  'defaults':
                      [{'visualProperty': 'COMPOUND_NODE_SHAPE', 'value': 'ROUND_RECTANGLE'},
                       {'visualProperty': 'EDGE_LABEL', 'value': ''},
                       {'visualProperty': 'EDGE_LINE_TYPE', 'value': style.edgePen().style()},
                       {'visualProperty': 'EDGE_PAINT', 'value': style.edgePen().color().name()},
                       {'visualProperty': 'EDGE_SELECTED', 'value': False},
                       {'visualProperty': 'EDGE_SELECTED_PAINT', 'value': style.edgePen('selected').color().name()},
                       {'visualProperty': 'EDGE_VISIBLE', 'value': True},
                       {'visualProperty': 'EDGE_WIDTH', 'value': 12.0},
                       {'visualProperty': 'EDGE_SOURCE_ARROW_UNSELECTED_PAINT', 'value': style.edgePen().color().name()},
                       {'visualProperty': 'EDGE_TARGET_ARROW_UNSELECTED_PAINT', 'value': style.edgePen().color().name()},
                       {'visualProperty': 'EDGE_STROKE_UNSELECTED_PAINT', 'value': style.edgePen().color().name()},
                       {'visualProperty': 'EDGE_SOURCE_ARROW_SELECTED_PAINT', 'value': style.edgePen().color().name()},
                       {'visualProperty': 'EDGE_TARGET_ARROW_SELECTED_PAINT', 'value': style.edgePen().color().name()},
                       {'visualProperty': 'EDGE_STROKE_SELECTED_PAINT', 'value': style.edgePen().color().name()},
                       {'visualProperty': 'NETWORK_BACKGROUND_PAINT', 'value': style.backgroundBrush().color().name()},
                       {'visualProperty': 'NETWORK_CENTER_X_LOCATION', 'value': 0.0},
                       {'visualProperty': 'NETWORK_CENTER_Y_LOCATION', 'value': 0.0},
                       {'visualProperty': 'NETWORK_CENTER_Z_LOCATION', 'value': 0.0},
                       {'visualProperty': 'NETWORK_DEPTH', 'value': 0.0},
                       {'visualProperty': 'NETWORK_EDGE_SELECTION', 'value': True},
                       {'visualProperty': 'NETWORK_HEIGHT', 'value': 400.0},
                       {'visualProperty': 'NETWORK_NODE_SELECTION', 'value': True},
                       {'visualProperty': 'NETWORK_SCALE_FACTOR', 'value': 1.0},
                       {'visualProperty': 'NETWORK_SIZE', 'value': 550.0},
                       {'visualProperty': 'NETWORK_TITLE', 'value': ''},
                       {'visualProperty': 'NETWORK_WIDTH', 'value': 550.0},
                       {'visualProperty': 'NODE_BORDER_PAINT', 'value': style.nodePen().color().name()},
                       {'visualProperty': 'NODE_BORDER_STROKE', 'value': style.nodePen().style()},
                       {'visualProperty': 'NODE_BORDER_TRANSPARENCY', 'value': 255},
                       {'visualProperty': 'NODE_BORDER_WIDTH', 'value': style.nodePen().width()},
                       {'visualProperty': 'NODE_DEPTH', 'value': 0.0},
                       {'visualProperty': 'NODE_FILL_COLOR', 'value': style.nodeBrush().color().name()},
                       {'visualProperty': 'NODE_HEIGHT', 'value': RADIUS*2},
                       {'visualProperty': 'NODE_LABEL', 'value': ''},
                       {'visualProperty': 'NODE_LABEL_COLOR', 'value': style.nodeTextColor().name()},
                       {'visualProperty': 'NODE_LABEL_FONT_FACE', 'value': style.nodeFont().family()},
                       {'visualProperty': 'NODE_LABEL_FONT_SIZE', 'value': style.nodeFont().pointSize()},
                       {'visualProperty': 'NODE_LABEL_TRANSPARENCY', 'value': 255},
                       {'visualProperty': 'NODE_NESTED_NETWORK_IMAGE_VISIBLE', 'value': True},
                       {'visualProperty': 'NODE_PAINT', 'value': style.nodeBrush().color().name()},
                       {'visualProperty': 'NODE_SELECTED', 'value': False},
                       {'visualProperty': 'NODE_SELECTED_PAINT', 'value': style.nodeBrush('selected').color().name()},
                       {'visualProperty': 'NODE_SHAPE', 'value': 'ELLIPSE'},
                       {'visualProperty': 'NODE_SIZE', 'value': RADIUS*2},
                       {'visualProperty': 'NODE_TOOLTIP', 'value': ''},
                       {'visualProperty': 'NODE_TRANSPARENCY', 'value': 255},
                       {'visualProperty': 'NODE_VISIBLE', 'value': True},
                       {'visualProperty': 'NODE_WIDTH', 'value': RADIUS*2},
                       {'visualProperty': 'NODE_X_LOCATION', 'value': 0.0},
                       {'visualProperty': 'NODE_Y_LOCATION', 'value': 0.0},
                       {'visualProperty': 'NODE_Z_LOCATION', 'value': 0.0}],
                  'mappings': [{'mappingType': 'passthrough',
                                'mappingColumn': 'interaction',
                                'mappingColumnType': 'String',
                                'visualProperty': 'EDGE_LABEL'},
                               {'mappingType': 'passthrough',
                                'mappingColumn': 'name',
                                'mappingColumnType': 'String',
                                'visualProperty': 'NODE_LABEL'}]}

    return style_dict
