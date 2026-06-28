"""Redis client helpers."""

from typing import TYPE_CHECKING

from redis.asyncio import Redis

from app.config import Settings

if TYPE_CHECKING:
    RedisClient = Redis[str]
else:
    RedisClient = Redis

_redis_client: "RedisClient | None" = None


async def init_redis_client(settings: Settings) -> "RedisClient":
    """Create or return the shared application Redis client.

    Args:
        settings: Application settings.

    Returns:
        RedisClient: Shared async Redis client with connection pooling.
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
    return _redis_client


def get_shared_redis_client() -> "RedisClient":
    """Return the initialized shared Redis client.

    Returns:
        RedisClient: Shared async Redis client.

    Raises:
        RuntimeError: When the client has not been initialized.
    """
    if _redis_client is None:
        raise RuntimeError("Redis client is not initialized")
    return _redis_client


async def shutdown_redis_client() -> None:
    """Close the shared Redis client and reset module state."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()  # type: ignore[attr-defined]
        _redis_client = None


async def get_redis_client(settings: Settings) -> "RedisClient":
    """Return the shared Redis client, initializing it when needed.

    Args:
        settings: Application settings.

    Returns:
        RedisClient: Shared async Redis client.
    """
    return await init_redis_client(settings)


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
