import asyncio
import json
import logging
from io import StringIO
from typing import Union, Dict, Any, Optional

from .api import AsyncAPI
from ..utils import bytes2human


class AsyncBuffer:
    def __init__(
        self,
        max_wait_seconds: float = 1,
        max_wait_records: int = 10000,
        max_wait_bytes: int = 1024 * 1024 * 1,
    ):
        self.records = 0
        self.max_wait_seconds = max_wait_seconds
        self.max_wait_records = max_wait_records
        self.max_wait_bytes = max_wait_bytes
        self.timer_task: Optional[asyncio.Task] = None
        self.timer_start = None
        self.sink = None
        self._lock = asyncio.Lock()

    async def append(self):
        async with self._lock:
            while self.sink and self.sink.wait:
                logging.info("Waiting while flushing...")
                await asyncio.sleep(0.1)

            self.records += 1
            if max(self.records % self.max_wait_records / 100, 10) == 0:
                logging.info(
                    f"Buffering {self.records} records and {bytes2human(self.sink.tell())} bytes"
                )

            if (
                self.records < self.max_wait_records
                and self.sink.tell() < self.max_wait_bytes
            ):
                if not self.timer_task or self.timer_task.done():
                    self.timer_start = asyncio.get_event_loop().time()
                    self.timer_task = asyncio.create_task(self._timer_callback())
            else:
                await self.flush()

    async def _timer_callback(self):
        await asyncio.sleep(self.max_wait_seconds)
        await self.flush()

    async def flush(self):
        async with self._lock:
            if self.timer_task and not self.timer_task.done():
                self.timer_task.cancel()
                self.timer_task = None
                self.timer_start = None

            if not self.records or not self.sink:
                return

            await self.sink.flush()
            self.records = 0


class AsyncDatasource:
    def __init__(
        self,
        datasource_name: str,
        token: str,
        api_url: str = "https://api.tinybird.co",
        buffer: Optional[AsyncBuffer] = None,
    ):
        self.datasource_name = datasource_name
        self.api = AsyncAPI(token, api_url)
        self.path = f"/events?name={self.datasource_name}&format=ndjson&wait=false"
        self.reset()
        self.buffer = buffer
        if not self.buffer:
            self.buffer = AsyncBuffer()
        self.buffer.sink = self
        self.wait = False
        self._lock = asyncio.Lock()

    def reset(self):
        self.chunk = StringIO()

    async def append(self, value: Union[str, bytes, Dict[str, Any]]):
        async with self._lock:
            if isinstance(value, bytes):
                value = value.decode("utf-8")
            if not isinstance(value, str):
                value = json.dumps(value)
            self.chunk.write(value + "\n")
            await self.buffer.append()

    def tell(self):
        return self.chunk.tell()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def __iadd__(self, row):
        await self.append(row)
        return self

    async def __lshift__(self, row):
        await self.append(row)
        return self

    async def close(self):
        await self.buffer.flush()
        await self.api.close()

    async def flush(self):
        async with self._lock:
            try:
                logging.info(
                    f"Flushing {self.buffer.records} records and {bytes2human(self.tell())} bytes to {self.datasource_name}"
                )
                self.wait = True
                data = self.chunk.getvalue()
                self.reset()
                await self.api.post(self.path, data=data)
            finally:
                self.wait = False
