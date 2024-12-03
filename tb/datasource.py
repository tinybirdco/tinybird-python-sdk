from .api import API
from .utils import bytes2human
from io import StringIO
import json
import time
from threading import Timer, Thread
import logging


class Datasource:
    def __init__(
        self, datasource_name, token, api_url="https://api.tinybird.co", buffer=None
    ):
        self.datasource_name = datasource_name
        self.api = API(token, api_url)
        self.path = (
            f"/events?mode=append&name={self.datasource_name}&format=ndjson&wait=false"
        )
        self.reset()
        self.buffer = buffer
        if not self.buffer:
            self.buffer = Buffer()
        self.buffer.sink = self
        self.wait = False

    def reset(self):
        self.chunk = StringIO()

    def append(self, value):
        if isinstance(value, bytes):
            value = value.decode("utf-8")
        if not isinstance(value, str):
            value = json.dumps(value)
        self.chunk.write(value + "\n")
        self.buffer.append()

    def tell(self):
        return self.chunk.tell()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.buffer.flush()

    def __iadd__(self, row):
        self.append(row)
        return self

    def __lshift__(self, row):
        self.append(row)
        return self

    def flush(self):
        try:
            logging.info(
                f"Flushing {self.buffer.records} records and {bytes2human(self.tell())} bytes to {self.datasource_name}"
            )
            self.wait = True
            data = self.chunk.getvalue()
            self.reset()
            self.api.post(self.path, data=data)
        finally:
            self.wait = False


class Buffer:
    def __init__(
        self, max_wait_seconds=1, max_wait_records=10000, max_wait_bytes=1024 * 1024 * 1
    ):
        self.records = 0
        self.max_wait_seconds = max_wait_seconds
        self.max_wait_records = max_wait_records
        self.max_wait_bytes = max_wait_bytes
        self.records = 0
        self.timer = None
        self.timer_start = None

    def append(self):
        while self.sink.wait:
            logging.info("Waiting while flushing...")
            time.sleep(0.1)
        self.records += 1
        if max(self.records % self.max_wait_records / 100, 10) == 0:
            logging.info(
                f"Buffering {self.records} records and {bytes2human(self.sink.tell())} bytes"
            )
        if (
            self.records < self.max_wait_records
            and self.sink.tell() < self.max_wait_bytes
        ):
            if not self.timer:
                self.timer_start = time.monotonic()
                self.timer = Timer(self.max_wait_seconds, self.flush)
                self.timer.name = f"f{self.__class__}_timer"
                self.timer.start()
        else:
            self.flush()

    def flush(self):
        if self.timer:
            self.timer.cancel()
            self.timer = None
            self.timer_start = None
        if not self.records:
            return
        self.sink.flush()
        self.records = 0
