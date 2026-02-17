from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional, Tuple
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from src.scenes.base_scene import BaseScene
from src.gfx.draw import draw_text, measure_text, hex_to_rgb, draw_image_rgba
from src.gfx.image_loader import load_rgba_pixels

logger = logging.getLogger(__name__)


class CalendarScene(BaseScene):
    """
    Standardized scene structure:
      - on_enter(): init defaults -> load config -> load assets -> finalize
      - on_exit(): cleanup
      - update(): render only
    """

    def on_enter(self) -> None:
        super().on_enter()
        self._init_state_defaults()
        self._load_config()
        self._load_assets()
        logger.info(
            "%s entered (timezone=%s, logo=%s)",
            self.__class__.__name__,
            self.tz_key,
            self.logo_path,
        )

    def on_exit(self) -> None:
        logger.info("%s exited", self.__class__.__name__)
        super().on_exit()

    def update(self, dt: float) -> None:
        if self.renderer is None:
            return

        now = datetime.now(self.tz)
        day_month = now.strftime("%d.%m")
        year = now.strftime("%Y")

        self._render_logo()
        self._render_date(day_month)
        self._render_year(year)

    # --------------------
    # Internal helpers
    # --------------------
    def _init_state_defaults(self) -> None:
        # timezone
        self.tz_key: str = "Europe/Prague"
        self.tz = timezone.utc

        # colors
        self.primary_color: Tuple[int, int, int] = (255, 255, 255)
        self.secondary_color: Tuple[int, int, int] = (170, 170, 170)

        # layout (logo)
        self.logo_path: str = "assets/images/logo/calendar.png"
        self.logo_size: int = 28
        self.logo_center: bool = False
        self.logo_y: int = 4

        # layout (date)
        self.date_center: bool = False
        self.date_y: int = 38
        self.date_scale: int = 2

        # layout (year)
        self.year_center: bool = False
        self.year_y: int = 52
        self.year_scale: int = 1

        # assets
        self._logo_pixels = None
        self._logo_w = 0
        self._logo_h = 0

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

        font_cfg = (self.config.get("font") or {})
        self.primary_color = hex_to_rgb(font_cfg.get("primary_color", "#FFFFFF"))
        self.secondary_color = hex_to_rgb(font_cfg.get("secondary_color", "#AAAAAA"))

        layout = self.config.get("layout", {}) or {}

        logo_cfg = (layout.get("logo") or {})
        self.logo_path = str(logo_cfg.get("path", "assets/images/logo/calendar.png"))
        self.logo_size = int(logo_cfg.get("size", 28))
        self.logo_center = bool(logo_cfg.get("center", False))
        self.logo_y = int(logo_cfg.get("y", 4))

        date_cfg = (layout.get("date") or {})
        self.date_center = bool(date_cfg.get("center", False))
        self.date_y = int(date_cfg.get("y", 38))
        self.date_scale = int(date_cfg.get("scale", 2))

        year_cfg = (layout.get("year") or {})
        self.year_center = bool(year_cfg.get("center", False))
        self.year_y = int(year_cfg.get("y", 52))
        self.year_scale = int(year_cfg.get("scale", 1))

    def _load_assets(self) -> None:
        self._logo_pixels, self._logo_w, self._logo_h = None, 0, 0
        try:
            self._logo_pixels, self._logo_w, self._logo_h = load_rgba_pixels(self.logo_path, self.logo_size)
        except Exception as e:
            logger.warning(
                "%s: logo load error (%s): %s",
                self.__class__.__name__,
                self.logo_path,
                e,
                exc_info=True,
            )

    def _render_logo(self) -> None:
        if self.renderer is None or self._logo_pixels is None:
            return
        x_logo = max(0, (self.renderer.width - self._logo_w) // 2) if self.logo_center else 0
        draw_image_rgba(self.renderer, x_logo, self.logo_y, self._logo_pixels, self._logo_w, self._logo_h)

    def _render_date(self, day_month: str) -> None:
        if self.renderer is None:
            return
        w, h = measure_text(day_month, scale=self.date_scale, spacing=1)
        x = max(0, (self.renderer.width - w) // 2) if self.date_center else 0
        y = self.date_y
        if y + h > self.renderer.height:
            y = max(0, self.renderer.height - h)
        draw_text(self.renderer, x, y, day_month, self.primary_color, scale=self.date_scale, spacing=1)

    def _render_year(self, year: str) -> None:
        if self.renderer is None:
            return
        w, h = measure_text(year, scale=self.year_scale, spacing=1)
        x = max(0, (self.renderer.width - w) // 2) if self.year_center else 0
        y = self.year_y
        if y + h > self.renderer.height:
            y = max(0, self.renderer.height - h)
        draw_text(self.renderer, x, y, year, self.secondary_color, scale=self.year_scale, spacing=1)
