import sys
import os

from setuptools import setup, find_packages
from setuptools.command.build_py import build_py
from distutils import cmd
from PyQt5.pyrcc_main import processResourceFile
from metgem_app import version

# Gather data files
package_data = {'metgem_app': ['splash.png',
                               'styles/*.css',
                               'ui/*.ui',
                               'ui/widgets/images/*',
                               'ui/widgets/*.ui',
                               'ui/widgets/databases/*.ui',
                               'ui/widgets/spectrum/*.ui',
                               'ui/widgets/metadata/*.ui',
                               'ui/widgets/metadata/*.csv'
                               ]}

data_files = [("", ["LICENSE"])]
if not sys.platform.startswith('darwin'):
    data_files.extend([('examples', ['examples/Codiaeum.csv', 'examples/Codiaeum.mgf',
                                     'examples/Stillingia SFE.csv', 'examples/Stillingia SFE.mgf',
                                     'examples/Stillingia group mapping.txt'])])


class ProcessResourceCommand(cmd.Command):
    """A custom command to compile the resource file into a Python file"""

    description = "Compile the qrc file into a python file"

    def initialize_options(self):
        return

    def finalize_options(self):
        return

    def run(self):
        processResourceFile([os.path.join('metgem_app', 'ui', 'ui.qrc')],
                            os.path.join('metgem_app', 'ui', 'ui_rc.py'), False)


class BuildPyCommand(build_py):
    """Custom build command to include ProcessResource command"""

    def run(self):
        self.run_command("process_resource")
        build_py.run(self)


setup(
    name=version.APPLICATION.lower(),
    version=version.VERSION.lower(),
    author="Nicolas Elie",
    author_email="nicolas.elie@cnrs.fr",
    url="https://github.com/metgem/metgem",
    description="Calculation and visualization of molecular networks based on t-SNE algorithm",
    long_description="Calculation and visualization of molecular networks based on t-SNE algorithm",
    keywords=["chemistry", "molecular networking", "mass spectrometry"],
    license="GPLv3+",
    classifiers=["Development Status :: 5 - Production/Stable",
                 "Intended Audience :: Science/Research",
                 "Intended Audience :: Developers",
                 "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
                 "Operating System :: OS Independent",
                 "Topic :: Scientific/Engineering :: Bio-Informatics",
                 "Topic :: Scientific/Engineering :: Chemistry",
                 "Programming Language :: Python :: 3",
                 "Programming Language :: Python :: 3.6",
                 "Programming Language :: Python :: 3.7",
                 "Programming Language :: Python :: 3.8"],
    packages=find_packages(exclude=("packaging", "tests",)),
    scripts=['MetGem'],
    data_files=data_files,
    package_dir={'metgem': 'metgem'},
    package_data=package_data,
    include_package_data=True,
    cmdclass={'process_resource': ProcessResourceCommand,
              'build_py': BuildPyCommand},
    install_requires=['pandas >=0.22',
                      'lxml >=4.0',
                      'pyqt',
                      'python-igraph >=0.7.1',
                      'scikit-learn >=0.19',
                      'scipy >=1.0.0',
                      'qtconsole >=4.3',
                      'matplotlib >=2.2',
                      'requests >=2.18',
                      'sqlalchemy >=1.2',
                      'pyarrow >=0.9.0',
                      'pluginbase >=1.0',
                      'pyyaml >=3.13',
                      'rdkit',
                      'numexpr >=2.7.0',
                      'xlrd',
                      'odfpy',
                      'feedparser',
                      'mplcursors',
                      'py2cytoscape >=0.7.0',
                      'libmetgem >=0.4',
                      'pyqtnetworkview >=0.5.1',
                      'forceatlas2 >=0.2',
                      'pyemf >=2.1.2alpha',
                      'pyqtads >=3.3.0',
                      'numba >=0.46.0',
                      'umap-learn >= 0.3.10',
                      'phate >= 0.4.5'],
    zip_safe=False
)
