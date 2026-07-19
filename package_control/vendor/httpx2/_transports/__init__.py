import sys

from .asgi import ASGITransport
from .base import AsyncBaseTransport, BaseTransport
from .mock import MockTransport
from .wsgi import WSGITransport

if sys.platform == "emscripten":  # pragma: nocover
    if sys.version_info < (3, 12):
        raise RuntimeError("httpx2 requires Python 3.12+ on Emscripten.")

    from httpx2_jsfetch import (
        AsyncJavascriptFetchTransport as AsyncHTTPTransport,
        JavascriptFetchTransport as HTTPTransport,
    )
else:
    from .default import AsyncHTTPTransport, HTTPTransport

__all__ = [
    "ASGITransport",
    "AsyncBaseTransport",
    "BaseTransport",
    "AsyncHTTPTransport",
    "HTTPTransport",
    "MockTransport",
    "WSGITransport",
]
