try:
    from PyQt5.QtWidgets import qApp
    from qtconsole.rich_jupyter_widget import RichJupyterWidget
    from qtconsole.inprocess import QtInProcessKernelManager
    import tornado
except ImportError:
    pass
else:
    import sys

    class JupyterWidget(RichJupyterWidget):

        def __init__(self):
            super().__init__()

            self.kernel_manager = QtInProcessKernelManager()
            self.kernel_manager.start_kernel()

            self.kernel_client = self.kernel_manager.client()
            self.kernel_client.start_channels()

            self.exit_requested.connect(self.stop)
            qApp.aboutToQuit.connect(self.stop)

        def stop(self):
            self.kernel_client.stop_channels()
            self.kernel_manager.shutdown_kernel()

        def push(self, **kwargs):
            self.kernel_manager.kernel.shell.push(kwargs)
