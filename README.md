# Tinybird Python SDK

SDK around Tinybird APIs.

If you want to manage Workspaces, Data Sources and Pipes you might be looking for the [tinybird-cli](https://pypi.org/project/tinybird-cli/).

The SDK is meant to programatically ingest `NDJSON` data or send any request to an `API` instance.

## Ingest to a Tinybird DataSource

```python
from tb.datasource import Datasource

with Datasource(datasource_name, token) as ds:
    ds << {'key': 'value', 'key1': 'value1'}
```

```python
from tb.datasource import Datasource

with Datasource(datasource_name, token, api_url='https://api.us-east.tinybird.co') as ds:
    ds << {'key': 'value', 'key1': 'value1'}
```

Alternatively you can do:

```python
from tb.datasource import Datasource

ds = Datasource(datasource_name, token)
for json_obj in list_of_json:
    ds << json_obj

# just remember to flush the remaining json_obj at the end
ds.flush()
```

Notes:
- The `Datasource` object does some in-memory buffering and uses the [events API](https://docs.tinybird.co/api-reference/datasource-api.html#post-v0-events). 
- It only supports `ndjson` data
- It automatically handles [Rate Limits](https://docs.tinybird.co/api-reference/api-reference.html#limits)

## Ingest using an API instance

```python

from tb.api import API

api = API(token, api_url)
api.post('/v0/datasources', params={
                              'name': 'datasource_name',
                              'mode': 'append',
                              'format': 'ndjson',
                              'url': 'https://storage.googleapis.com/davidm-wadus/events.ndjson',
                          })
```

- It automatically handle [Rate Limits](https://docs.tinybird.co/api-reference/api-reference.html#limits)
- Works with any Tinybird API
- The `post`, `get`, `send` methods signatures are equivalent to the [requests](https://docs.python-requests.org/en/latest/) library.

## Logging from your Python module to a Tinybird Data Source

```python
import logging
from tb.logger import TinybirdLoggingHandler
from dotenv import load_dotenv

load_dotenv()
TB_API_URL = os.getenv("TB_API_URL")
TB_ADMIN_TOKEN = os.getenv("TB_ADMIN_TOKEN")

logger = logging.getLogger('your-logger-name')
handler = TinybirdLoggingHandler(TB_API_URL, TB_ADMIN_TOKEN, 'your-app-name')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
```

Each time you call the logger an event to the `tb_logs` DataSource in your Workspace is sent.

To configure the DataSource name initialize the `TinybirdLogginHandler` like this:

```python
handler = TinybirdLoggingHandler(TB_API_URL, TB_ADMIN_TOKEN, 'your-app-name', ds_name="your_tb_ds_name")
```

### Non-blocking logging

If you want to avoid blocking the main thread you can use a queue to send the logs to a different thread.

```python
import logging
from multiprocessing import Queue
from tb.logger import TinybirdLoggingQueueHandler
from dotenv import load_dotenv

load_dotenv()
TB_API_URL = os.getenv("TB_API_URL")
TB_ADMIN_TOKEN = os.getenv("TB_ADMIN_TOKEN")

logger = logging.getLogger('your-logger-name')
handler = TinybirdLoggingQueueHandler(Queue(-1), TB_API_URL, TB_ADMIN_TOKEN, 'your-app-name', ds_name="your_tb_ds_name")
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
```
