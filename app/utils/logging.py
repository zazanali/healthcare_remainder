
from contextvars import ContextVar
from datetime import datetime, timezone
import json
import logging
import sys
import uuid

_request_id: ContextVar[str] = ContextVar("request_id", default="-")

def get_request_id() -> str:
    return _request_id.get()

def set_request_id(value: str):
    _request_id.set(value)

class JsonFormatter(logging.Formatter):
    def format(self, record):
        data = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "msg": record.getMessage(),
            "logger": record.name,
            "request_id": get_request_id(),
        }
        if record.exc_info:
            data["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(data)

def configure_logging(level: str = "INFO"):
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())
    return root
