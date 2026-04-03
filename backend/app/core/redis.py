"""
Redis client for caching, real-time presence, and session management.
"""

import redis.asyncio as redis

from app.core.config import get_settings

settings = get_settings()

# Async Redis client
redis_client = redis.from_url(
    settings.REDIS_URL,
    encoding="utf-8",
    decode_responses=True,
)


async def get_redis() -> redis.Redis:
    """Dependency to get Redis client."""
    return redis_client


# ── Presence tracking helpers ──

async def set_user_online(user_id: str) -> None:
    """Mark a user as online with 2-minute expiry (heartbeat-refreshed by agent)."""
    await redis_client.setex(f"presence:{user_id}", 120, "online")


async def set_user_idle(user_id: str) -> None:
    """Mark a user as idle."""
    await redis_client.setex(f"presence:{user_id}", 120, "idle")


async def set_user_offline(user_id: str) -> None:
    """Remove user's presence (offline)."""
    await redis_client.delete(f"presence:{user_id}")


async def get_user_status(user_id: str) -> str:
    """Get a user's current online status."""
    status = await redis_client.get(f"presence:{user_id}")
    return status or "offline"


async def get_all_online_users(org_id: str) -> dict[str, str]:
    """Get all online/idle users for an organization."""
    # In production, use a Redis Set per org for efficiency
    # This is a simplified version
    cursor = 0
    users = {}
    while True:
        cursor, keys = await redis_client.scan(cursor, match="presence:*", count=100)
        for key in keys:
            user_id = key.split(":")[1]
            status = await redis_client.get(key)
            if status:
                users[user_id] = status
        if cursor == 0:
            break
    return users
