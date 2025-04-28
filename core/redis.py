from redis.asyncio import Redis

_redis: Redis = None

def set_redis_connection(redis: Redis):
    global _redis
    _redis = redis

async def get_redis() -> Redis:
    return _redis
