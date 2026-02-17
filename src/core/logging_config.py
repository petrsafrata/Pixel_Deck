from __future__ import annotations

import logging
import sys

try:
    import colorama

    colorama.just_fix_windows_console()
    _COLORAMA = True
except Exception:
    _COLORAMA = False


class _ColorFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": "\x1b[36m",     # cyan
        "INFO": "\x1b[32m",      # green
        "WARNING": "\x1b[33m",   # yellow
        "ERROR": "\x1b[31m",     # red
        "CRITICAL": "\x1b[41m",  # red background
    }
    RESET = "\x1b[0m"

    def format(self, record: logging.LogRecord) -> str:
        msg = super().format(record)
        color = self.COLORS.get(record.levelname)
        if color:
            return f"{color}{msg}{self.RESET}"
        return msg


def setup_logging(level: str = "INFO") -> None:
    """
    Configure root logger once. Use per-module loggers via logging.getLogger(__name__).
    """
    root = logging.getLogger()
    numeric = getattr(logging, level.upper(), logging.INFO)
    root.setLevel(numeric)

    # prevent duplicate handlers if setup_logging called twice
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)

    base_fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    date_fmt = "%H:%M:%S"

    if _COLORAMA:
        handler.setFormatter(_ColorFormatter(base_fmt, datefmt=date_fmt))
    else:
        handler.setFormatter(logging.Formatter(base_fmt, datefmt=date_fmt))

    root.addHandler(handler)
