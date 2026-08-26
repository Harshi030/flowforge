import logging
import time
import uuid
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")

logger = logging.getLogger("app.access")

class RequestContextMiddleware(BaseHTTPMiddleware):
  async def dispatch(self, request:Request, call_next) -> Response:
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request_id_var.set(request_id)
    
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 1000,1)
    
    response.headers["X-Request-ID"] = request_id
    
    logger.info(
      "request completed",
      extra={
        "request_id":request_id,
        "method":request.method,
        "path":request.url.path,
        "status":response.status_code,
        "duration_ms":duration_ms
      }
    )
    
    return response