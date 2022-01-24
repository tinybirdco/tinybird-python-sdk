# Tinybird Python SDK

SDK around Tinybird APIs.

If you want to manage Workspaces, Data Sources and Pipes you might be looking for the [tinybird-cli](https://pypi.org/project/tinybird-cli/).

The SDK is meant to programatically ingest `NDJSON` data.

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
- It automatically handle [Rate Limits](https://docs.tinybird.co/api-reference/api-reference.html#limits)
