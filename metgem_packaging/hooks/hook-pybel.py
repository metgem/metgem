# noinspection PyUnresolvedReferences
import openbabel
from PyInstaller.utils.hooks import collect_data_files

# noinspection PyProtectedMember
datas = [(openbabel._openbabel.__file__, 'openbabel')]
d = collect_data_files('openbabel')
datas += d
datas += [(x, '') for x, _ in d if x.endswith('.dll') or x.endswith('.so')]
