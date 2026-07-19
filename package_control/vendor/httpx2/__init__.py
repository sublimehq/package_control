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
    "__description__",
    "__title__",
    "__version__",
    "alias_httpx",
    "ASGITransport",
    "AsyncBaseTransport",
    "AsyncByteStream",
    "AsyncClient",
    "AsyncHTTPTransport",
    "Auth",
    "BaseTransport",
    "BasicAuth",
    "ByteStream",
    "Client",
    "CloseError",
    "codes",
    "ConnectError",
    "ConnectTimeout",
    "CookieConflict",
    "Cookies",
    "create_ssl_context",
    "DecodingError",
    "delete",
    "DigestAuth",
    "EventSource",
    "FunctionAuth",
    "get",
    "head",
    "Headers",
    "HTTPError",
    "HTTPStatusError",
    "HTTPTransport",
    "InvalidURL",
    "Limits",
    "LocalProtocolError",
    "MockTransport",
    "NetRCAuth",
    "NetworkError",
    "options",
    "Origin",
    "patch",
    "PoolTimeout",
    "post",
    "ProtocolError",
    "Proxy",
    "ProxyError",
    "put",
    "query",
    "QueryParams",
    "ReadError",
    "ReadTimeout",
    "RemoteProtocolError",
    "request",
    "Request",
    "RequestError",
    "RequestNotRead",
    "Response",
    "ResponseNotRead",
    "ServerSentEvent",
    "SSEError",
    "stream",
    "StreamClosed",
    "StreamConsumed",
    "StreamError",
    "SyncByteStream",
    "Timeout",
    "TimeoutException",
    "TooManyRedirects",
    "TransportError",
    "UnsupportedProtocol",
    "URL",
    "USE_CLIENT_DEFAULT",
    "websocket",
    "WriteError",
    "WriteTimeout",
    "WSGITransport",
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
