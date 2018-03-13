# Build instructions for Windows (Python 3.6, 64 bits)
Some useful tools are downloaded automatically when running build scripts.
Wheel packages for igraph can be found on [Christoph Gohlke's website](https://www.lfd.uci.edu/~gohlke/pythonlibs/#python-igraph)
Use of [Anaconda](https://anaconda.org/) distribution is recommended.

```
> conda create --name tsne-network
> cd packaging
> activate.bat tsne-network
> conda install pip
> pip install invoke==0.22.1
> invoke check-dependencies
> pip install python_igraph-*.whl
> pip install -r ..\requirements.txt
> conda install -c rdkit rdkit
> pip install pyinstaller pypiwin32
> invoke build
> deactivate.bat
```

# Build instructions for Mac OS (Python 3.6, 64 bits)
First install brew and Python 3, using [these instructions](http://docs.python-guide.org/en/latest/starting/install3/osx/)

```bash
$ python3 -m venv packaging
$ cd packaging
$ source bin/activate
$ pip3 install -r ../requirements.txt
$ pip3 install pyinstaller dmgbuild invoke==0.22.1
$ invoke build
$ source bin/deactivate
```