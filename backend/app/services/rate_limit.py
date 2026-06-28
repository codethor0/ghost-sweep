"""Auth endpoint rate limiting backed by Redis."""

from typing import cast

from app.config import Settings
from app.exceptions import RateLimitError
from app.redis_client import RedisClient

RATE_LIMIT_WINDOW_SECONDS = 60

_RATE_LIMIT_SCRIPT = """
local current = redis.call('INCR', KEYS[1])
if current == 1 then
  redis.call('EXPIRE', KEYS[1], ARGV[1])
end
return current
"""


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
    raw_count = await redis.eval(  # type: ignore[no-untyped-call]
        _RATE_LIMIT_SCRIPT,
        1,
        key,
        str(RATE_LIMIT_WINDOW_SECONDS),
    )
    count = int(cast(int, raw_count))
    if count > settings.auth_rate_limit_per_minute:
        raise RateLimitError()
