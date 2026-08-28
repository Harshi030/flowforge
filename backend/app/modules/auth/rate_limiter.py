from app.core.config import Settings
from app.core.redis import redis_client

settings = Settings()

class LoginRateLimiter:
  def __init__(self, redis_client):
    self.redis = redis_client
    
  def is_allowed(self, key: str):
    count = self.redis.get(key)
    
    if count is None:
      return True
    
    return int(count) < settings.login_rate_limit_attempts
  
  def record_failure(self, key: str) -> int:
    count = self.redis.incr(key)
    
    if count == 1:
      self.redis.expire(
        key,
        settings.login_rate_limit_window_seconds
      )
      
      
    return count
  
  def reset(self, key: str) -> None:
    self.redis.delete(key)
