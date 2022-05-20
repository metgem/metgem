from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules('sklearn.tree', filter=lambda x: "tests" not in x.split("."))
