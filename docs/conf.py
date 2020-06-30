# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
sys.path.insert(0, os.path.abspath('_ext'))


# -- Project information -----------------------------------------------------

project = 'MetGem'
copyright = '2020, Nicolas Elie'
author = 'Nicolas Elie'

# The short X.Y version
version = '1.3'

# The full version, including alpha/beta/rc tags
release = '1.3.0'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinxcontrib.rsvgconverter',
    'metgem'
]
autosectionlabel_prefix_document = True

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', 'includes/colors.rst']


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'alabaster'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# A list of CSS files.
# The entry must be a filename string or a tuple containing the filename string and the attributes dictionary. The filename must be relative to the html_static_path, or a full URI with scheme like http://example.org/style.css.
# The attributes is used for attributes of <link> tag. It defaults to an empty list.
html_css_files = ['colors.css', 'kbd.css']

# Alabaster config
html_theme_options = {
    'logo': 'main-wide.svg',
    'github_user': 'metgem',
    'github_repo': 'metgem',
}

   

# A string of reStructuredText that will be included at the beginning of every source file that is read.
# This is a possible place to add substitutions that should be available in every file (another being rst_epilog).
rst_prolog = """
.. include:: /includes/colors.rst
"""

# A string of reStructuredText that will be included at the end of every source file that is read.
# This is a possible place to add substitutions that should be available in every file (another being rst_prolog).
rst_epilog = """
.. |appname| replace:: MetGem

.. _GNPS: https://gnps.ucsd.edu
.. _t-SNE: https://en.wikipedia.org/wiki/T-distributed_stochastic_neighbor_embedding
.. _mgf: http://www.matrixscience.com/help/data_file_help.html
.. _msp: https://chemdata.nist.gov/mass-spc/ms-search/docs/Ver20Man_11.pdf#page=47
.. _UMAP: https://umap-learn.readthedocs.io
.. _MDS: https://en.wikipedia.org/wiki/Multidimensional_scaling
.. _Isomap: https://en.wikipedia.org/wiki/Isomap
.. _PHATE: https://phate.readthedocs.io
.. _csv: https://en.wikipedia.org/wiki/Comma-separated_values
.. _spreadsheet: https://en.wikipedia.org/wiki/Spreadsheet
.. _Microsoft Excel: https://en.wikipedia.org/wiki/Microsoft_Excel
.. _LibreOffice: https://www.libreoffice.org
.. _Cytoscape: https://cytoscape.org
.. _HDBScan: https://hdbscan.readthedocs.io
.. _Python: https://www.python.org
.. _Pandas: https://pandas.pydata.org

.. |mousescroll| image:: /images/mouse-scroll.svg
.. |mouseleft| image:: /images/mouse-left.svg
.. |mouseright| image:: /images/mouse-right.svg
.. |import-data| image:: /images/icons/import-data.svg
    :alt: Import Data
.. |import-database| image:: /images/icons/import-database.svg
    :alt: Import Database
.. |import-mapping| image:: /images/icons/import-mapping.svg
    :alt: Import Mapping
.. |import-metadata| image:: /images/icons/import-metadata.svg
    :alt: Import Metadata
.. |browse| image:: /images/browse.png
    :alt: Browse
.. |options| image:: /images/options.png
    :alt: Options
.. |ok| image:: /images/ok.png
    :alt: OK
.. |refresh| image:: /images/icons/refresh.svg
    :alt: Refresh
"""


latex_elements = {
    'papersize': 'a4paper',
    'preamble': r'''
\usepackage{menukeys}
\renewmenumacro{\keys}{shadowedroundedkeys}
\renewmenumacro{\menu}[|]{angularmenus}
\renewcommand{\sphinxkeyboard}{\keys}
\renewcommand{\sphinxguilabel}{\menu}
\renewcommand{\sphinxmenuselection}{\menu}
    ''',
}
