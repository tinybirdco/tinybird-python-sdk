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

You can also use the async version:

```python
from tb.a.datasource import AsyncDatasource

async with AsyncDatasource(datasource_name, token, api_url='https://api.us-east.tinybird.co') as ds:
    await ds << {'key': 'value', 'key1': 'value1'}
```

Notes:
- The `Datasource` object does some in-memory buffering and uses the [events API](https://www.tinybird.co/docs/v2/get-data-in/events-api). 
- It only supports `ndjson` data
- It automatically handles [Rate Limits](https://www.tinybird.co/docs/get-started/plans/limits#ingestion-limits-api)

## Ingest using an API instance

```python

from tb.a.api import AsyncAPI

async with AsyncAPI(token, api_url) as api:
    await api.post('datasources',
        params={
            'name': 'datasource_name',
            'mode': 'append',
            'format': 'ndjson',
            'url': 'https://storage.googleapis.com/davidm-wadus/events.ndjson',
        }
    )
```

- It automatically handles [Rate Limits](https://docs.tinybird.co/api-reference/api-reference.html#limits)
- Works with any Tinybird API
- The `post`, `get`, `send` methods signatures are equivalent to the [requests](https://docs.python-requests.org/en/latest/) library.

## Logging from your Python module to a Tinybird Data Source

```python
import logging
from tb.logger import TinybirdLoggingHandler
from dotenv import load_dotenv

load_dotenv()
TB_API_URL = os.getenv("TB_API_URL")
TB_WRITE_TOKEN = os.getenv("TB_WRITE_TOKEN")

logger = logging.getLogger('your-logger-name')
handler = TinybirdLoggingHandler(TB_API_URL, TB_WRITE_TOKEN, 'your-app-name')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
```

Each time you call the logger an event to the `tb_logs` DataSource in your Workspace is sent.

To configure the DataSource name initialize the `TinybirdLogginHandler` like this:

```python
handler = TinybirdLoggingHandler(TB_API_URL, TB_WRITE_TOKEN, 'your-app-name', ds_name="your_tb_ds_name")
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
TB_WRITE_TOKEN = os.getenv("TB_WRITE_TOKEN")

logger = logging.getLogger('your-logger-name')
handler = TinybirdLoggingQueueHandler(Queue(-1), TB_API_URL, TB_WRITE_TOKEN, 'your-app-name', ds_name="your_tb_ds_name")
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
```

## Logging from Litellm to a Tinybird Data Source

Install the `ai` extra:

```
pip install tinybird-python-sdk[ai]
```

Then use the following handler:

```python
from tb.litellm.handler import TinybirdLitellmHandler

customHandler = TinybirdLitellmHandler(
    api_url="https://api.us-east.aws.tinybird.co", 
    tinybird_token=os.getenv("TINYBIRD_TOKEN"), 
    datasource_name="litellm"
)

litellm.callbacks = [customHandler]

response = await acompletion(
    model="gpt-3.5-turbo", 
    messages=[{"role": "user", "content": "Hi 👋 - i'm openai"}],
    stream=True
)
```
