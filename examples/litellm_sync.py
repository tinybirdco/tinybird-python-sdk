import time
import litellm
from litellm import completion
import os
from tb.litellm.handler import TinybirdLitellmSyncHandler

customHandler = TinybirdLitellmSyncHandler(
    api_url="https://api.us-east.aws.tinybird.co",
    tinybird_token=os.getenv("TINYBIRD_TOKEN"),
    datasource_name="litellm",
)

litellm.callbacks = [customHandler]

print("Running synchronous example...")
response = completion(
    model="anthropic/claude-3-5-sonnet-latest",
    messages=[{"role": "user", "content": "Hi 👋 - i'm claude"}],
    stream=True,
    user="test_user",
    metadata={
        "organization": "tinybird",
        "environment": "dev",
        "project": "litellm_test",
        "chat_id": "1234567890",
    },
)

for chunk in response:
    print(chunk)

time.sleep(2)

print("\nTo run the async example, use the litellm_async.py script")
