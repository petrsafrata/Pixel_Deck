from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Tuple
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from src.scenes.base_scene import BaseScene
from src.gfx.draw import draw_text, measure_text, hex_to_rgb

logger = logging.getLogger(__name__)


class ClockScene(BaseScene):
    """
    Standardized scene structure:
      - on_enter(): init defaults -> load config -> finalize
      - on_exit(): cleanup
      - update(): render only
    """

    def on_enter(self) -> None:
        super().on_enter()
        self._init_state_defaults()
        self._load_config()
        logger.info(
            "%s entered (timezone=%s, format=%s, scale=%s)",
            self.__class__.__name__,
            self.tz_key,
            self.time_format,
            self.time_scale,
        )

    def on_exit(self) -> None:
        logger.info("%s exited", self.__class__.__name__)
        super().on_exit()

    def update(self, dt: float) -> None:
        if self.renderer is None:
            return

        now = datetime.now(self.tz)
        text = now.strftime(self.time_format)

        w, h = measure_text(text, scale=self.time_scale, spacing=self.time_spacing)

        # Always centered horizontally
        x = max(0, (self.renderer.width - w) // 2)

        y = self.time_y
        if y + h > self.renderer.height:
            y = max(0, self.renderer.height - h)

        draw_text(
            self.renderer,
            x,
            y,
            text,
            self.font_color,
            scale=self.time_scale,
            spacing=self.time_spacing,
        )

    # --------------------
    # Internal helpers
    # --------------------
    def _init_state_defaults(self) -> None:
        # timezone
        self.tz_key: str = "Europe/Prague"
        self.tz = timezone.utc

        # time format
        self.time_format: str = "%H:%M:%S"
        self.show_date: bool = False  # currently unused, preserved

        # background (currently unused, preserved)
        self.bg: Tuple[int, int, int] = (0, 0, 0)

        # colors
        self.font_color: Tuple[int, int, int] = (255, 255, 255)

        # layout/time
        self.time_x: int = 2  # kept, but render centers horizontally
        self.time_y: int = 22
        self.time_scale: int = 2
        self.time_spacing: int = 1

    def _load_config(self) -> None:
        self.tz_key = str(self.config.get("timezone", "Europe/Prague"))
        try:
            self.tz = ZoneInfo(self.tz_key)
        except ZoneInfoNotFoundError:
            self.tz = datetime.now().astimezone().tzinfo or timezone.utc
            logger.warning(
                "%s: timezone '%s' not found. Falling back to local/UTC.",
                self.__class__.__name__,
                self.tz_key,
            )
        except Exception as e:
            self.tz = datetime.now().astimezone().tzinfo or timezone.utc
            logger.warning(
                "%s: timezone init failed for '%s': %s. Falling back to local/UTC.",
                self.__class__.__name__,
                self.tz_key,
                e,
                exc_info=True,
            )

        self.time_format = str(self.config.get("format", "%H:%M:%S"))
        self.show_date = bool(self.config.get("show_date", False))

        self.bg = hex_to_rgb(self.config.get("background", "#000000"))

        font_cfg = self.config.get("font", {}) or {}
        self.font_color = hex_to_rgb(font_cfg.get("primary_color", "#FFFFFF"))

        layout = self.config.get("layout", {}) or {}
        time_cfg = (layout.get("time") or {})
        self.time_x = int(time_cfg.get("x", 2))
        self.time_y = int(time_cfg.get("y", 22))
        self.time_scale = int(time_cfg.get("scale", 2))
        self.time_spacing = int(time_cfg.get("spacing", 1))
