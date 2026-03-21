from __future__ import annotations

from typing import Tuple, Optional

from src.gfx.font5x7 import FONT_5X7

Color = Tuple[int, int, int]


def hex_to_rgb(value: str) -> Color:
    v = value.strip().lstrip("#")
    if len(v) != 6:
        raise ValueError(f"Invalid hex color: {value}")
    r = int(v[0:2], 16)
    g = int(v[2:4], 16)
    b = int(v[4:6], 16)
    return (r, g, b)


def draw_text(renderer, x: int, y: int, text: str, color: Color, scale: int = 1, spacing: int = 1) -> None:
    """
    Draw text using 5x7 bitmap font.
    scale=1 draws 5x7, scale=2 draws 10x14, etc.
    spacing is pixel gap between characters (before scaling).
    """
    if renderer is None:
        return

    cx = x
    for ch in text:
        glyph = FONT_5X7.get(ch.upper(), FONT_5X7[" "])
        _draw_glyph(renderer, cx, y, glyph, color, scale)
        cx += (5 + spacing) * scale


def _draw_glyph(renderer, x: int, y: int, rows: list[int], color: Color, scale: int) -> None:
    r, g, b = color
    for row_idx, mask in enumerate(rows):
        for col in range(5):
            bit = (mask >> (4 - col)) & 1
            if bit:
                px = x + col * scale
                py = y + row_idx * scale
                for dx in range(scale):
                    for dy in range(scale):
                        renderer.set_pixel(px + dx, py + dy, (r, g, b))


def draw_image_rgb(renderer, x: int, y: int, rgb_pixels, w: int, h: int, key_color: Optional[Color] = None) -> None:
    """
    Draw raw RGB pixels (list/iter of (r,g,b)) into renderer.
    key_color: if given, these pixels will not be drawn (transparent).
    """
    if renderer is None:
        return

    idx = 0
    for j in range(h):
        for i in range(w):
            r, g, b = rgb_pixels[idx]
            idx += 1
            if key_color is not None and (r, g, b) == key_color:
                continue
            renderer.set_pixel(x + i, y + j, (r, g, b))


def measure_text(text: str, scale: int = 1, spacing: int = 1) -> tuple[int, int]:
    if not text:
        return 0, 0
    w = (len(text) * 5 + (len(text) - 1) * spacing) * scale
    h = 7 * scale
    return w, h


def draw_image_rgba(renderer, x: int, y: int, rgba_pixels, w: int, h: int, alpha_threshold: int = 10) -> None:
    """
    Draw RGBA pixels. Pixels with alpha <= threshold are treated as transparent.
    """
    if renderer is None:
        return

    idx = 0
    for j in range(h):
        for i in range(w):
            r, g, b, a = rgba_pixels[idx]
            idx += 1
            if a <= alpha_threshold:
                continue
            renderer.set_pixel(x + i, y + j, (r, g, b))