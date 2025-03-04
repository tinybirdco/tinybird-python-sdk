import asyncio
import litellm
from litellm import acompletion
import os
from tb.litellm.handler import TinybirdLitellmHandler


async def main():
    # Set up the handler
    customHandler = TinybirdLitellmHandler(
        api_url="https://api.us-east.aws.tinybird.co",
        tinybird_token=os.getenv("TINYBIRD_TOKEN"),
        datasource_name="litellm",
    )

    litellm.callbacks = [customHandler]

    print("Running async example...")
    response = await acompletion(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Hi 👋 - i'm openai"}],
        stream=True,
    )

    async for chunk in response:
        print(chunk)

    # Wait for callbacks to complete
    await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(main())
