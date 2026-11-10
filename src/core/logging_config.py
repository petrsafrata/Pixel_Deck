"""
Logging configuration for Pixel Deck.

Responsibilities
----------------
* Configure the root logger once at startup (``setup_logging``).
* Provide coloured console output when *colorama* is available.
* Keep a thread-safe in-memory ring-buffer of recent log entries so the
  Web UI can display live logs without reading log files.

The ring-buffer (``LOG_BUFFER``) stores up to 1 000 entries and is
populated by ``InMemoryLogHandler``, which is attached to the root logger
alongside the console ``StreamHandler``.
"""
from __future__ import annotations

import logging
import sys
from collections import deque
from datetime import datetime, timezone
from threading import Lock

try:
    import colorama

    colorama.just_fix_windows_console()
    _COLORAMA = True
except Exception:
    _COLORAMA = False


LOG_BUFFER: deque[dict] = deque(maxlen=1000)
"""Ring-buffer of the most recent 1 000 log entries (thread-safe via ``LOG_BUFFER_LOCK``)."""

LOG_BUFFER_LOCK = Lock()


class _ColorFormatter(logging.Formatter):
    """
    ``logging.Formatter`` subclass that wraps each formatted message in the
    ANSI escape sequence matching its log level.

    Falls back to the plain message string for unknown levels.
    Only used when *colorama* is available (``_COLORAMA = True``).
    """

    COLORS = {
        "DEBUG": "\x1b[36m",    # cyan
        "INFO": "\x1b[32m",     # green
        "WARNING": "\x1b[33m",  # yellow
        "ERROR": "\x1b[31m",    # red
        "CRITICAL": "\x1b[41m", # red background
    }
    RESET = "\x1b[0m"

    def format(self, record: logging.LogRecord) -> str:
        msg = super().format(record)
        color = self.COLORS.get(record.levelname)
        if color:
            return f"{color}{msg}{self.RESET}"
        return msg


class InMemoryLogHandler(logging.Handler):
    """
    ``logging.Handler`` that appends every emitted record to ``LOG_BUFFER``.

    Each entry is a plain dict with the following keys:

    * ``timestamp`` – ISO-8601 UTC string
    * ``level``     – level name (``"INFO"``, ``"WARNING"``, …)
    * ``levelno``   – numeric level (used for numeric comparisons in ``get_recent_logs``)
    * ``logger``    – logger name (e.g. ``"src.scenes.clock"``)
    * ``message``   – fully formatted log message
    """

    def emit(self, record: logging.LogRecord) -> None:
        entry = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "levelno": record.levelno,
            "logger": record.name,
            "message": record.getMessage(),
        }
        with LOG_BUFFER_LOCK:
            LOG_BUFFER.append(entry)


def setup_logging(level: str = "INFO") -> None:
    """
    Configure the root logger once and attach the in-memory log buffer.

    Clears any existing handlers on the root logger before adding:

    * A coloured ``StreamHandler`` to *stdout* (colour only when *colorama*
      is available).
    * An ``InMemoryLogHandler`` that feeds the Web UI log viewer.

    Parameters
    ----------
    level:
        Minimum log level string (``"DEBUG"``, ``"INFO"``, ``"WARNING"``,
        ``"ERROR"``).  Invalid values fall back to ``"INFO"``.
    """
    root = logging.getLogger()
    numeric = getattr(logging, str(level).upper(), logging.INFO)
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
    root.addHandler(InMemoryLogHandler())


def get_recent_logs(limit: int = 200, level: str | None = None) -> list[dict]:
    """
    Return the most recent log entries from the in-memory buffer.

    Parameters
    ----------
    limit:
        Maximum number of entries to return (clamped to at least 1).
    level:
        If given, only entries at this level or above are included
        (e.g. ``"WARNING"`` returns warnings, errors, and criticals).
        Unknown level strings are ignored and all entries are returned.

    Returns
    -------
    list[dict]
        Entries in chronological order (oldest first), each with the keys
        described in ``InMemoryLogHandler``.
    """
    limit = max(1, int(limit))

    with LOG_BUFFER_LOCK:
        items = list(LOG_BUFFER)

    if level:
        level_num = getattr(logging, level.upper(), None)
        if isinstance(level_num, int):
            items = [item for item in items if item.get("levelno", 0) >= level_num]

    return items[-limit:]


def clear_recent_logs() -> None:
    """Remove all entries from the in-memory log buffer."""
    with LOG_BUFFER_LOCK:
        LOG_BUFFER.clear()


def set_log_level(level: str) -> None:
    """
    Change the root logger's minimum level at runtime.

    Used by the Web UI to temporarily enable ``DEBUG`` logging without
    restarting the application.

    Parameters
    ----------
    level:
        Target level string.  Invalid values fall back to ``"INFO"``.
    """
    root = logging.getLogger()
    numeric = getattr(logging, str(level).upper(), logging.INFO)
    root.setLevel(numeric)
