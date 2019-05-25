from .session import create_session

import errno
import os


class SpectraLibrary:

    def __init__(self, database, echo=False):
        database = f'{database}.sqlite' if not database.endswith('.sqlite') else database
        self.database = database
        self.echo = echo
        self._session = None

    def __enter__(self):
        return self

    def __exit__(self, type_, value, traceback):
        self.close()

    def close(self):
        if self._session is not None:
            self._session.close()
            self._session.bind.dispose()
            self._session = None

    @property
    def session(self):
        if self._session is None:
            if not os.path.exists(self.database):
                raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), self.database)
            self._session = create_session(self.database, echo=self.echo, read_only=True)
        return self._session

    def __getattr__(self, item):
        return getattr(self.session, item)
