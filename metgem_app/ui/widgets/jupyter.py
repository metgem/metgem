try:
    from PyQt5.QtWidgets import qApp
    from qtconsole.rich_jupyter_widget import RichJupyterWidget
    from qtconsole.inprocess import QtInProcessKernelManager
except ImportError:
    pass
else:
    import sys

    class JupyterWidget(RichJupyterWidget):

        def __init__(self):
            super().__init__()

            if 'asyncio' in sys.modules:
                self._init_asyncio_patch()

            self.kernel_manager = QtInProcessKernelManager()
            self.kernel_manager.start_kernel()

            self.kernel_client = self.kernel_manager.client()
            self.kernel_client.start_channels()

            # Fix issue with Jupyter 5.0+, see https://github.com/ipython/ipykernel/pull/376
            if hasattr(self.kernel_manager.kernel, '_abort_queue'):
                # noinspection PyProtectedMember
                self.kernel_manager.kernel._abort_queues = self.kernel_manager.kernel._abort_queue

            self.exit_requested.connect(self.stop)
            qApp.aboutToQuit.connect(self.stop)

        def _init_asyncio_patch(self):
            """set default asyncio policy to be compatible with tornado
            Tornado 6 (at least) is not compatible with the default
            asyncio implementation on Windows
            Pick the older SelectorEventLoopPolicy on Windows
            if the known-incompatible default policy is in use.
            do this as early as possible to make it a low priority and overrideable
            ref: https://github.com/tornadoweb/tornado/issues/2608
            FIXME: if/when tornado supports the defaults in asyncio,
                   remove and bump tornado requirement for py38
            """
            if sys.platform.startswith("win") and sys.version_info >= (3, 8):
                import asyncio
                try:
                    from asyncio import (
                        WindowsProactorEventLoopPolicy,
                        WindowsSelectorEventLoopPolicy,
                    )
                except ImportError:
                    pass
                    # not affected
                else:
                    if type(asyncio.get_event_loop_policy()) is WindowsProactorEventLoopPolicy:
                        # WindowsProactorEventLoopPolicy is not compatible with tornado 6
                        # fallback to the pre-3.8 default of Selector
                        asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())

        def stop(self):
            self.kernel_client.stop_channels()
            self.kernel_manager.shutdown_kernel()

        def push(self, **kwargs):
            self.kernel_manager.kernel.shell.push(kwargs)
