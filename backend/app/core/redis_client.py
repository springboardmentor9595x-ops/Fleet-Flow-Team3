"""Redis Pub/Sub transport for cross-instance GPS broadcasts."""
import asyncio
import json
import logging
import os
import uuid
from collections.abc import Awaitable, Callable

import redis
from redis.exceptions import RedisError


logger = logging.getLogger(__name__)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
GPS_CHANNEL = "fleetflow:gps:locations"

redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)


class RedisGPSPubSub:
    """Publish GPS events and forward events from other API instances."""

    def __init__(self) -> None:
        self.instance_id = str(uuid.uuid4())
        self._pubsub = None
        self._listener_task: asyncio.Task | None = None
        self._on_message: Callable[[uuid.UUID, dict], Awaitable[None]] | None = None
        self.available = False

    async def start(
        self,
        on_message: Callable[[uuid.UUID, dict], Awaitable[None]],
    ) -> bool:
        if self._listener_task and not self._listener_task.done():
            return self.available

        self._on_message = on_message
        try:
            await asyncio.to_thread(redis_client.ping)
            self._pubsub = redis_client.pubsub(ignore_subscribe_messages=True)
            await asyncio.to_thread(self._pubsub.subscribe, GPS_CHANNEL)
            self.available = True
            self._listener_task = asyncio.create_task(
                self._listen(), name="fleetflow-redis-gps-listener"
            )
            logger.info("Redis GPS Pub/Sub listener connected.")
        except RedisError:
            self.available = False
            self._pubsub = None
            logger.warning("Redis is unavailable; GPS broadcasts stay local.")
        return self.available

    async def publish(self, vehicle_id: uuid.UUID, message: dict) -> None:
        if not self.available:
            return

        event = json.dumps(
            {
                "origin": self.instance_id,
                "vehicle_id": str(vehicle_id),
                "message": message,
            }
        )
        try:
            await asyncio.to_thread(redis_client.publish, GPS_CHANNEL, event)
        except RedisError:
            self.available = False
            logger.warning("Redis publish failed; GPS broadcast stayed local.")

    async def _listen(self) -> None:
        try:
            while self.available and self._pubsub is not None:
                event = await asyncio.to_thread(
                    self._pubsub.get_message,
                    ignore_subscribe_messages=True,
                    timeout=1.0,
                )
                if not event or event.get("type") != "message":
                    continue
                payload = json.loads(event["data"])
                if payload.get("origin") == self.instance_id:
                    continue
                if self._on_message is not None:
                    await self._on_message(
                        uuid.UUID(payload["vehicle_id"]), payload["message"]
                    )
        except (RedisError, ValueError, json.JSONDecodeError) as error:
            self.available = False
            logger.warning("Redis GPS listener stopped: %s", error)

    async def stop(self) -> None:
        self.available = False
        if self._listener_task and not self._listener_task.done():
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass
        if self._pubsub is not None:
            try:
                await asyncio.to_thread(self._pubsub.close)
            except RedisError:
                pass
        self._pubsub = None
        self._listener_task = None


gps_pubsub = RedisGPSPubSub()
