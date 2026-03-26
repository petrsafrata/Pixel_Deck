from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import requests
from zoneinfo import ZoneInfo

from src.gfx.draw import draw_text, draw_image_rgba, measure_text, hex_to_rgb
from src.gfx.image_loader import load_rgba_pixels
from src.scenes.base_scene import BaseScene

logger = logging.getLogger(__name__)


@dataclass
class NextRace:
    race_name: str
    country: str
    locality: str
    circuit_name: str
    start_dt: datetime
    ts: float

class F1CalendarScene(BaseScene):
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
            "%s entered (provider=%s, refresh_s=%d, tz=%s)",
            self.__class__.__name__,
            self.provider,
            self.refresh_s,
            self.tz,
        )

    def on_exit(self) -> None:
        self._close_clients()
        logger.info("%s exited", self.__class__.__name__)
        super().on_exit()

    def update(self, dt: float) -> None:
        if self.renderer is None:
            return
        self._maybe_fetch()
        if self._race is None:
            return
        self._render()

    # --------------------
    # Internal helpers
    # --------------------
    def _init_state_defaults(self) -> None:
        self.refresh_s: int = 3600

        self.provider: str = "jolpi_ergast"
        self.api_url: str = "https://api.jolpi.ca/ergast/f1/current/next.json"
        self.tz: str = "Europe/Prague"

        self.primary_color: tuple[int, int, int] = (255, 255, 255)
        self.secondary_color: tuple[int, int, int] = (170, 170, 170)

        self.logo_path: str = "assets/images/logo/f1.png"
        self.logo_size: int = 20
        self.logo_center: bool = True
        self.logo_y: int = 2

        self.title_center: bool = True
        self.title_y: int = 28
        self.title_scale: int = 1

        self.time_center: bool = True
        self.time_y: int = 48
        self.time_scale: int = 1

        self._http: Optional[requests.Session] = None

        self._logo_pixels = None
        self._logo_w = 0
        self._logo_h = 0

        self._race: Optional[NextRace] = None
        self._last_fetch: float = 0.0

    def _load_config(self) -> None:
        self.refresh_s = int(self.config.get("refresh_s", 3600))

        font_cfg = self.config.get("font") or {}
        self.primary_color = hex_to_rgb(font_cfg.get("primary_color", "#FFFFFF"))
        self.secondary_color = hex_to_rgb(font_cfg.get("secondary_color", "#AAAAAA"))

        data_cfg = self.config.get("data") or {}
        self.provider = str(data_cfg.get("provider", "jolpi_ergast")).lower()
        self.api_url = str(data_cfg.get("api_url", self.api_url))
        self.tz = str(data_cfg.get("timezone", self.config.get("timezone", "Europe/Prague")))

        layout = self.config.get("layout") or {}

        logo_cfg = layout.get("logo") or {}
        self.logo_path = str(logo_cfg.get("path", self.logo_path))
        self.logo_size = int(logo_cfg.get("size", 20))
        self.logo_center = bool(logo_cfg.get("center", True))
        self.logo_y = int(logo_cfg.get("y", 2))

        title_cfg = layout.get("title") or {}
        self.title_center = bool(title_cfg.get("center", True))
        self.title_y = int(title_cfg.get("y", 28))
        self.title_scale = int(title_cfg.get("scale", 1))

        time_cfg = layout.get("time") or {}
        self.time_center = bool(time_cfg.get("center", True))
        self.time_y = int(time_cfg.get("y", 48))
        self.time_scale = int(time_cfg.get("scale", 1))

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

    def _reset_timers(self) -> None:
        self._race = None
        self._last_fetch = 0.0

    def _maybe_fetch(self) -> None:
        now = time.time()
        if self._race is None or (now - self._last_fetch) >= self.refresh_s:
            race = self._fetch_next_race()
            if race is not None:
                self._race = race
            self._last_fetch = now

    def _fetch_next_race(self) -> Optional[NextRace]:
        if self.provider != "jolpi_ergast":
            logger.warning("%s: unsupported provider '%s'", self.__class__.__name__, self.provider)
            return None
        if self._http is None:
            return None

        try:
            resp = self._http.get(self.api_url, timeout=6)
            resp.raise_for_status()
            data = resp.json()

            races = (((data.get("MRData") or {}).get("RaceTable") or {}).get("Races") or [])
            if not races:
                logger.warning("%s: no next race in API response", self.__class__.__name__)
                return None

            race = races[0]
            race_name = str(race.get("raceName", "Grand Prix"))
            circuit = race.get("Circuit") or {}
            location = circuit.get("Location") or {}

            country = str(location.get("country", "Unknown"))
            locality = str(location.get("locality", "Unknown"))
            circuit_name = str(circuit.get("circuitName", "")).strip() or locality

            date_str = str(race.get("date", ""))
            time_str = str(race.get("time", "00:00:00Z"))
            if not date_str:
                return None

            start_utc = datetime.fromisoformat(f"{date_str}T{time_str.replace('Z', '+00:00')}")
            local_dt = start_utc.astimezone(ZoneInfo(self.tz))

            return NextRace(
                race_name=race_name,
                country=country,
                locality=locality,
                circuit_name=circuit_name,
                start_dt=local_dt,
                ts=time.time(),
            )
        except Exception as e:
            logger.warning("%s: F1 API fetch failed: %s", self.__class__.__name__, e, exc_info=True)
            return None

    def _render(self) -> None:
        assert self.renderer is not None
        assert self._race is not None

        if self._logo_pixels is not None:
            x_logo = max(0, (self.renderer.width - self._logo_w) // 2) if self.logo_center else 0
            draw_image_rgba(self.renderer, x_logo, self.logo_y, self._logo_pixels, self._logo_w, self._logo_h)
        else:
            # fallback
            self._draw_centered("F1", y=self.logo_y + 4, scale=2, color=self.primary_color)

        # Output
        line1 = self._format_gp_title(self._race.country)  # "GP Japan"
        line2 = self._format_circuit(self._race.circuit_name)  # "Suzuka"
        line3 = self._race.start_dt.strftime("%d.%m %H:%M") # Time

        self._draw_centered(line1, y=self.title_y, scale=self.title_scale, color=self.primary_color)
        self._draw_centered(line2, y=self.title_y + 10, scale=1, color=self.secondary_color)
        self._draw_centered(line3, y=self.time_y, scale=self.time_scale, color=self.secondary_color, spacing=0)

    def _format_gp_title(self, country: str) -> str:
        c = country.strip()
        if len(c) > 12:
            c = c[:12]
        return f"GP {c}"

    def _format_circuit(self, circuit_name: str) -> str:
        name = circuit_name.strip()
        name = name.split(" ", 1)[0]
        if len(name) > 14:
            name = name[:14]
        return name

    def _draw_centered(
            self,
            text: str,
            y: int,
            scale: int,
            color: tuple[int, int, int],
            spacing: int = 1,
    ) -> None:
        assert self.renderer is not None

        s = max(1, int(scale))
        while s > 1:
            w, _ = measure_text(text, scale=s, spacing=spacing)
            if w <= self.renderer.width:
                break
            s -= 1

        w, h = measure_text(text, scale=s, spacing=spacing)
        x = max(0, (self.renderer.width - w) // 2)
        if y + h > self.renderer.height:
            y = max(0, self.renderer.height - h)

        draw_text(self.renderer, x, y, text, color, scale=s, spacing=spacing)
