import io
import json
import zipfile

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from numpy.compat import is_pathlib_path, basestring
from numpy.lib import format
from numpy.lib.npyio import NpzFile

from .config import FILE_EXTENSION


# Copy of numpy's _savez function to allow different file extension
# https://github.com/numpy/numpy/blob/master/numpy/lib/npyio.py#L669
# Copyright (c) 2005, NumPy Developers

# All rights reserved.

# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

    # Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
    # Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
    # Neither the name of the NumPy Developers nor the names of any contributors may be used to endorse or promote products derived from this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS “AS IS” AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


class MnzFile(NpzFile):

    def __init__(self, file, *args, **kwargs):
        if isinstance(file, basestring):
            fid = open(file, "rb")
            own_fid = True
        else:
            fid = file
            own_fid = False

        super().__init__(fid, own_fid, *args, **kwargs)
        self.parquet_files = [x[:-8] for x in self._files if x.endswith('.parquet')]

    def __getitem__(self, key):
        if key in self.parquet_files:
            with self.zip.open(key + '.parquet') as f:
                table = pq.read_table(io.BytesIO(f.read()))
            return table.to_pandas()

        val = super().__getitem__(key)

        if isinstance(val, bytes):
            try:
                return json.loads(val)
            except json.JSONDecodeError:
                return val
        else:
            return val
                

def zipfile_factory(file, *args, **kwargs):
    """
    Create a ZipFile.
    Allows for Zip64, and the `file` argument can accept file, str, or
    pathlib.Path objects. `args` and `kwargs` are passed to the zipfile.ZipFile
    constructor.
    """

    if is_pathlib_path(file):
        file = str(file)

    kwargs['allowZip64'] = True
    
    return zipfile.ZipFile(file, *args, **kwargs)
                           

def savez(file, version, *args, compress=True, **kwargs):
    if isinstance(file, basestring):
        if not file.endswith(FILE_EXTENSION):
            file = file + FILE_EXTENSION
    elif is_pathlib_path(file):
        if not file.name.endswith(FILE_EXTENSION):
            file = file.parent / (file.name + FILE_EXTENSION)

    namedict = kwargs
    for i, val in enumerate(args):
        key = 'arr_%d' % i
        if key in namedict.keys():
            raise ValueError(
                "Cannot use un-named variables and keyword %s" % key)
        namedict[key] = val

    if compress:
        compression = zipfile.ZIP_DEFLATED
    else:
        compression = zipfile.ZIP_STORED

    with zipfile_factory(file, mode="a", compression=compression) as zipf:
        # Write file format version
        zipf.writestr('version', str(version))
        
        # Write directly to a ZIP file
        for key, val in namedict.items():
            if isinstance(val, str):
                zipf.writestr(key, val)
            else:
                try:
                    s = json.dumps(val, indent=4)
                except TypeError:
                    if type(val).__module__ == 'pandas.core.frame':
                        fname = key + '.parquet'
                        force_zip64 = val.values.nbytes >= 2 ** 30
                        with zipf.open(fname, 'w', force_zip64=force_zip64) as fid:
                            pq.write_table(pa.Table.from_pandas(val), fid)
                    else:
                        fname = key + '.npy'
                        val = np.asanyarray(val)
                        force_zip64 = val.nbytes >= 2**30
                        with zipf.open(fname, 'w', force_zip64=force_zip64) as fid:
                            format.write_array(fid, val, allow_pickle=False)
                else:
                    zipf.writestr(key, s)
