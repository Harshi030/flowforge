import json
import logging
import sys
from datetime import datetime,timezone
from app.core.middleware import request_id_var

class JsonFormatter(logging.Formatter):
  
  def format(self, record:logging.LogRecord) -> str:
    log:dict[str,object] = {
      "ts":datetime.now(timezone.utc).isoformat(),
      "level":record.levelname,
      "logger":record.name,
      "msg":record.getMessage(),
      "request_id":request_id_var.get()
    }
    
    for key in ("request_id", "path", "method", "status", "duration_ms"):
      value = getattr(record,key,None)
      if value is not None:
        log[key] = value
        
    if record.exc_info:
      log["exc_info"] = self.formatException(record.exc_info)
      
    return json.dumps(log)
  
def setup_logging(level: str) -> None:
  handler = logging.StreamHandler(sys.stdout)
  handler.setFormatter(JsonFormatter())
  root = logging.getLogger()
  root.setLevel(level.upper())
  root.handlers.clear()
  root.addHandler(handler)