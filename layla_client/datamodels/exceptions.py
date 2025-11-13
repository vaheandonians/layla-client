class LaylaError(Exception):
    pass


class JobTimeoutError(LaylaError):
    pass


class JobFailedError(LaylaError):
    pass


class NetworkError(LaylaError):
    pass


class AuthenticationError(LaylaError):
    pass

