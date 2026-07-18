from __future__ import annotations

from collections.abc import Generator
from os.path import expandvars

from ..vendor import httpx2


class HostSpecificBasicAuth(httpx2.Auth):
    """
    Allows the 'auth' argument to be passed as a (username, password) pair,
    and uses HTTP Basic authentication.
    """

    def __init__(self, auth: dict[str, tuple[str, str]]) -> None:
        self._auth: dict[str, httpx2.BasicAuth] = {
            host: httpx2.BasicAuth(*map(expandvars, user_password))
            for host, user_password in auth.items()
        }

    def auth_flow(self, request: httpx2.Request) -> Generator[httpx2.Request, httpx2.Response, None]:
        if request.url.host in self._auth:
            yield from self._auth[request.url.host].auth_flow(request)
        else:
            yield request
