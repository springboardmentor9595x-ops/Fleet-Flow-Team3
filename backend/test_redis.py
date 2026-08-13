import asyncio
import redis.asyncio as redis


async def main():
    client = redis.from_url(
        "redis://127.0.0.1:6379",
        decode_responses=True,
    )

    try:
        result = await client.ping()
        print("Redis connection:", result)

    except Exception as error:
        print("Redis ERROR:", error)

    finally:
        await client.aclose()


asyncio.run(main())