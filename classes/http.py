import asyncio
import logging
import weakref

from urllib.parse import quote as _uriquote

import orjson

from discord import DiscordServerError, Forbidden, HTTPException, NotFound, http, utils
from discord.http import MaybeUnlock, Route

log = logging.getLogger(__name__)


async def json_or_text(response):
    text = await response.text(encoding="utf-8")
    try:
        if response.headers["content-type"] == "application/json":
            return orjson.loads(text)
    except KeyError:
        pass
    return text


class HTTPClient(http.HTTPClient):
    def __init__(self, connector=None, *, proxy=None, proxy_auth=None, loop=None, unsync_clock=True):
        self.loop = asyncio.get_event_loop() if loop is None else loop
        self.connector = connector
        self.__session = None
        self._locks = weakref.WeakValueDictionary()
        self._global_over = asyncio.Event()
        self._global_over.set()
        self.token = None
        self.bot_token = False
        self.proxy = proxy
        self.proxy_auth = proxy_auth
        self.use_clock = not unsync_clock

        self.user_agent = "DiscordBot (Custom, 1.0.0)"

    async def request(self, route, *, files=None, **kwargs):
        bucket = route.bucket
        method = route.method
        url = route.url

        lock = self._locks.get(bucket)
        if lock is None:
            lock = asyncio.Lock()
            if bucket is not None:
                self._locks[bucket] = lock

        headers = {
            "User-Agent": self.user_agent,
            "X-Ratelimit-Precision": "millisecond",
        }

        if self.token is not None:
            headers["Authorization"] = "Bot " + self.token if self.bot_token else self.token
        if "json" in kwargs:
            headers["Content-Type"] = "application/json"
            kwargs["data"] = utils.to_json(kwargs.pop("json"))

        try:
            reason = kwargs.pop("reason")
        except KeyError:
            pass
        else:
            if reason:
                headers["X-Audit-Log-Reason"] = _uriquote(reason, safe="/ ")

        kwargs["headers"] = headers

        if self.proxy is not None:
            kwargs["proxy"] = self.proxy
        if self.proxy_auth is not None:
            kwargs["proxy_auth"] = self.proxy_auth

        if not self._global_over.is_set():
            await self._global_over.wait()

        await lock.acquire()
        with MaybeUnlock(lock) as maybe_lock:
            for tries in range(5):
                if files:
                    for f in files:
                        f.reset(seek=tries)
                try:
                    async with self.__session.request(method, url, **kwargs) as r:
                        log.debug(f"{method} {url} with {kwargs.get('data')} has returned {r.status}")

                        data = await json_or_text(r)

                        remaining = r.headers.get("X-Ratelimit-Remaining")
                        if remaining == "0" and r.status != 429:
                            delta = utils._parse_ratelimit_header(r, use_clock=self.use_clock)
                            log.debug(f"A rate limit bucket has been exhausted (bucket: {bucket}, retry: {delta}).")
                            maybe_lock.defer()
                            self.loop.call_later(delta, lock.release)

                        if 300 > r.status >= 200:
                            log.debug(f"{method} {url} has received {data}", method, url, data)
                            return data

                        if r.status == 429:
                            if not r.headers.get("Via"):
                                raise HTTPException(r, data)

                            retry_after = data["retry_after"] / 1000.0
                            log.warning(
                                f"We are being rate limited. Retrying in {retry_after}.2f seconds."
                                f"Handled under the bucket '{bucket}'"
                            )

                            is_global = data.get("global", False)
                            if is_global:
                                log.warning(f"Global rate limit has been hit. Retrying in {retry_after}.2f seconds.")
                                self._global_over.clear()

                            await asyncio.sleep(retry_after)
                            log.debug("Done sleeping for the rate limit. Retrying...")

                            if is_global:
                                self._global_over.set()
                                log.debug("Global rate limit is now over.")

                            continue

                        if r.status in {500, 502}:
                            await asyncio.sleep(1 + tries * 2)
                            continue

                        if r.status == 403:
                            raise Forbidden(r, data)
                        elif r.status == 404:
                            raise NotFound(r, data)
                        elif r.status == 503:
                            raise DiscordServerError(r, data)
                        else:
                            raise HTTPException(r, data)

                except OSError as e:
                    if tries < 4 and e.errno in (54, 10054):
                        continue
                    raise

            if r.status >= 500:
                raise DiscordServerError(r, data)

            raise HTTPException(r, data)

    def request_guild_members(self, guild_id, query, limit=1):
        return self.request(
            Route(
                "GET",
                "/guilds/{guild_id}/members/search?query={query}&limit={limit}",
                guild_id=guild_id,
                query=query,
                limit=limit,
            )
        )
