try:
    import litellm
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
import logging


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
        self.api_version = api_version
        self.api = Tinybird(
            token=self.token, api_url=self.api_url, version=self.api_version
        )
        self.async_api = AsyncTinybird(
            token=self.token, api_url=self.api_url, version=self.api_version
        )

    def _extract_data(self, kwargs, response_obj, start_time, end_time):
        api_key = kwargs.get("api_key")
        if api_key and len(api_key) > 8:
            api_key = api_key[:4] + "****" + api_key[-4:]
        else:
            api_key = "****"

        data = {
            "model": kwargs.get("model"),
            "messages": kwargs.get("messages"),
            "user": kwargs.get("user"),
            "start_time": start_time,
            "end_time": end_time,
            "id": kwargs.get("litellm_call_id"),
            "stream": kwargs.get("stream", False),
            "call_type": kwargs.get("call_type", "completion"),
            "provider": kwargs.get("custom_llm_provider"),
            "log_event_type": kwargs.get("log_event_type"),
            "llm_api_duration_ms": kwargs.get("llm_api_duration_ms"),
            "response_headers": kwargs.get("response_headers", {}),
            "cache_hit": kwargs.get("cache_hit", False),
            "standard_logging_object_id": kwargs.get("standard_logging_object", {}).get(
                "id"
            ),
            "standard_logging_object_status": kwargs.get(
                "standard_logging_object", {}
            ).get("status"),
            "standard_logging_object_response_time": kwargs.get(
                "standard_logging_object", {}
            ).get("response_time"),
            "standard_logging_object_saved_cache_cost": kwargs.get(
                "standard_logging_object", {}
            ).get("saved_cache_cost"),
            "standard_logging_object_hidden_params": kwargs.get(
                "standard_logging_object", {}
            ).get("status"),
            "api_key": api_key,
        }

        # response = litellm.completion(model="gpt-3.5-turbo", messages=messages, metadata={"hello": "world"})
        litellm_params = kwargs.get("litellm_params", {})
        data["proxy_metadata"] = litellm_params.get("metadata", {})
        data["response"] = response_obj.json()
        data["cost"] = litellm.completion_cost(
            completion_response=response_obj,
            custom_llm_provider=kwargs.get("custom_llm_provider"),
        )

        data["exception"] = kwargs.get("exception", None)
        data["traceback"] = kwargs.get("traceback_exception", None)
        if isinstance(start_time, datetime) and isinstance(end_time, datetime):
            duration = (end_time - start_time).total_seconds()
        else:
            duration = end_time - start_time
        data["duration"] = duration
        return safe_json_dumps(data)


class TinybirdLitellmSyncHandler(TinybirdLitellmHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def log_success_event(self, kwargs, response_obj, start_time, end_time):
        try:
            data = self._extract_data(kwargs, response_obj, start_time, end_time)
            self.api.send(f"events?name={self.datasource_name}", data=data)
        except Exception as e:
            logging.error(f"Error logging success event: {e}")

    def log_failure_event(self, kwargs, response_obj, start_time, end_time):
        try:
            data = self._extract_data(kwargs, response_obj, start_time, end_time)
            self.api.send(f"events?name={self.datasource_name}", data=data)
        except Exception as e:
            logging.error(f"Error logging failure event: {e}")


class TinybirdLitellmAsyncHandler(TinybirdLitellmHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def async_log_success_event(self, kwargs, response_obj, start_time, end_time):
        try:
            data = self._extract_data(kwargs, response_obj, start_time, end_time)
            await self.async_api.send(f"events?name={self.datasource_name}", data=data)
        except Exception as e:
            logging.error(f"Error logging success event: {e}")

    async def async_log_failure_event(self, kwargs, response_obj, start_time, end_time):
        try:
            data = self._extract_data(kwargs, response_obj, start_time, end_time)
            await self.async_api.send(f"events?name={self.datasource_name}", data=data)
        except Exception as e:
            logging.error(f"Error logging failure event: {e}")
