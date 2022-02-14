from PyInstaller.depend import imphookapi

def pre_safe_import_module(api):
    """buit-in hook-six.moves fails with error 'Target module "six.moves.tkinter_dialog" already imported as "AliasNode('six.moves.tkinter_dialog', "'tkinter.dialog'")".'
    when called two times (Two analysis)."""
    imphookapi.PreSafeImportModuleAPI.add_runtime_module = lambda *args: None
    imphookapi.PreSafeImportModuleAPI.add_alias_module = lambda *args: None
