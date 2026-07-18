from __future__ import annotations

import asyncio
import logging
import os
import ssl
import weakref
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .. import __version__
from ..sys_path import user_config_dir
from ..vendor import httpx2
from ._auth import HostSpecificBasicAuth
from ._cache import AsyncCacheTransport, AsyncHttpCache
from ._file import AsyncFileTransport
from ._ratelimits import AsyncRateLimitTransport

logger = logging.getLogger(__package__)


class AsyncClientFactory:
    """
    A context manager to create or re-use a shared httpx2 client on demand.
    """

    MAX_IDLE_TIME = 30.0
    """The idle time to close and destroy the client after"""

    _client: httpx2.AsyncClient | None = None
    """Active HTTP client in use"""

    _ref_count: int = 0
    """Number of active users holding a reference of the http client."""

    _idle_task: asyncio.Task | None = None
    """Task to close connections and delete client after a period of no usage."""

    _lock = asyncio.Lock()

    def __init__(self, settings: Mapping[str, Any]):
        self.settings = settings

    async def __aenter__(self) -> httpx2.AsyncClient:
        return await self.aquire(self.settings)

    async def __aexit__(self, *args) -> None:
        await self.release()

    @classmethod
    async def aquire(cls, settings: Mapping[str, Any]) -> httpx2.AsyncClient:
        if cls._idle_task:
            cls._idle_task.cancel()
            cls._idle_task = None

        cls._ref_count += 1

        if cls._client is None:
            async with cls._lock:
                if cls._client is None:
                    cls._client = await cls.create_client(settings)

        return weakref.proxy(cls._client)

    @classmethod
    async def release(cls) -> None:
        cls._ref_count -= 1
        if cls._ref_count < 1:
            cls._ref_count = 0

            if cls._idle_task:
                cls._idle_task.cancel()
            cls._idle_task = asyncio.create_task(cls.close_client())

    @classmethod
    async def create_client(cls, settings: Mapping[str, Any]) -> httpx2.AsyncClient:
        """
        Creates a HTTP client.

        :param settings:
            A dictionary with settings

        :returns:
            httpx2.Client object
        """
        logger.info("Creating http client")

        # setup ssl_context
        ssl_context = await asyncio.get_running_loop().run_in_executor(
            None,
            create_ssl_context,
        )

        # setup http(s) proxy
        proxy = None
        if (proxy_url := settings.get("http_proxy")) and (
            proxy_url := os.path.expandvars(proxy_url)
        ):
            proxy_url = httpx2.URL(proxy_url)

            # setup authentication
            proxy_auth = None
            if (proxy_user := settings.get("proxy_username")) and (
                proxy_user := os.path.expandvars(proxy_user)
            ):
                proxy_auth = (
                    proxy_user,
                    os.path.expandvars(settings.get("proxy_password", "")),
                )

            # instantiate proxy
            proxy = httpx2.Proxy(
                url=proxy_url,
                auth=proxy_auth,
                ssl_context=ssl_context if proxy_url.scheme == "https" else None,
            )

        if logger.getEffectiveLevel() == logging.DEBUG:
            event_hooks = {"request": [log_request], "response": [log_response]}
        else:
            event_hooks = None

        return httpx2.AsyncClient(
            auth=HostSpecificBasicAuth(settings.get("http_basic_auth", {})),
            event_hooks=event_hooks,
            follow_redirects=True,
            headers={
                "cache-control": "no-cache",
                "user-agent": f"Mozilla/5.0 (Package Control v{__version__})",
            },
            mounts={"file://": AsyncFileTransport()},
            timeout=settings.get("http_timeout", 10),
            transport=AsyncCacheTransport(
                transport=AsyncRateLimitTransport(
                    transport=httpx2.AsyncHTTPTransport(
                        http2=True,
                        proxy=proxy,
                        retries=settings.get("http_retries", 3),
                        verify=ssl_context,
                    ),
                ),
                cache=AsyncHttpCache(
                    max_age=settings.get("http_max_age", 1200),
                    ttl=settings.get("http_cache_ttl", 604800),
                ),
            ),
        )

    @classmethod
    async def close_client(cls) -> None:
        if cls._client:
            await asyncio.sleep(cls.MAX_IDLE_TIME)
            client = cls._client
            cls._client = None
            if client and cls._ref_count < 1:
                await client.aclose()
                logger.info("Closed http client")


def create_ssl_context() -> ssl.SSLContext:
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.load_default_certs()
    ctx.check_hostname = True
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    ctx.verify_flags = ssl.VERIFY_X509_TRUSTED_FIRST | ssl.VERIFY_X509_STRICT
    ctx.verify_mode = ssl.CERT_REQUIRED
    ctx.set_ciphers("ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:TLS_AES_256_GCM_SHA384")

    extra_ca = Path(user_config_dir(), "Package Control.user-ca-bundle")
    try:
        # must be large enough to contain at least one certificate
        if extra_ca.stat().st_size > 100:
            ctx.load_verify_locations(extra_ca)
            logger.debug("Loaded extra CA %s", extra_ca)
    except FileNotFoundError:
        pass
    except BaseException:
        logger.exception("Failed to load extra CA.")

    return ctx


async def log_request(request: httpx2.Request) -> None:
    message = f'{request.method} "{request.url!s}"'
    for k, v in request.headers.items():
        message += f"\n  {k}: {v}"
    for k, v in request.extensions.items():
        message += f"\n  {k}: {v}"
    logger.debug(message)


async def log_response(response: httpx2.Response) -> None:
    message = f'Got {response.status_code} for "{response.url!s}"'
    for k, v in response.headers.items():
        message += f"\n  {k}: {v}"
    for k, v in response.extensions.items():
        message += f"\n  {k}: {v}"
    logger.debug(message)
