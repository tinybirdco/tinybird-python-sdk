try:
    from litellm.integrations.custom_logger import CustomLogger
except ImportError:
    raise ImportError(
        "AI extension not found. Please install it using 'pip install tinybird-python-sdk[ai]'"
    )

import os
import json
from datetime import datetime
from tb.a.api import AsyncAPI as AsyncTinybird
from tb.api import API as Tinybird


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        try:
            return super().default(obj)
        except TypeError:
            return str(obj)


def safe_json_dumps(data):
    return json.dumps(data, cls=CustomJSONEncoder)


class TinybirdLitellmHandler(CustomLogger):
    def __init__(
        self,
        api_url: str = "https://api.us-east.aws.tinybird.co",
        tinybird_token: str = os.getenv("TINYBIRD_TOKEN"),
        datasource_name: str = "litellm",
        api_version: str = "v0",
    ):
        self.token = tinybird_token
        self.api_url = api_url
        self.datasource_name = datasource_name
        self.api = Tinybird(
            token=self.token, api_url=self.api_url, api_version=api_version
        )
        self.async_api = AsyncTinybird(
            token=self.token, api_url=self.api_url, api_version=api_version
        )

    def log_success_event(self, kwargs, response_obj, start_time, end_time):
        self.api.send(
            f"events?name={self.datasource_name}",
            data=safe_json_dumps(
                {
                    "kwargs": kwargs,
                    "response_obj": response_obj,
                    "start_time": start_time,
                    "end_time": end_time,
                }
            ),
        )

    def log_failure_event(self, kwargs, response_obj, start_time, end_time):
        self.api.send(
            f"events?name={self.datasource_name}",
            data=safe_json_dumps(
                {
                    "kwargs": kwargs,
                    "response_obj": response_obj,
                    "start_time": start_time,
                    "end_time": end_time,
                }
            ),
        )

    #### ASYNC #### - for acompletion/aembeddings
    async def async_log_success_event(self, kwargs, response_obj, start_time, end_time):
        await self.async_api.send(
            f"events?name={self.datasource_name}",
            data=safe_json_dumps(
                {
                    "kwargs": kwargs,
                    "response_obj": response_obj,
                    "start_time": start_time,
                    "end_time": end_time,
                }
            ),
        )

    async def async_log_failure_event(self, kwargs, response_obj, start_time, end_time):
        await self.async_api.send(
            f"events?name={self.datasource_name}",
            data=safe_json_dumps(
                {
                    "kwargs": kwargs,
                    "response_obj": response_obj,
                    "start_time": start_time,
                    "end_time": end_time,
                }
            ),
        )
