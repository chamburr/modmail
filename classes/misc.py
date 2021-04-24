import logging

from discord.utils import parse_time

log = logging.getLogger(__name__)


class Session:
    def __init__(self, data):
        self._data = data

    @property
    def session_id(self):
        return self._data["session_id"]

    @property
    def sequence(self):
        return self._data["sequence"]


class Status:
    def __init__(self, data):
        self._data = data

    @property
    def shard(self):
        return self._data["shard"]

    @property
    def status(self):
        return self._data["status"]

    @property
    def latency(self):
        return self._data["latency"]

    @property
    def last_ack(self):
        return parse_time(self._data["last_ack"].split(".")[0])
