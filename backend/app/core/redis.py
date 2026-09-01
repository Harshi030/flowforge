import redis

from app.core.config import Settings

settings = Settings()

redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
