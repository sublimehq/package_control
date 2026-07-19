from __future__ import annotations

import contextlib
import math
import typing
from types import TracebackType

import anyio
import wsproto
from anyio.streams.stapled import StapledObjectStream
from wsproto.frame_protocol import CloseReason

from .._models import Request, Response
from .._transports.asgi import ASGITransport, _ASGIApp
from .._types import AsyncByteStream
from ._exceptions import WebSocketDisconnect, WebSocketUpgradeError

Scope = dict[str, typing.Any]
Message = dict[str, typing.Any]
Receive = typing.Callable[[], typing.Awaitable[Message]]
Send = typing.Callable[[Scope], typing.Coroutine[None, None, None]]
ASGIApp = typing.Callable[[Scope, Receive, Send], typing.Coroutine[None, None, None]]


class ASGIWebSocketTransportError(Exception):
    pass


class UnhandledASGIMessageType(ASGIWebSocketTransportError):
    def __init__(self, message: Message) -> None:
        self.message = message


class UnhandledWebSocketEvent(ASGIWebSocketTransportError):
    def __init__(self, event: wsproto.events.Event) -> None:
        self.event = event


class ASGIWebSocketAsyncNetworkStream:
    def __init__(
        self,
        app: ASGIApp,
        scope: Scope,
        task_group: anyio.abc.TaskGroup,
        initial_receive_timeout: float = 1.0,
    ) -> None:
        self.app = app
        self.scope = scope
        self._receive_queue = StapledObjectStream(*anyio.create_memory_object_stream[Message](max_buffer_size=math.inf))
        self._send_queue = StapledObjectStream(*anyio.create_memory_object_stream[Message](max_buffer_size=math.inf))
        self._task_group = task_group
        self._initial_receive_timeout = initial_receive_timeout
        self.connection = wsproto.WSConnection(wsproto.ConnectionType.SERVER)
        self.connection.initiate_upgrade_connection(scope["headers"], scope["path"])
        self._aentered = False

    async def __aenter__(
        self,
    ) -> tuple[ASGIWebSocketAsyncNetworkStream, bytes]:
        if self._aentered:
            raise RuntimeError("Cannot use ASGIWebSocketAsyncNetworkStream in a context manager twice")
        self._aentered = True
        self._task_group.start_soon(self._run)
        async with contextlib.AsyncExitStack() as stack:
            stack.push_async_callback(self.aclose)
            await self.send({"type": "websocket.connect"})

            try:
                message = await self.receive(self._initial_receive_timeout)
            except TimeoutError as e:
                raise RuntimeError(
                    "WebSocket didn't accept the connection in time. Did you forget to call accept()?"
                ) from e

            if message["type"] == "websocket.close":
                await stack.aclose()
                raise WebSocketDisconnect(message["code"], message.get("reason"))

            # Websocket Denial Response extension
            # Ref: https://asgi.readthedocs.io/en/latest/extensions.html#websocket-denial-response
            if message["type"] == "websocket.http.response.start":
                status_code: int = message["status"]
                headers: list[tuple[bytes, bytes]] = message["headers"]
                body: list[bytes] = []
                while True:
                    message = await self.receive()
                    assert message["type"] == "websocket.http.response.body"
                    body.append(message["body"])
                    if not message.get("more_body", False):
                        break

                await stack.aclose()
                raise WebSocketUpgradeError(Response(status_code, headers=headers, content=b"".join(body)))

            assert message["type"] == "websocket.accept"
            retval = self, self._build_accept_response(message)
            self._exit_stack = stack.pop_all()
        return retval

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None:
        return await self._exit_stack.__aexit__(exc_type, exc_val, exc_tb)

    async def read(self, max_bytes: int, timeout: float | None = None) -> bytes:
        message: Message = await self.receive(timeout=timeout)
        type = message["type"]

        if type not in {"websocket.send", "websocket.close"}:
            raise UnhandledASGIMessageType(message)

        event: wsproto.events.Event
        if type == "websocket.send":
            data_str: str | None = message.get("text")
            if data_str is not None:
                event = wsproto.events.TextMessage(data_str)
            data_bytes: bytes | None = message.get("bytes")
            if data_bytes is not None:
                event = wsproto.events.BytesMessage(data_bytes)
        elif type == "websocket.close":
            event = wsproto.events.CloseConnection(message["code"], message["reason"])

        return self.connection.send(event)

    async def write(self, buffer: bytes, timeout: float | None = None) -> None:
        self.connection.receive_data(buffer)
        for event in self.connection.events():
            if isinstance(event, wsproto.events.Request):
                pass
            elif isinstance(event, wsproto.events.CloseConnection):
                await self.send(
                    {
                        "type": "websocket.disconnect",
                        "code": event.code,
                        "reason": event.reason,
                    }
                )
            elif isinstance(event, wsproto.events.TextMessage):
                await self.send({"type": "websocket.receive", "text": event.data})
            elif isinstance(event, wsproto.events.BytesMessage):
                await self.send({"type": "websocket.receive", "bytes": event.data})
            else:
                raise UnhandledWebSocketEvent(event)

    async def aclose(self) -> None:
        with contextlib.suppress(anyio.ClosedResourceError):
            await self.send({"type": "websocket.disconnect"})
        await self._receive_queue.aclose()
        await self._send_queue.aclose()

    async def send(self, message: Message) -> None:
        await self._receive_queue.send(message)

    async def receive(self, timeout: float | None = None) -> Message:
        if timeout is None:
            timeout = math.inf
        with anyio.fail_after(timeout):
            return await self._send_queue.receive()

    async def _run(self) -> None:
        """
        The sub-thread in which the websocket session runs.
        """
        scope = self.scope
        receive = self._receive_queue.receive
        send = self._send_queue.send
        try:
            await self.app(scope, receive, send)
        except Exception as e:
            message = {
                "type": "websocket.close",
                "code": CloseReason.INTERNAL_ERROR,
                "reason": str(e),
            }
            with contextlib.suppress(anyio.ClosedResourceError):
                await send(message)

    def _build_accept_response(self, message: Message) -> bytes:
        subprotocol = message.get("subprotocol", None)
        headers = message.get("headers", [])
        return self.connection.send(
            wsproto.events.AcceptConnection(
                subprotocol=subprotocol,
                extra_headers=headers,
            )
        )


class ASGIWebSocketTransport(ASGITransport):
    def __init__(
        self,
        app: _ASGIApp,
        raise_app_exceptions: bool = True,
        root_path: str = "",
        client: tuple[str, int] = ("127.0.0.1", 123),
        initial_receive_timeout: float = 1.0,
    ) -> None:
        super().__init__(app, raise_app_exceptions, root_path, client)
        self._exit_stack: contextlib.AsyncExitStack | None = None
        self._initial_receive_timeout = initial_receive_timeout

    async def __aenter__(self) -> ASGIWebSocketTransport:
        async with contextlib.AsyncExitStack() as stack:
            self._task_group = await stack.enter_async_context(anyio.create_task_group())
            self._exit_stack = stack.pop_all()

        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_val: BaseException | None = None,
        exc_tb: TracebackType | None = None,
    ) -> None:
        await super().__aexit__(exc_type, exc_val, exc_tb)
        assert self._exit_stack is not None
        await self._exit_stack.__aexit__(exc_type, exc_val, exc_tb)

    async def handle_async_request(self, request: Request) -> Response:
        scheme = request.url.scheme
        headers = request.headers

        if scheme in {"ws", "wss"} or headers.get("upgrade") == "websocket":
            subprotocols: list[str] = []
            if (subprotocols_header := headers.get("sec-websocket-protocol")) is not None:
                subprotocols = subprotocols_header.split(",")

            scope = {
                "type": "websocket",
                "path": request.url.path,
                "raw_path": request.url.raw_path,
                "root_path": self.root_path,
                "scheme": scheme,
                "query_string": request.url.query,
                "headers": [(k.lower(), v) for (k, v) in request.headers.raw],
                "client": self.client,
                "server": (request.url.host, request.url.port),
                "subprotocols": subprotocols,
            }
            return await self._handle_ws_request(request, scope)

        return await super().handle_async_request(request)

    async def _create_asgi_websocket_async_network_stream(
        self,
        *,
        task_status: anyio.abc.TaskStatus[tuple[ASGIWebSocketAsyncNetworkStream, bytes]],
    ) -> None:
        stream = ASGIWebSocketAsyncNetworkStream(
            self.app,  # type: ignore[arg-type]
            self.scope,
            self._task_group,
            self._initial_receive_timeout,
        )
        assert self._exit_stack is not None
        result = await self._exit_stack.enter_async_context(stream)
        task_status.started(result)

    async def _handle_ws_request(
        self,
        request: Request,
        scope: Scope,
    ) -> Response:
        assert isinstance(request.stream, AsyncByteStream)

        self.scope = scope
        stream, accept_response = await self._task_group.start(self._create_asgi_websocket_async_network_stream)
        accept_response_lines = accept_response.decode("utf-8").splitlines()
        headers = [
            typing.cast(tuple[str, str], line.split(": ", 1))
            for line in accept_response_lines[1:]
            if line.strip() != ""
        ]

        return Response(
            status_code=101,
            headers=headers,
            extensions={"network_stream": stream},
        )
