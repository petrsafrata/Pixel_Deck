from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

from PIL import Image


@lru_cache(maxsize=64)
def load_rgba_pixels(path: str, size: Optional[int] = None) -> tuple[list[tuple[int, int, int, int]], int, int]:
    """
    Load image as RGBA and return:
      - flat list of (r,g,b,a) pixels
      - width, height

    If size is provided, image is resized to (size, size) using NEAREST
    (pixel-perfect scaling for LED matrix look).
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Image not found: {path}")

    img = Image.open(p).convert("RGBA")

    if size is not None:
        s = int(size)
        img = img.resize((s, s), Image.NEAREST)

    w, h = img.size
    pixels = list(img.getdata())  # [(r,g,b,a), ...]
    return pixels, w, h
