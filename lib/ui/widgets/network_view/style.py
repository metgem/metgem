try:
    import tinycss2
except ImportError:
    HAS_TINYCSS2 = False
else:
    HAS_TINYCSS2 = True

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont, QPen, QBrush

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

        def nodeRadius(self) -> int:
            try:
                return self.node['radius']
            except KeyError:
                return 30

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
        node = {'radius': 30,
                'bgcolor':  {'normal':    QBrush(Qt.lightGray),
                             'selected':  QBrush(Qt.yellow)},
                'txtcolor': {'normal':   QColor(Qt.black),
                             'selected': QColor(Qt.black)},
                'border':   {'normal':   QPen(Qt.black, 1, Qt.SolidLine),
                             'selected': QPen(Qt.black, 1, Qt.SolidLine)},
                'font':     {'normal': QFont('Arial', 10),
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
    if not HAS_TINYCSS2:
        return

    with open(css, 'r') as f:
        sheet = tinycss2.parse_stylesheet(''.join(f.readlines()))

    stylename = ""
    node = {'radius': 30,
            'bgcolor':  {'normal':   Qt.lightGray,
                         'selected': Qt.yellow},
            'txtcolor': {'normal':   Qt.black,
                         'selected': Qt.black},
            'border': {'normal':   {'style': Qt.SolidLine, 'width': 1, 'color': 'black'},
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
                    elif token.type == 'number':
                        if prop == 'radius' and state == 'normal':
                            try:
                                node['radius'] = int(token.value)
                            except ValueError:
                                pass
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
