"""Structured Logging Utility."""

import logging
import sys
from src.utils.security import sanitize_log_message


class SanitizedFormatter(logging.Formatter):
    """Formatter that sanitizes secrets before emitting logs."""
    def format(self, record: logging.LogRecord) -> str:
        original = super().format(record)
        sanitized = sanitize_log_message(original)
        encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
        try:
            sanitized.encode(encoding)
            return sanitized
        except (UnicodeEncodeError, AttributeError):
            return sanitized.encode(encoding, errors="replace").decode(encoding)



def get_logger(name: str = "qet_accelerator") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        formatter = SanitizedFormatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


logger = get_logger()
