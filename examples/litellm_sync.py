import time
import litellm
from litellm import completion
import os
from tb.litellm.handler import TinybirdLitellmHandler

customHandler = TinybirdLitellmHandler(
    api_url="https://api.us-east.aws.tinybird.co", 
    tinybird_token=os.getenv("TINYBIRD_TOKEN"), 
    datasource_name="litellm"
)

litellm.callbacks = [customHandler]

print("Running synchronous example...")
response = completion(
    model="gpt-3.5-turbo", 
    messages=[{"role": "user", "content": "Hi 👋 - i'm openai"}],
    stream=True
)

for chunk in response:
    print(chunk)

time.sleep(2)

print("\nTo run the async example, use the litellm_async.py script")
