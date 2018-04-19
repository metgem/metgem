from PyQt5.QtCore import QByteArray, pyqtProperty, QSize
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import QVBoxLayout, QPushButton, QWidget

try:
    from rdkit.Chem import MolFromSmiles, rdDepictor
    from rdkit.Chem.Draw import rdMolDraw2D
    from rdkit.Chem.inchi import INCHI_AVAILABLE
    if INCHI_AVAILABLE:
        from rdkit.Chem.inchi import MolFromInchi
except ImportError:
    RDKIT_AVAILABLE = False
    INCHI_AVAILABLE = False
else:
    RDKIT_AVAILABLE = True

try:
    import pybel
    from lxml import etree
except ImportError:
    OPENBABEL_AVAILABLE = False
    INCHI_AVAILABLE = False
else:
    OPENBABEL_AVAILABLE = True
    INCHI_AVAILABLE = 'inchi' in pybel.informats.keys()


class SecondColumnMapping(QWidget):

    @pyqtProperty(str)
    def smiles(self):
        return self.parent()._smiles

    @smiles.setter
    def smiles(self, smiles):
        self.parent().smiles = smiles

class StructureSvgWidget(QSvgWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._inchi = None
        self._smiles = None

        layout = QVBoxLayout()
        self.btShowStructure = QPushButton('View Structure')
        self.btShowStructure.clicked.connect(self.render_structure)
        layout.addWidget(self.btShowStructure)
        self.setLayout(layout)

        self.btShowStructure.setVisible(False)

        self.second_mapping = SecondColumnMapping(self)

    @pyqtProperty(str)
    def inchi(self):
        return self._inchi

    @inchi.setter
    def inchi(self, inchi):
        self.setInchi(inchi)

    @pyqtProperty(str)
    def smiles(self):
        return self._smiles

    @smiles.setter
    def smiles(self, smiles):
        self.setSmiles(smiles)

    def setSmiles(self, smiles):
        self._smiles = smiles
        self.btShowStructure.setVisible(bool(self._inchi or self._smiles))
        self.load(QByteArray(b''))

    def setInchi(self, inchi):
        self._inchi = inchi
        self.btShowStructure.setVisible(bool(self._inchi or self._smiles))
        self.load(QByteArray(b''))

    def setMaximumWidth(self, width):
        super().setMaximumWidth(width)
        self._base_width = width

    def setMaximumHeight(self, height):
        super().setMaximumHeight(height)
        self._base_height = height

    def setMaximumSize(self, size):
        super().setMaximumSize(size)
        self._base_width = size.width()
        self._base_height = size.height()

    def render_structure(self):
        # Try to render structure from InChI or SMILES
        if RDKIT_AVAILABLE:
            mol = None
            if INCHI_AVAILABLE and self._inchi:  # Use InChI first
                mol = MolFromInchi(self._inchi)
            elif self._smiles is not None:  # If InChI not available, use SMILES as a fallback
                mol = MolFromSmiles(self._smiles)
            if mol is not None:
                if not mol.GetNumConformers():
                    rdDepictor.Compute2DCoords(mol)
                drawer = rdMolDraw2D.MolDraw2DSVG(self.size().width(),
                                                  self.size().height())
                drawer.DrawMolecule(mol)
                drawer.FinishDrawing()
                svg = drawer.GetDrawingText().replace('svg:', '')
                self.load(QByteArray(svg.encode()))
            else:
                self.load(QByteArray(b''))
        elif OPENBABEL_AVAILABLE:  # If RDkit not available, try to use OpenBabel
            mol = None
            try:
                if INCHI_AVAILABLE and self._inchi:
                    mol = pybel.readstring('inchi', self._inchi)
                elif self._smiles:
                    mol = pybel.readstring('smiles', self._smiles)
            except OSError:
                self.load(QByteArray(b''))
            else:
                if mol is not None:
                    # Convert to svg, code loosely based on _repr_svg_ from pybel's Molecule
                    namespace = "http://www.w3.org/2000/svg"
                    tree = etree.fromstring(mol.write("svg"))
                    svg = tree.find(f"{{{namespace}}}g/{{{namespace}}}svg")
                    self.load(QByteArray(etree.tostring(svg)))
                else:
                    self.load(QByteArray(b''))
        self.btShowStructure.setVisible(False)

    def load(self, *args, **kwargs):
        super().load(*args, **kwargs)

        # Preserve aspect ratio
        vb = self.renderer().viewBox()
        w, h = min(self._base_width, vb.width()), min(self._base_height, vb.height())
        if w > 0 and h > 0:
            w = self._base_width
            h = min(w / vb.width() * vb.height(), self._base_height)
            w = min(w / self._base_width * vb.width(), self._base_width)
            size = QSize(w, h)
            self.setFixedSize(size)
