import datetime
import logging
from typing import Any, Dict, Optional
from logging.handlers import QueueHandler
from logging.handlers import QueueListener
from multiprocessing import Queue
import inspect
from tb.datasource import Datasource


def log_record_to_dict(record: logging.LogRecord) -> Dict[str, Any]:
    """
    Convert a LogRecord object into a dictionary containing all its attributes,
    including args and kwargs if present.

    Args:
        record: The LogRecord instance to convert

    Returns:
        A dictionary containing all LogRecord attributes and extra fields
    """
    base_dict = {
        "name": record.name,
        "level": record.levelno,
        "levelname": record.levelname,
        "pathname": record.pathname,
        "filename": record.filename,
        "module": record.module,
        "lineno": record.lineno,
        "funcName": record.funcName,
        "created": record.created,
        "asctime": datetime.datetime.fromtimestamp(record.created).isoformat(),
        "msecs": record.msecs,
        "relativeCreated": record.relativeCreated,
        "thread": record.thread,
        "threadName": record.threadName,
        "process": record.process,
        "processName": record.processName,
        "message": record.getMessage(),  # This applies the formatting to % style messages
    }

    if record.exc_info:
        base_dict["exc_info"] = {
            "type": str(record.exc_info[0]),
            "value": str(record.exc_info[1]),
            "traceback": record.exc_text if record.exc_text else None,
        }

    if record.args:
        if isinstance(record.args, dict):
            base_dict["args"] = record.args
        else:
            base_dict["args"] = list(record.args)

    if record.stack_info:
        base_dict["stack_info"] = record.stack_info

    extra_attrs = {
        key: value
        for key, value in record.__dict__.items()
        if key not in logging.LogRecord.__dict__  # Skip standard LogRecord attributes
        and key not in base_dict  # Skip already processed attributes
        and not key.startswith("_")  # Skip private attributes
        and not inspect.ismethod(value)  # Skip methods
    }

    if extra_attrs:
        base_dict["extra"] = extra_attrs

    return base_dict


class TinybirdLoggingHandler(logging.Handler):
    def __init__(
        self,
        tinybird_admin_token: str,
        tinybird_api_url: str,
        app_name: str,
        ds_name: Optional[str] = None,
    ):
        super().__init__()
        self.tinybird_admin_token = tinybird_admin_token
        self.tinybird_api_url = tinybird_api_url
        self.app_name = app_name
        self.ds_name = ds_name or "tb_logs"

    def emit(self, record: logging.LogRecord) -> None:
        """
        Send the log record to the Tinybird.
        Override this method to implement your specific logging logic.
        """
        try:
            log_data = log_record_to_dict(record)
            log_data["formatted_message"] = self.format(record)
            log_data["app_name"] = self.app_name
            with Datasource(
                self.ds_name, self.tinybird_admin_token, api_url=self.tinybird_api_url
            ) as ds:
                ds << log_data
        except Exception as e:
            self.handleError(record)


class TinybirdLoggingQueueHandler(QueueHandler):
    def __init__(
        self,
        queue: Queue,
        tinybird_admin_token: str,
        tinybird_api_url: str,
        app_name: str,
        ds_name: Optional[str] = None,
    ):
        super().__init__(queue)
        self.handler = TinybirdLoggingHandler(
            tinybird_admin_token, tinybird_api_url, app_name, ds_name
        )
        self.listener = QueueListener(self.queue, self.handler)
        self.listener.start()
