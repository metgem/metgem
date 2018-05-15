from PyInstaller.utils.hooks import collect_data_files, get_module_file_attribute

datas = collect_data_files('openbabel') + [(get_module_file_attribute('openbabel._openbabel'), 'openbabel')]