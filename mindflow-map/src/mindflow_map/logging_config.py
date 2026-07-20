"""结构化日志配置 + 敏感数据脱敏 + Correlation ID。"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from typing import Any, Dict, Optional

# 标准 LogRecord 属性，不进入 extra
_STANDARD_ATTRS: set[str] = {
    "name", "msg", "args", "created", "relativeCreated", "exc_info",
    "exc_text", "stack_info", "lineno", "funcName", "pathname",
    "filename", "module", "levelname", "levelno", "thread",
    "threadName", "process", "processName", "msecs", "message",
    "taskName",
}

# 需要脱敏的模式
_SENSITIVE_PATTERNS = [
    re.compile(r"(?i)(bearer\s+)[a-zA-Z0-9_\-\.]+"),
    re.compile(r"(?i)(api[_\-]?key\s*[=:]\s*)['\"]?[a-zA-Z0-9_\-]+['\"]?"),
    re.compile(r"(?i)(password\s*[=:]\s*)['\"]?[^'\"]+['\"]?"),
    re.compile(r"(?i)(secret\s*[=:]\s*)['\"]?[a-zA-Z0-9_\-]+['\"]?"),
    re.compile(r"(?i)(token\s*[=:]\s*)['\"]?[a-zA-Z0-9_\-]+['\"]?"),
    re.compile(r"(?i)(authorization\s*[=:]\s*)['\"]?[a-zA-Z0-9_\-]+['\"]?"),
    re.compile(r"(?i)(encryption[_\-]?key\s*[=:]\s*)['\"]?[a-zA-Z0-9_\-]+['\"]?"),
    re.compile(r"(?i)(aes[_\-]?key\s*[=:]\s*)['\"]?[a-zA-Z0-9_\-]+['\"]?"),
]


class SensitiveFilter(logging.Filter):
    """脱敏敏感数据。"""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = self._mask(record.msg)
        if record.args:
            record.args = tuple(
                self._mask(arg) if isinstance(arg, str) else arg
                for arg in record.args
            )
        return True

    def _mask(self, value: str) -> str:
        for pattern in _SENSITIVE_PATTERNS:
            value = pattern.sub(lambda m: m.group(1) + "***MASKED***", value)
        return value


class CorrelationIdFilter(logging.Filter):
    """注入 request_id。"""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            from mindflow_map.middleware.correlation_id import get_request_id
            record.request_id = get_request_id()
        except Exception:
            record.request_id = None
        return True


class JsonFormatter(logging.Formatter):
    """JSON 格式日志。"""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        request_id = getattr(record, "request_id", None)
        if request_id:
            log_entry["request_id"] = request_id
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)
        extra = {
            k: v
            for k, v in record.__dict__.items()
            if k not in _STANDARD_ATTRS and not k.startswith("_")
        }
        if extra:
            log_entry["extra"] = extra
        return json.dumps(log_entry, ensure_ascii=False)


class ConsoleFormatter(logging.Formatter):
    """控制台彩色格式。"""

    COLORS = {
        logging.DEBUG: "\033[36m",
        logging.INFO: "\033[32m",
        logging.WARNING: "\033[33m",
        logging.ERROR: "\033[31m",
        logging.CRITICAL: "\033[35m",
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelno, "")
        reset = self.RESET if color else ""
        timestamp = datetime.fromtimestamp(
            record.created, tz=timezone.utc
        ).strftime("%Y-%m-%d %H:%M:%S")
        base = (
            f"{color}{timestamp} [{record.levelname}] "
            f"{record.name}: {record.getMessage()}{reset}"
        )
        request_id = getattr(record, "request_id", None)
        if request_id:
            base += f" (request_id={request_id})"
        if record.exc_info and record.exc_info[0] is not None:
            base += "\n" + self.formatException(record.exc_info)
        return base


_LOGGING_CONFIGURED = False


def setup_logging() -> None:
    """配置日志。安全幂等。"""
    global _LOGGING_CONFIGURED
    if _LOGGING_CONFIGURED:
        return

    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    environment = os.getenv("ENVIRONMENT", "development").lower()

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level, logging.INFO))

    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    sensitive_filter = SensitiveFilter()
    correlation_filter = CorrelationIdFilter()

    if environment in ("production", "staging"):
        formatter = JsonFormatter()
        file_path = os.getenv("LOG_FILE", "logs/mindflow-map.log")
        os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
        file_handler = RotatingFileHandler(
            file_path,
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        file_handler.addFilter(sensitive_filter)
        file_handler.addFilter(correlation_filter)
        root_logger.addHandler(file_handler)
    else:
        formatter = ConsoleFormatter()
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        stream_handler.addFilter(sensitive_filter)
        stream_handler.addFilter(correlation_filter)
        root_logger.addHandler(stream_handler)

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)

    _LOGGING_CONFIGURED = True
