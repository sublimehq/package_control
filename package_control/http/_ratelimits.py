from __future__ import annotations

import time

from ..vendor import httpx2


class AsyncRateLimitTransport(httpx2.AsyncBaseTransport):
    """
    This class describes a rate limit transport with legacy behaviror.

    The transport behaves like Package Control's legacy rate_limiting_downloader
    by just raising `RateLimitException` if a host's rate limit is being exceeded,
    skipping all further requests by `RateLimitSkipException`.
    """

    def __init__(self, *args, transport: httpx2.AsyncBaseTransport, **kwargs):
        super().__init__(*args, **kwargs)
        self._ratelimit_reset: dict[str, int] = {}
        self._transport: httpx2.AsyncBaseTransport = transport

    async def handle_async_request(self, request: httpx2.Request) -> httpx2.Response:
        if (host := request.url.host) in self._ratelimit_reset:
            if (reset := self._ratelimit_reset[host]) >= int(time.time()):
                return httpx2.Response(
                    status_code=429,
                    headers={"x-ratelimit-reset": str(reset)},
                    request=request,
                )

            del self._ratelimit_reset[host]

        response = await self._transport.handle_async_request(request)

        if (
            response.status_code in (403, 429)
            and int(response.headers.get("x-ratelimit-remaining", 1)) < 1
        ):
            self._ratelimit_reset[host] = int(response.headers.get("x-ratelimit-reset", "0"))
            response.status_code = 429

        return response
