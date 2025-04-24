import redis.asyncio as redis
from app.config import settings

redis_client = redis.Redis(
    host=settings.redis_host,
    port=int(settings.redis_port),
    decode_responses=True
)
