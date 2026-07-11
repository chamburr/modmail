from __future__ import annotations

import datetime
import logging

from typing import Any

from discord.utils import parse_time

log = logging.getLogger(__name__)


class Session:
    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data

    @property
    def session_id(self) -> str:
        return self._data["session_id"]

    @property
    def sequence(self) -> int:
        return self._data["sequence"]


class Status:
    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data

    @property
    def shard(self) -> int:
        return self._data["shard"]

    @property
    def status(self) -> str:
        return self._data["status"]

    @property
    def latency(self) -> float:
        return self._data["latency"]

    @property
    def last_ack(self) -> datetime.datetime:
        return parse_time(self._data["last_ack"].split(".")[0])
