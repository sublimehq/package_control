from __future__ import annotations

import secrets
import threading

import anyio


class PingManagerBase:
    def _generate_id(self) -> bytes:
        return secrets.token_bytes()


class PingManager(PingManagerBase):
    def __init__(self) -> None:
        self._pings: dict[bytes, threading.Event] = {}

    def create(self, ping_id: bytes | None = None) -> tuple[bytes, threading.Event]:
        ping_id = self._generate_id() if not ping_id else ping_id
        event = threading.Event()
        self._pings[ping_id] = event
        return ping_id, event

    def ack(self, ping_id: bytes | bytearray) -> None:
        event = self._pings.pop(bytes(ping_id), None)
        if event is not None:
            event.set()


class AsyncPingManager(PingManagerBase):
    def __init__(self) -> None:
        self._pings: dict[bytes, anyio.Event] = {}

    def create(self, ping_id: bytes | None = None) -> tuple[bytes, anyio.Event]:
        ping_id = self._generate_id() if not ping_id else ping_id
        event = anyio.Event()
        self._pings[ping_id] = event
        return ping_id, event

    def ack(self, ping_id: bytes | bytearray) -> None:
        event = self._pings.pop(bytes(ping_id), None)
        if event is not None:
            event.set()
