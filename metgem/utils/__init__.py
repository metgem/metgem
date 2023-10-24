import itertools
import os
import subprocess
import sys

def grouper(iterable, n, fillvalue=None):
    """Collect data into fixed-length chunks or blocks"""
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return itertools.zip_longest(*args, fillvalue=fillvalue)


def pairwise(iterable):
    """s -> (s0,s1), (s1,s2), (s2, s3), ..."""
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)


def open_folder(path: str):
    """Open a folder in file manager"""

    if sys.platform.startswith('win'):
        os.startfile(path)
    elif sys.platform.startswith('darwin'):
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])


def hasinstance(collection: list, type_: type):
    """Check if a collection has a member"""

    for item in collection:
        if isinstance(item, type_):
            return True
    return False
