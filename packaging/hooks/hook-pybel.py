from PyInstaller.utils.hooks import collect_data_files, get_module_file_attribute

datas = [(get_module_file_attribute('openbabel._openbabel'), 'openbabel')]
d = collect_data_files('openbabel')
datas += d
datas += [(x, '') for x, _ in d if x.endswith('.dll')]
