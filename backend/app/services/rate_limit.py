"""Auth endpoint rate limiting backed by Redis."""

from app.config import Settings
from app.exceptions import RateLimitError
from app.redis_client import RedisClient

RATE_LIMIT_WINDOW_SECONDS = 60


def rate_limit_key(route: str, client_ip: str) -> str:
    """Build the Redis key for an auth route rate limit counter.

    Args:
        route: Auth route identifier such as register or login.
        client_ip: Client IP address.

    Returns:
        str: Redis key in the form auth_rl:{route}:{ip}.
    """
    return f"auth_rl:{route}:{client_ip}"


async def check_auth_rate_limit(
    redis: RedisClient,
    route: str,
    client_ip: str,
    settings: Settings,
) -> None:
    """Increment and enforce the auth route rate limit for a client IP.

    Args:
        redis: Active Redis client.
        route: Auth route identifier such as register or login.
        client_ip: Client IP address.
        settings: Application settings.

    Raises:
        RateLimitError: When the client exceeds the configured limit.
    """
    key = rate_limit_key(route, client_ip)
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, RATE_LIMIT_WINDOW_SECONDS)
    if count > settings.auth_rate_limit_per_minute:
        raise RateLimitError()
