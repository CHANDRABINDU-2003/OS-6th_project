"""core/logger.py - Central kernel logger.

A single log() function records timestamped events to data/logs.txt, keeps them
in an in-memory ring buffer, and pushes them to any subscribed listener (the
Kernel Log Window subscribes to get a live feed).
"""

import time

from utils import LOGS_FILE

LOG_BUFFER = []        # list of formatted log strings (capped)
_MAX_BUFFER = 500
_subscribers = []      # callables receiving each new formatted line


def log(message, level="INFO"):
    """Record an event. level is one of INFO / WARN / ERROR / BOOT."""
    line = f"[{time.strftime('%H:%M:%S')}] [{level}] {message}"

    LOG_BUFFER.append(line)
    if len(LOG_BUFFER) > _MAX_BUFFER:
        del LOG_BUFFER[0]

    try:
        with open(LOGS_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass

    for cb in list(_subscribers):
        try:
            cb(line)
        except Exception:
            pass

    return line


def subscribe(callback):
    """Register a callback(line:str) to receive new log lines live."""
    _subscribers.append(callback)


def unsubscribe(callback):
    if callback in _subscribers:
        _subscribers.remove(callback)


def get_logs():
    """Return a copy of the in-memory log buffer."""
    return list(LOG_BUFFER)
