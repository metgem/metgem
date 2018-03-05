class UserRequestedStopError(Exception):
    '''Raised if user request to stop a worker's process'''


class UnsupportedVersionError(OSError):
    pass