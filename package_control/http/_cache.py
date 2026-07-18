from __future__ import annotations

import calendar
import hashlib
import logging
import time
from collections.abc import Generator
from email.utils import formatdate, parsedate_tz
from typing import cast

from ..sys_path import pc_cache_dir
from ..vendor import anyio, httpx2

__all__ = ("AsyncCacheTransport", "AsyncHttpCache", "AsyncHttpCacheEntry")

logger = logging.getLogger(__package__)


def cache_control_fields(headers: httpx2.Headers) -> Generator[str]:
    src = headers.get("cache-control", "").lower()
    return (s.strip() for s in src.split(","))


def is_cachable(request: httpx2.Request) -> bool:
    return request.method in ("GET", "HEAD") and "no-store" not in cache_control_fields(request.headers)


def parsedate(date: str) -> int | None:
    tm = parsedate_tz(date)
    if tm is None:
        return None
    return calendar.timegm(tm[:6])


def generate_key(request: httpx2.Request, suffix: str = "") -> str:
    key = request.method + str(request.url)
    key = key.lower().encode("utf-8")
    key = hashlib.sha256(key).hexdigest()
    return key + suffix


class AsyncHttpCache:

    def __init__(self, max_age: int = 600, ttl: int = 604800):
        self.max_age: int = max_age
        self.ttl: int = ttl
        self.cache_root: anyio.Path = anyio.Path(pc_cache_dir(), "httpcache")
        self.last_pruned: int | None = None

    def is_fresh(self, headers: httpx2.Headers) -> bool:
        if "date" in headers and (response_time := parsedate(headers["date"])):
            if (age := int(time.time()) - response_time) <= self.max_age:
                logger.debug("Cached HTTP response %ds old. It's fresh.", age)
                return True
            logger.debug("Cached HTTP response %ds old. Needs validation.", age)
        return False

    async def prune_stale_entries(self):
        now = int(time.time())
        cookie = self.cache_root / ".pruned"

        if self.last_pruned is None:
            try:
                self.last_pruned = int((await cookie.read_text()).strip())
            except Exception:
                self.last_pruned = 0

        if now - self.last_pruned < self.ttl:
            return

        async for meta_file in self.cache_root.glob("*.meta"):
            content = await meta_file.read_text(encoding="utf-8")
            for line in content.splitlines():
                key, value = line.split(": ", 1)
                if (key == "date") and (response_date := parsedate(value)):
                    if now - response_date > self.ttl:
                        await meta_file.unlink(missing_ok=True)
                        await meta_file.with_suffix(".data").unlink(missing_ok=True)
                        logger.debug("Removed stale http cache: %s", meta_file.stem)

        await cookie.write_text(str(now))
        logger.info("Cleared http cache")

    async def aclose(self) -> None:
        await self.prune_stale_entries()


class AsyncHttpCacheEntry:

    def __init__(self, cache: AsyncHttpCache, request: httpx2.Request):
        self.cache: AsyncHttpCache = cache
        self.key: str = generate_key(request)

    @property
    def meta_file(self):
        return self.cache.cache_root.joinpath(self.key + ".meta")

    @property
    def data_file(self):
        return self.cache.cache_root.joinpath(self.key + ".data")

    async def get_headers(self) -> httpx2.Headers:
        headers = httpx2.Headers()
        try:
            content = await self.meta_file.read_text(encoding="utf-8")
            for line in content.splitlines():
                key, value = line.split(": ", 1)
                headers[key] = value
        except OSError:
            pass
        return headers

    async def get_content(self) -> bytes | None:
        try:
            return await self.data_file.read_bytes()
        except OSError:
            return None

    async def store_headers(self, response: httpx2.Response) -> None:
        if "date" not in response.headers:
            response.headers["date"] = formatdate(localtime=False, usegmt=True)

        # Note: Don't cache content-encoding and content-length as decoded content
        # is stored in cache and thus must not be decoded again when retrieving cache.
        ignored_headers = ("content-encoding", "content-length")
        content = "\n".join(
            f"{key}: {value}"
            for key, value in response.headers.items()
            if key not in ignored_headers
        )
        await self.meta_file.write_text(content, encoding="utf-8")

    async def store_response(self, response: httpx2.Response) -> None:
        await self.cache.cache_root.mkdir(parents=True, exist_ok=True)
        await self.data_file.write_bytes(await response.aread())
        await self.store_headers(response)


class AsyncCacheTransport(httpx2.AsyncBaseTransport):

    def __init__(
        self, transport: httpx2.AsyncBaseTransport, cache: AsyncHttpCache | None = None
    ) -> None:
        self.transport: httpx2.AsyncBaseTransport = transport
        self.cache: AsyncHttpCache = cache or AsyncHttpCache()

    async def handle_async_request(self, request: httpx2.Request) -> httpx2.Response:
        cache_entry = None
        if is_cachable(request):
            cache_entry = AsyncHttpCacheEntry(self.cache, request)
            if cached_headers := await cache_entry.get_headers():
                if self.cache.is_fresh(cached_headers):
                    if (cached_content := await cache_entry.get_content()) is not None:
                        cached_headers["content-length"] = str(len(cached_content))
                        response = httpx2.Response(
                            status_code=200,
                            headers=cached_headers,
                            content=cached_content,
                            request=request,
                            extensions={
                                "from_cache": True,
                                "cache_verified": False,
                            },
                        )
                        return response

                else:
                    # prepare verification request
                    if etag := cast(str, cached_headers.get("etag")):
                        request.headers["if-none-match"] = etag
                    if last_modified := cast(str, cached_headers.get("last-modified")):
                        request.headers["if-modified-since"] = last_modified

        response = await self.transport.handle_async_request(request)

        if cache_entry:
            if 200 <= response.status_code <= 299:
                if "no-store" not in cache_control_fields(response.headers):
                    await cache_entry.store_response(response)
                response.extensions["from_cache"] = False
                response.extensions["cache_verified"] = False

            elif response.status_code == 304:
                cached_content = await cache_entry.get_content()
                assert cached_content
                response.headers["content-length"] = str(len(cached_content))
                response.headers.pop("content-encoding", None)
                response.extensions["from_cache"] = True
                response.extensions["cache_verified"] = True
                response.extensions["reason_phrase"] = b"OK"
                response.status_code = 200
                response.stream = httpx2.ByteStream(cached_content)
                await cache_entry.store_headers(response)

        else:
            response.extensions["from_cache"] = False
            response.extensions["cache_verified"] = False

        return response

    async def aclose(self) -> None:
        await self.transport.aclose()
        await super().aclose()
        await self.cache.aclose()
