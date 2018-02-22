def _has_binding(api):
    return True

import qtconsole.qt_loaders
qtconsole.qt_loaders.has_binding = _has_binding