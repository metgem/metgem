from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules('sklearn.utils', filter=lambda x: "tests" not in x.split("."))
