from .__version__ import __description__, __title__, __version__
from ._alias import *
from ._api import *
from ._auth import *
from ._client import *
from ._config import *
from ._content import *
from ._exceptions import *
from ._models import *
from ._sse import *
from ._status_codes import *
from ._transports import *
from ._types import *
from ._urls import *

__all__ = [
    # __version__.py
    "__description__",
    "__title__",
    "__version__",
    # _alias.py
    "alias_httpx",
    # _api.py
    "delete",
    "get",
    "head",
    "options",
    "patch",
    "post",
    "put",
    "query",
    "request",
    "stream",
    "websocket",
    # _auth.py
    "Auth",
    "BasicAuth",
    "DigestAuth",
    "FunctionAuth",
    "NetRCAuth",
    # _client.py
    "AsyncClient",
    "Client",
    "USE_CLIENT_DEFAULT",
    # _config.py
    "create_ssl_context",
    "Limits",
    "Proxy",
    "Timeout",
    # _content.py
    "ByteStream",
    # _exceptions.py
    "CloseError",
    "ConnectError",
    "ConnectTimeout",
    "CookieConflict",
    "DecodingError",
    "HTTPError",
    "HTTPStatusError",
    "InvalidURL",
    "LocalProtocolError",
    "NetworkError",
    "PoolTimeout",
    "ProtocolError",
    "ProxyError",
    "ReadError",
    "ReadTimeout",
    "RemoteProtocolError",
    "RequestError",
    "RequestNotRead",
    "ResponseNotRead",
    "StreamClosed",
    "StreamConsumed",
    "StreamError",
    "TimeoutException",
    "TooManyRedirects",
    "TransportError",
    "UnsupportedProtocol",
    "WriteError",
    "WriteTimeout",
    # _models.py
    "Cookies",
    "Headers",
    "Request",
    "Response",
    # _sse.py
    "EventSource",
    "ServerSentEvent",
    "SSEError",
    # _status_codes.py
    "codes",
    # _transports
    "ASGITransport",
    "AsyncBaseTransport",
    "AsyncHTTPTransport",
    "BaseTransport",
    "HTTPTransport",
    "MockTransport",
    "WSGITransport",
    # _types.py
    "AsyncByteStream",
    "SyncByteStream",
    # _urls.py
    "Origin",
    "QueryParams",
    "URL",
]


__locals = locals()
for __name in __all__:
    if not __name.startswith("__"):
        setattr(__locals[__name], "__module__", "httpx2")  # noqa


def __getattr__(name: str) -> object:  # pragma: no cover
    if name == "main":
        import warnings

        warnings.warn(
            "`httpx2.main` is deprecated and will be removed in a future release. "
            "Use the `httpx2` CLI entry point instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        from ._main import main

        return main

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
