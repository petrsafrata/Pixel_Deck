from __future__ import annotations

import logging
from typing import Optional

from src.gfx.draw import draw_image_rgba
from src.gfx.image_loader import load_rgba_pixels
from src.scenes.base_scene import BaseScene

logger = logging.getLogger(__name__)


class ShowAppLogo(BaseScene):
    """
    Startup scene shown once during app launch.
        - on_enter(): reset internal timer and load logo asset
        - update(): render centered logo and animated loading bar
        - on_exit(): final cleanup/logging
    """

    # Default config
    LOGO_PATH = "assets/images/app/pixel-deck-logo-small.png"
    LOGO_SIZE = 64
    LOGO_Y = -5

    BAR_MARGIN_X = 2
    BAR_HEIGHT = 2
    BAR_Y = 56
    BAR_BG = (30, 30, 30)
    BAR_FG = (52, 194, 66)

    def on_enter(self) -> None:
        super().on_enter()
        self._elapsed_s = 0.0
        self._img: Optional[list[tuple[int, int, int, int]]] = None
        self._w = 0
        self._h = 0

        try:
            self._img, self._w, self._h = load_rgba_pixels(self.LOGO_PATH, self.LOGO_SIZE)
        except Exception as e:
            logger.warning(
                "%s: failed to load logo '%s': %s",
                self.__class__.__name__,
                self.LOGO_PATH,
                e,
                exc_info=True,
            )

        logger.info("%s entered", self.__class__.__name__)

    def on_exit(self) -> None:
        logger.info("%s exited", self.__class__.__name__)
        super().on_exit()

    def update(self, dt: float) -> None:
        if self.renderer is None:
            return

        self._elapsed_s += max(0.0, dt)
        progress = min(1.0, self._elapsed_s / 5.0)

        if self._img is not None:
            x = max(0, (self.renderer.width - self._w) // 2)
            draw_image_rgba(self.renderer, x, self.LOGO_Y, self._img, self._w, self._h)

        self._draw_loading_bar(progress)

    # --------------------
    # Internal helpers
    # --------------------
    def _draw_loading_bar(self, progress: float) -> None:
        if self.renderer is None:
            return

        def clamp(v: float, lo: float, hi: float) -> float:
            return max(lo, min(hi, v))

        def lerp(a: int, b: int, t: float) -> int:
            return int(a + (b - a) * t)

        def lerp_color(c1: tuple[int, int, int], c2: tuple[int, int, int], t: float) -> tuple[int, int, int]:
            return (
                lerp(c1[0], c2[0], t),
                lerp(c1[1], c2[1], t),
                lerp(c1[2], c2[2], t),
            )

        def draw_rounded_rect(x: int, y: int, w: int, h: int, color: tuple[int, int, int]) -> None:
            # Simple rounded corners for tiny LED canvas (pill look).
            if w <= 0 or h <= 0:
                return
            for py in range(y, y + h):
                for px in range(x, x + w):
                    rx = min(px - x, (x + w - 1) - px)
                    ry = min(py - y, (y + h - 1) - py)
                    # Keep corner pixels trimmed for rounded effect
                    if h >= 4 and rx == 0 and ry == 0:
                        continue
                    self.renderer.set_pixel(px, py, color)

        p = clamp(progress, 0.0, 1.0)

        # Geometry tuned for 64x64
        x0 = max(1, self.BAR_MARGIN_X)
        y0 = self.BAR_Y
        w = max(8, self.renderer.width - 2 * x0)
        h = max(3, self.BAR_HEIGHT + 1)

        # Shadow under track
        shadow = (8, 8, 8)
        if y0 + h < self.renderer.height:
            draw_rounded_rect(x0, y0 + 1, w, h, shadow)

        # Track
        track = (24, 24, 28)
        draw_rounded_rect(x0, y0, w, h, track)

        # Inner padding for fill
        ix = x0 + 1
        iy = y0 + 1
        iw = max(1, w - 2)
        ih = max(1, h - 2)

        fill_w = int(iw * p)
        if fill_w > 0:
            # Gradient fill (green -> cyan for "modern" look)
            c_start = (52, 194, 66)
            c_end = (64, 180, 255)

            for py in range(iy, iy + ih):
                for px in range(ix, ix + fill_w):
                    t = (px - ix) / max(1, fill_w - 1)
                    self.renderer.set_pixel(px, py, lerp_color(c_start, c_end, t))

            # Moving shine highlight (subtle animated light)
            shine_x = ix + int((fill_w - 1) * ((self._elapsed_s * 2.2) % 1.0))
            shine = (220, 240, 255)
            for py in range(iy, iy + ih):
                if ix <= shine_x < ix + fill_w:
                    self.renderer.set_pixel(shine_x, py, shine)
