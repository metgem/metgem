from PyInstaller.utils.hooks import collect_all, collect_submodules
datas, binaries, hiddenimports = collect_all('debugpy')
hiddenimports += collect_submodules('xmlrpc')