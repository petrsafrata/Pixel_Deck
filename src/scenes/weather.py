from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Optional, Tuple

import requests

from src.scenes.base_scene import BaseScene
from src.gfx.draw import draw_text, measure_text, hex_to_rgb, draw_image_rgba
from src.gfx.image_loader import load_rgba_pixels

logger = logging.getLogger(__name__)


@dataclass
class WeatherData:
    temp_c: float
    tmin_c: float
    tmax_c: float
    weather_code: int
    ts: float


class WeatherScene(BaseScene):
    """
    Standardized scene structure:
      - on_enter(): init defaults -> load config -> init clients -> load assets (icon cache lazy) -> reset timers
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
        if self._data is None:
            return

        self._render()

    # --------------------
    # Internal helpers
    # --------------------
    def _init_state_defaults(self) -> None:
        # refresh
        self.refresh_s: int = 600

        # colors
        self.primary_color: Tuple[int, int, int] = (255, 255, 255)
        self.secondary_color: Tuple[int, int, int] = (170, 170, 170)

        # data config
        self.provider: str = "open_meteo"
        self.lat: float = 50.0755
        self.lon: float = 14.4378
        self.tz: str = "Europe/Prague"

        # layout icon
        self.icon_size: int = 28
        self.icon_center: bool = True
        self.icon_y: int = 4
        self.icon_paths: dict = {}

        # layout temp
        self.temp_center: bool = True
        self.temp_y: int = 34
        self.temp_scale: int = 2

        # layout min/max
        self.mm_center: bool = True
        self.mm_y: int = 54
        self.mm_scale: int = 1

        # http
        self._http: Optional[requests.Session] = None

        # cache
        self._last_fetch: float = 0.0
        self._data: Optional[WeatherData] = None

        # icon cache per key
        self._icon_cache: dict[str, tuple[list[tuple[int, int, int, int]], int, int]] = {}

    def _load_config(self) -> None:
        self.refresh_s = int(self.config.get("refresh_s", 600))

        font_cfg = (self.config.get("font") or {})
        self.primary_color = hex_to_rgb(font_cfg.get("primary_color", "#FFFFFF"))
        self.secondary_color = hex_to_rgb(font_cfg.get("secondary_color", "#AAAAAA"))

        data_cfg = (self.config.get("data") or {})
        self.provider = str(data_cfg.get("provider", "open_meteo")).lower()
        self.lat = float(data_cfg.get("latitude", 50.0755))
        self.lon = float(data_cfg.get("longitude", 14.4378))
        self.tz = str(data_cfg.get("timezone", self.config.get("timezone", "Europe/Prague")))

        layout = (self.config.get("layout") or {})

        icon_cfg = (layout.get("icon") or {})
        self.icon_size = int(icon_cfg.get("size", 28))
        self.icon_center = bool(icon_cfg.get("center", True))
        self.icon_y = int(icon_cfg.get("y", 4))
        self.icon_paths = (icon_cfg.get("icons") or {})  # expected keys: sun/half_sun/cloud/rain/snow/thunderstorm

        temp_cfg = (layout.get("temp") or {})
        self.temp_center = bool(temp_cfg.get("center", True))
        self.temp_y = int(temp_cfg.get("y", 34))
        self.temp_scale = int(temp_cfg.get("scale", 2))

        mm_cfg = (layout.get("minmax") or {})
        self.mm_center = bool(mm_cfg.get("center", True))
        self.mm_y = int(mm_cfg.get("y", 54))
        self.mm_scale = int(mm_cfg.get("scale", 1))

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
        # icons are lazy-loaded by key, but we ensure cache dict exists
        if not isinstance(self._icon_cache, dict):
            self._icon_cache = {}

    def _reset_timers(self) -> None:
        self._last_fetch = 0.0
        self._data = None

    def _maybe_fetch(self) -> None:
        now = time.time()
        if self._data is None or (now - self._last_fetch) >= self.refresh_s:
            new_data = self._fetch_open_meteo()
            if new_data is not None:
                self._data = new_data
            self._last_fetch = now

    def _render(self) -> None:
        assert self.renderer is not None
        assert self._data is not None

        icon_key = self._map_weather_code_to_icon(self._data.weather_code)
        self._draw_icon(icon_key)

        temp_text = f"{int(round(self._data.temp_c))}°C"
        self._draw_centered_text(temp_text, y=self.temp_y, scale=self.temp_scale, color=self.primary_color,
                                 center=self.temp_center)

        tmin = int(round(self._data.tmin_c))
        tmax = int(round(self._data.tmax_c))
        mm_text = f"{tmin}°    {tmax}°"
        self._draw_centered_text(mm_text, y=self.mm_y, scale=self.mm_scale, color=self.secondary_color,
                                 center=self.mm_center)

    def _draw_centered_text(self, text: str, y: int, scale: int, color, center: bool) -> None:
        assert self.renderer is not None
        w, h = measure_text(text, scale=scale, spacing=1)
        x = max(0, (self.renderer.width - w) // 2) if center else 0
        if y + h > self.renderer.height:
            y = max(0, self.renderer.height - h)
        draw_text(self.renderer, x, y, text, color, scale=scale, spacing=1)

    def _draw_icon(self, key: str) -> None:
        assert self.renderer is not None

        path = (self.icon_paths or {}).get(key)
        if not path:
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

    def _map_weather_code_to_icon(self, code: int) -> str:
        """
        Open-Meteo:
            0 = clear sky
            1,2 = mainly clear / partly cloudy
            3 = overcast
            45,48 = fog
            51-67,80-82 = drizzle/rain
            71-77,85-86 = snow
            95-99 = thunderstorm
        """
        if code == 0:
            return "sun"
        if code in (1, 2):
            return "half_sun"
        if code in (3, 45, 48):
            return "cloud"
        if 71 <= code <= 77 or 85 <= code <= 86:
            return "snow"
        if 95 <= code <= 99:
            return "thunderstorm"
        if 51 <= code <= 67 or 80 <= code <= 82:
            return "rain"
        return "cloud"

    def _fetch_open_meteo(self) -> Optional[WeatherData]:
        if self.provider != "open_meteo" or self._http is None:
            if self.provider != "open_meteo":
                logger.warning("%s: unsupported provider '%s'", self.__class__.__name__, self.provider)
            return None

        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": self.lat,
            "longitude": self.lon,
            "current": "temperature_2m,weather_code",
            "daily": "temperature_2m_max,temperature_2m_min",
            "timezone": self.tz,
        }

        try:
            r = self._http.get(url, params=params, timeout=6)
            r.raise_for_status()
            js = r.json()

            cur = js.get("current") or {}
            daily = js.get("daily") or {}

            temp = float(cur["temperature_2m"])
            code = int(cur["weather_code"])

            tmax = float((daily.get("temperature_2m_max") or [None])[0])
            tmin = float((daily.get("temperature_2m_min") or [None])[0])

            return WeatherData(
                temp_c=temp,
                tmin_c=tmin,
                tmax_c=tmax,
                weather_code=code,
                ts=time.time(),
            )

        except Exception as e:
            logger.warning("%s: weather fetch failed: %s", self.__class__.__name__, e, exc_info=True)
            return None
