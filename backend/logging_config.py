import logging
import json
import sys
from datetime import datetime


class JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "ts": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # include any extra fields set via `extra` kwarg
        if hasattr(record, "extra") and isinstance(record.extra, dict):
            payload.update(record.extra)
        # attach exception info if present
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(level=logging.INFO):
    root = logging.getLogger()
    if root.handlers:
        # avoid double configuration
        return
    root.setLevel(level)
    h = logging.StreamHandler(stream=sys.stdout)
    h.setLevel(level)
    h.setFormatter(JsonFormatter())
    root.addHandler(h)
