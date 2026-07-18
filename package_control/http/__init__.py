from __future__ import annotations

from collections.abc import Mapping

from ._client import AsyncClientFactory
from ._exceptions import DownloaderException
from ._urls import from_uri, resolve_url, update_url

__all__ = (
    "AsyncClientFactory",
    "DownloaderException",
    "from_uri",
    "http_get",
    "resolve_url",
    "update_url",
)


async def http_get(
    url: str, settings: Mapping[str, object], error_message: str = "", no_cache: bool = False
) -> bytes:
    """
    Performs a HTTP GET request using best matching downloader.

    :param url:
        The string URL to download

    :param settings:
        The dictionary with downloader settings.

          - ``http_basic_auth``
          - ``http_cache_max_age``
          - ``http_cache_ttl``
          - ``http_proxy``
          - ``http_retries``
          - ``http_timeout``
          - ``proxy_username``
          - ``proxy_password``

        Note: It is only applied if new client is to be created.

    :param error_message:
        The error message to include if the download fails

    :param no_cache:
        Disable local caching of request response.

    :raises:
        DownloaderException: if there was an error downloading the URL

    :return:
        The string contents of the URL
    """
    async with AsyncClientFactory(settings) as client:
        if no_cache:
            headers = {"cache-control": "no-cache,no-store"}
        else:
            headers = None
        try:
            response = await client.get(url, headers=headers)
        except Exception as exc:
            raise DownloaderException(f"{error_message} {exc}") from exc
        if response.is_error:
            raise DownloaderException(
                f"{error_message} HTTP error {response.status_code} for {url}"
            )
        return await response.aread()
