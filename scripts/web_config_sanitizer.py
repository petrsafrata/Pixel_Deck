"""
Standalone utility script for verifying the Pixel Deck config sanitizer.

Usage
-----
Run from the project root so that the ``src`` package is on the Python path::

    python scripts/web_config_sanitizer.py

What it does
------------
1. Loads ``config.yml`` from the current working directory.
2. Passes the raw dict through ``sanitize_config``, which strips or
   normalises any values that are unsafe to expose via the Web UI.
3. Prints the top-level keys of the sanitized result as a quick sanity
   check – no files are written.

This script is intended for local development and CI checks only.
It is not part of the main application startup.
"""
from __future__ import annotations

from pathlib import Path

from src.web.config_editor import load_config_dict, sanitize_config


def main() -> None:
    """
    Load ``config.yml``, sanitize it, and print the resulting top-level keys.

    Exits with a non-zero status implicitly if ``load_config_dict`` or
    ``sanitize_config`` raise an exception (e.g. file not found, YAML
    parse error, or validation failure).
    """
    config_path = Path("config/config.yml")
    data = load_config_dict(config_path)
    sanitized = sanitize_config(data)
    print("Sanitized config loaded, top-level keys:", ", ".join(sorted(sanitized.keys())))


if __name__ == "__main__":
    main()
