from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

import requests
from zoneinfo import ZoneInfo

from src.gfx.draw import draw_image_rgba, draw_text, hex_to_rgb, measure_text
from src.gfx.image_loader import load_rgba_pixels
from src.scenes.base_scene import BaseScene

logger = logging.getLogger(__name__)


@dataclass
class SolarEvent:
    kind: str  # "sunrise" | "sunset"
    when: datetime


class DayStateScene(BaseScene):
    """
    Standardized scene structure:
      - on_enter(): init defaults -> load config -> init clients -> load assets -> reset timers
      - on_exit(): cleanup (close session)
      - update(): fetch (if needed) -> render
    """

    def on_enter(self) -> None:
        super().on_enter()
        self._init_state_defaults()
        self._load_config()
        self._init_clients()
        self._load_assets()
        self._reset_timers()
        logger.info(
            "%s entered (provider=%s, lat=%.4f, lon=%.4f, tz=%s, refresh_s=%d)",
            self.__class__.__name__,
            self.provider,
            self.lat,
            self.lon,
            self.tz,
            self.refresh_s,
        )

    def on_exit(self) -> None:
        self._close_clients()
        logger.info("%s exited", self.__class__.__name__)
        super().on_exit()

    def update(self, dt: float) -> None:
        if self.renderer is None:
            return

        self._maybe_fetch()
        self._render()

    # --------------------
    # Internal helpers
    # --------------------
    def _init_state_defaults(self) -> None:
        self.refresh_s: int = 3600

        self.primary_color: tuple[int, int, int] = (255, 255, 255)
        self.secondary_color: tuple[int, int, int] = (170, 170, 170)

        self.provider: str = "open_meteo"
        self.lat: float = 50.0755
        self.lon: float = 14.4378
        self.tz: str = "Europe/Prague"

        self.icon_size: int = 32
        self.icon_center: bool = True
        self.icon_y: int = 2
        self.icon_paths: dict[str, str] = {
            "sun": "assets/images/weather/sun.png",
            "night": "assets/images/weather/moon.png",
        }

        self.label_center: bool = True
        self.label_y: int = 40
        self.label_scale: int = 1

        self.time_center: bool = True
        self.time_y: int = 50
        self.time_scale: int = 2

        self._http: Optional[requests.Session] = None
        self._last_fetch: float = 0.0

        self._sunrise_times: list[datetime] = []
        self._sunset_times: list[datetime] = []

        self._icon_cache: dict[str, tuple[list[tuple[int, int, int, int]], int, int]] = {}

    def _load_config(self) -> None:
        self.refresh_s = int(self.config.get("refresh_s", 3600))

        font_cfg = self.config.get("font") or {}
        self.primary_color = hex_to_rgb(font_cfg.get("primary_color", "#FFFFFF"))
        self.secondary_color = hex_to_rgb(font_cfg.get("secondary_color", "#AAAAAA"))

        data_cfg = self.config.get("data") or {}
        self.provider = str(data_cfg.get("provider", "open_meteo")).lower()
        self.lat = float(data_cfg.get("latitude", 50.0755))
        self.lon = float(data_cfg.get("longitude", 14.4378))
        self.tz = str(data_cfg.get("timezone", self.config.get("timezone", "Europe/Prague")))

        layout_cfg = self.config.get("layout") or {}
        icon_cfg = layout_cfg.get("icon") or {}
        self.icon_size = int(icon_cfg.get("size", 32))
        self.icon_center = bool(icon_cfg.get("center", True))
        self.icon_y = int(icon_cfg.get("y", 2))

        icons_cfg = icon_cfg.get("icons") or {}
        self.icon_paths = {
            "sun": str(icons_cfg.get("sun", self.icon_paths["sun"])),
            # fallback na moon kvuli zpetne kompatibilite
            "night": str(icons_cfg.get("night", icons_cfg.get("moon", self.icon_paths["night"]))),
        }

        # text je v configu na rootu scenes.day_state.text (ne v layout.text)
        text_cfg = self.config.get("text") or {}
        self.label_center = bool(text_cfg.get("center", True))
        self.label_y = int(text_cfg.get("label_y", 40))
        self.label_scale = int(text_cfg.get("label_scale", 1))
        self.time_center = bool(text_cfg.get("center", True))
        self.time_y = int(text_cfg.get("time_y", 50))
        self.time_scale = int(text_cfg.get("time_scale", 1))

    def _init_clients(self) -> None:
        self._http = requests.Session()

    def _close_clients(self) -> None:
        if self._http is not None:
            try:
                self._http.close()
            except Exception:
                logger.debug("%s: failed to close http session", self.__class__.__name__, exc_info=True)
            finally:
                self._http = None

    def _load_assets(self) -> None:
        self._icon_cache = {}

    def _reset_timers(self) -> None:
        self._last_fetch = 0.0
        self._sunrise_times = []
        self._sunset_times = []

    def _maybe_fetch(self) -> None:
        now = time.time()
        if (not self._sunrise_times) or (not self._sunset_times) or ((now - self._last_fetch) >= self.refresh_s):
            sr, ss = self._fetch_open_meteo()
            if sr and ss:
                self._sunrise_times = sr
                self._sunset_times = ss
            self._last_fetch = now

    def _fetch_open_meteo(self) -> tuple[list[datetime], list[datetime]]:
        if self.provider != "open_meteo" or self._http is None:
            if self.provider != "open_meteo":
                logger.warning("%s: unsupported provider '%s'", self.__class__.__name__, self.provider)
            return [], []

        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": self.lat,
            "longitude": self.lon,
            "daily": "sunrise,sunset",
            "timezone": self.tz,
            "forecast_days": 2,
        }

        try:
            r = self._http.get(url, params=params, timeout=6)
            r.raise_for_status()
            js = r.json()

            daily = js.get("daily") or {}
            sunrise_raw = daily.get("sunrise") or []
            sunset_raw = daily.get("sunset") or []

            sunrises = [self._parse_dt(v) for v in sunrise_raw if isinstance(v, str)]
            sunsets = [self._parse_dt(v) for v in sunset_raw if isinstance(v, str)]

            return sunrises, sunsets
        except Exception as e:
            logger.warning("%s: fetch failed: %s", self.__class__.__name__, e, exc_info=True)
            return [], []

    def _parse_dt(self, value: str) -> datetime:
        dt = datetime.fromisoformat(value)
        zone = ZoneInfo(self.tz)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=zone)
        return dt.astimezone(zone)

    def _render(self) -> None:
        if self.renderer is None:
            return

        event = self._get_next_event()
        if event is None:
            return

        now = datetime.now(ZoneInfo(self.tz))
        remaining = max(timedelta(0), event.when - now)

        if event.kind == "sunrise":
            icon_key = "night"
            label = "Vychod v"
        else:
            icon_key = "sun"
            label = "Zapad v"

        event_time = self._format_event_time(event.when)

        self._draw_icon(icon_key)
        self._draw_centered_text(label, self.label_y, self.label_scale, self.primary_color, self.label_center)
        self._draw_centered_text(
            event_time,
            self.time_y,
            self.time_scale,
            self.secondary_color,
            self.time_center,
        )

    def _get_next_event(self) -> Optional[SolarEvent]:
        now = datetime.now(ZoneInfo(self.tz))
        events: list[SolarEvent] = []

        for dt in self._sunrise_times:
            if dt > now:
                events.append(SolarEvent(kind="sunrise", when=dt))
        for dt in self._sunset_times:
            if dt > now:
                events.append(SolarEvent(kind="sunset", when=dt))

        if not events:
            return None

        events.sort(key=lambda e: e.when)
        return events[0]

    def _format_event_time(self, dt: datetime) -> str:
        return dt.strftime("%H:%M")

    def _draw_centered_text(
        self,
        text: str,
        y: int,
        scale: int,
        color: tuple[int, int, int],
        center: bool,
    ) -> None:
        if self.renderer is None:
            return

        w, h = measure_text(text, scale=scale, spacing=1)
        x = max(0, (self.renderer.width - w) // 2) if center else 0
        if y + h > self.renderer.height:
            y = max(0, self.renderer.height - h)

        draw_text(self.renderer, x, y, text, color, scale=scale, spacing=1)

    def _draw_icon(self, key: str) -> None:
        if self.renderer is None:
            return

        path = self.icon_paths.get(key)
        if not path:
            logger.debug("%s: missing icon key '%s' in icon_paths", self.__class__.__name__, key)
            return

        if key not in self._icon_cache:
            try:
                pixels, w, h = load_rgba_pixels(path, self.icon_size)
                self._icon_cache[key] = (pixels, w, h)
            except Exception as e:
                logger.warning("%s: icon load failed (%s): %s", self.__class__.__name__, path, e, exc_info=True)
                return

        pixels, w, h = self._icon_cache[key]
        x = max(0, (self.renderer.width - w) // 2) if self.icon_center else 0
        draw_image_rgba(self.renderer, x, self.icon_y, pixels, w, h)