from __future__ import annotations

from ..vendor import anyio, httpx2
from ._urls import from_uri


def is_absolute_url(self):
    uri = self._uri_reference
    return bool(
        uri.scheme
        and (
            # handle remote URL
            uri.scheme != "file"
            and uri.host
            # handle file URL
            or uri.scheme == "file"
            and uri.host in ("", "localhost")
            and uri.path
        )
    )


# monkey patch to fix httpx URL parsing
httpx2.URL.is_absolute_url = property(is_absolute_url)  # type: ignore


class AsyncFileTransport(httpx2.AsyncBaseTransport):
    """
    Transport for file URIs.

    Supports "GET", "HEAD", "PUT" and "DELETE" methods.

    Usage:

        ```py
        class AsyncClient(
            mounts={"file://": AsyncFileTransport()},
        )
        ```
    """

    async def handle_async_request(self, request: httpx2.Request) -> httpx2.Response:
        content = None
        headers = {}

        if request.url.host and request.url.host != "localhost":
            raise NotImplementedError("Only local paths are allowed")

        filename = from_uri(str(request.url))

        if request.method == "DELETE":
            try:
                await anyio.Path(filename).unlink()
            except FileNotFoundError:
                status = 404  # Not Found
            except PermissionError:
                status = 403  # Forbidden
            else:
                status = 200  # OK

        elif request.method == "GET":
            try:
                async with await anyio.open_file(filename, mode="rb") as fp:
                    content = await fp.read()
            except FileNotFoundError:
                status = 404  # Not Found
            except PermissionError:
                status = 403  # Forbidden
            else:
                status = 200  # OK
                headers["Content-Length"] = str(len(content))

        elif request.method == "HEAD":
            try:
                if await anyio.Path(filename).is_file():
                    status = 204  # No content
                else:
                    status = 406  # Not Acceptable
            except FileNotFoundError:
                status = 404  # Not Found
            except PermissionError:
                status = 403  # Forbidden

        elif request.method == "PUT":
            try:
                async with await anyio.open_file(filename, mode="wb") as fp:
                    await fp.write(await request.aread())
            except PermissionError:
                status = 403  # Forbidden
            else:
                status = 200  # OK

        else:
            status = 405  # Method Not Allowed

        return httpx2.Response(
            status_code=status,
            headers=headers,
            content=content,
            request=request,
        )
