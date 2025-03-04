import asyncio
import os
from tb.a.datasource import AsyncDatasource

# Example usage
async def example():
    token = os.getenv("TINYBIRD_TOKEN")
    async with AsyncDatasource(
        datasource_name="my_datasource",
        token=token
    ) as datasource:
        await datasource.append({"key": "value1"})
        
        await (datasource << {"key": "value3"})
        
        for i in range(100):
            if i % 2 == 0:
                await datasource.append({"index": i, "value": f"append_{i}"})
            else:
                await (datasource << {"index": i, "value": f"lshift_{i}"})
            
    datasource = AsyncDatasource(
        datasource_name="my_datasource",
        token=token
    )
    try:
        await datasource.append({"method": "append"})
        await (datasource << {"method": "lshift"})
        
        await datasource.flush()
    finally:
        await datasource.close()


if __name__ == "__main__":
    asyncio.run(example()) 