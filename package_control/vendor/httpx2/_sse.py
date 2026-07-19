"""
Server-sent events support, derived from httpx-sse (https://github.com/florimondmanca/httpx-sse).

```
MIT License

Copyright (c) 2022 Florimond Manca

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
"""

from __future__ import annotations

import json as jsonlib
from collections.abc import AsyncIterator, Iterator
from dataclasses import dataclass

from ._config import DEFAULT_MAX_EVENT_SIZE_BYTES
from ._exceptions import TransportError, request_context
from ._models import Response

__all__ = ["EventSource", "SSEError", "ServerSentEvent"]


class SSEError(TransportError):
    """
    An error that occurred while connecting to a server-sent events endpoint.
    """


@dataclass(frozen=True)
class ServerSentEvent:
    event: str = "message"
    data: str = ""
    id: str = ""
    retry: int | None = None

    def json(self) -> object:
        return jsonlib.loads(self.data)


class _SSEEventDecoder:
    def __init__(self, max_event_size: int | None = None) -> None:
        self._max_event_size = max_event_size
        self._event = ""
        self._data: list[str] = []
        self._event_size = 0
        self._last_event_id = ""
        self._retry: int | None = None
        self._pending = False

    def decode(self, line: str) -> ServerSentEvent | None:
        if not line:
            self._event_size = 0
            if not self._pending:
                return None

            sse = ServerSentEvent(
                event=self._event or "message",
                data="\n".join(self._data),
                id=self._last_event_id,
                retry=self._retry,
            )
            self._event = ""
            self._data = []
            self._retry = None
            self._pending = False
            return sse

        if line.startswith(":"):
            return None

        self._event_size += len(line.encode("utf-8"))
        self._check_size()

        fieldname, _, value = line.partition(":")
        value = value[1:] if value.startswith(" ") else value

        if fieldname == "event":
            self._event = value
            self._pending = True
        elif fieldname == "data":
            self._data.append(value)
            self._pending = True
        elif fieldname == "id":
            if "\0" not in value:
                self._last_event_id = value
                self._pending = True
        elif fieldname == "retry":
            try:
                self._retry = int(value)
                self._pending = True
            except ValueError:
                pass

        return None

    def check_pending(self, pending_size: int) -> None:
        """
        Bound the total bytes buffered for the in-progress event, including
        a trailing line that has not been terminated by a newline yet.
        """
        self._check_size(pending_size)

    def _check_size(self, pending_size: int = 0) -> None:
        if self._max_event_size is not None and self._event_size + pending_size > self._max_event_size:
            raise SSEError(f"Server-sent event exceeded the {self._max_event_size} byte limit.")


class _SSELineDecoder:
    def __init__(self) -> None:
        self._parts: list[str] = []
        self._pending_size = 0
        self._trailing_cr = False

    @property
    def pending_size(self) -> int:
        return self._pending_size

    def decode(self, text: str) -> list[str]:
        if self._trailing_cr:
            text = "\r" + text
            self._trailing_cr = False
        if text.endswith("\r"):
            self._trailing_cr = True
            text = text[:-1]

        text = text.replace("\r\n", "\n").replace("\r", "\n")
        if "\n" not in text:
            self._append(text)
            return []

        lines = text.split("\n")
        self._append(lines[0])
        lines[0] = self._consume_pending()
        self._append(lines.pop())
        return lines

    def flush(self) -> list[str]:
        if self._trailing_cr:
            self._append("\n")
            self._trailing_cr = False
        buffer = self._consume_pending()
        if not buffer:
            return []
        return buffer.split("\n")

    def _append(self, text: str) -> None:
        if text:
            self._parts.append(text)
            self._pending_size += len(text.encode("utf-8"))

    def _consume_pending(self) -> str:
        pending = "".join(self._parts)
        self._parts = []
        self._pending_size = 0
        return pending


class _SSEParser:
    def __init__(self, max_event_size: int | None = None) -> None:
        self._event_decoder = _SSEEventDecoder(max_event_size)
        self._line_decoder = _SSELineDecoder()

    def decode(self, text: str) -> Iterator[ServerSentEvent]:
        yield from self._decode_lines(self._line_decoder.decode(text))
        self._event_decoder.check_pending(self._line_decoder.pending_size)

    def flush(self) -> Iterator[ServerSentEvent]:
        yield from self._decode_lines(self._line_decoder.flush())

    def _decode_lines(self, lines: list[str]) -> Iterator[ServerSentEvent]:
        for line in lines:
            sse = self._event_decoder.decode(line)
            if sse is not None:
                yield sse


class EventSource:
    def __init__(self, response: Response, max_event_size: int | None = DEFAULT_MAX_EVENT_SIZE_BYTES) -> None:
        self._response = response
        self._max_event_size = max_event_size

    @property
    def response(self) -> Response:
        return self._response

    def _check_content_type(self) -> None:
        content_type, _, _ = self._response.headers.get("content-type", "").partition(";")
        if content_type.strip().lower() != "text/event-stream":
            raise SSEError(f"Expected response with content type 'text/event-stream', got {content_type.strip()!r}.")

    def __iter__(self) -> Iterator[ServerSentEvent]:
        with request_context(request=self._response.request):
            self._check_content_type()
            parser = _SSEParser(self._max_event_size)
            for chunk in self._response.iter_text():
                yield from parser.decode(chunk)
            yield from parser.flush()

    async def __aiter__(self) -> AsyncIterator[ServerSentEvent]:
        with request_context(request=self._response.request):
            self._check_content_type()
            parser = _SSEParser(self._max_event_size)
            async for chunk in self._response.aiter_text():
                for sse in parser.decode(chunk):
                    yield sse
            for sse in parser.flush():
                yield sse
