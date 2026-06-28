"""Redis client helpers."""

from typing import TYPE_CHECKING

from redis.asyncio import Redis

from app.config import Settings

if TYPE_CHECKING:
    RedisClient = Redis[str]
else:
    RedisClient = Redis


async def get_redis_client(settings: Settings) -> "RedisClient":
    """Create a Redis client from settings.

    Args:
        settings: Application settings.

    Returns:
        RedisClient: Async Redis client.
    """
    return Redis.from_url(settings.redis_url, decode_responses=True)


async def check_redis_connection(client: "RedisClient") -> bool:
    """Verify Redis connectivity.

    Args:
        client: Redis client instance.

    Returns:
        bool: True when Redis responds to PING.
    """
    response = await client.ping()
    return response is True


async def close_redis_client(client: "RedisClient") -> None:
    """Close a Redis client and its connection pool.

    Args:
        client: Redis client instance.
    """
    await client.aclose()  # type: ignore[attr-defined]
