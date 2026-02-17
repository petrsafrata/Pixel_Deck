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
class IndexQuote:
    price: float
    prev_price: float
    change: float
    change_pct: float
    ts: float


class SP500Scene(BaseScene):
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
            "%s entered (provider=%s, symbol=%s, refresh_s=%s, logo=%s)",
            self.__class__.__name__,
            self.provider,
            self.symbol,
            self.refresh_s,
            self.logo_path,
        )

    def on_exit(self) -> None:
        self._close_clients()
        logger.info("%s exited", self.__class__.__name__)
        super().on_exit()

    def update(self, dt: float) -> None:
        if self.renderer is None:
            return

        self._maybe_fetch()
        if self.quote is None:
            return

        self._render()

    # --------------------
    # Internal helpers
    # --------------------
    def _init_state_defaults(self) -> None:
        self.refresh_s: int = 300

        # colors
        self.primary_color: Tuple[int, int, int] = (255, 255, 255)
        self.secondary_color: Tuple[int, int, int] = (170, 170, 170)

        # data
        self.provider: str = "stooq"
        self.symbol: str = "^spx"

        # layout
        self.logo_path: str = "assets/images/logo/sp500.png"
        self.logo_size: int = 28
        self.logo_center: bool = True
        self.logo_y: int = 4

        self.price_center: bool = True
        self.price_y: int = 34
        self.price_scale: int = 2

        self.change_center: bool = True
        self.change_y: int = 54
        self.change_scale: int = 1

        # http
        self._http: Optional[requests.Session] = None

        # assets
        self._logo_pixels = None
        self._logo_w = 0
        self._logo_h = 0

        # quote cache
        self.quote: Optional[IndexQuote] = None
        self._last_fetch: float = 0.0

    def _load_config(self) -> None:
        self.refresh_s = int(self.config.get("refresh_s", 300))

        font_cfg = (self.config.get("font") or {})
        self.primary_color = hex_to_rgb(font_cfg.get("primary_color", "#FFFFFF"))
        self.secondary_color = hex_to_rgb(font_cfg.get("secondary_color", "#AAAAAA"))

        data_cfg = (self.config.get("data") or {})
        self.provider = str(data_cfg.get("provider", "stooq")).lower()
        self.symbol = str(data_cfg.get("symbol", "^spx"))

        layout = (self.config.get("layout") or {})

        logo_cfg = (layout.get("logo") or {})
        self.logo_path = str(logo_cfg.get("path", "assets/images/logo/sp500.png"))
        self.logo_size = int(logo_cfg.get("size", 28))
        self.logo_center = bool(logo_cfg.get("center", True))
        self.logo_y = int(logo_cfg.get("y", 4))

        price_cfg = (layout.get("price") or {})
        self.price_center = bool(price_cfg.get("center", True))
        self.price_y = int(price_cfg.get("y", 34))
        self.price_scale = int(price_cfg.get("scale", 2))

        ch_cfg = (layout.get("change") or {})
        self.change_center = bool(ch_cfg.get("center", True))
        self.change_y = int(ch_cfg.get("y", 54))
        self.change_scale = int(ch_cfg.get("scale", 1))

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
        self._last_fetch = 0.0
        self.quote = None

    def _maybe_fetch(self) -> None:
        now = time.time()
        if self.quote is None or (now - self._last_fetch) >= self.refresh_s:
            q = self._fetch_quote()
            if q is not None:
                self.quote = q
            self._last_fetch = now

    def _render(self) -> None:
        assert self.renderer is not None
        assert self.quote is not None

        # --- LOGO ---
        if self._logo_pixels is not None:
            x_logo = max(0, (self.renderer.width - self._logo_w) // 2) if self.logo_center else 0
            draw_image_rgba(self.renderer, x_logo, self.logo_y, self._logo_pixels, self._logo_w, self._logo_h)

        # --- PRICE ---
        price_text = f"${int(round(self.quote.price))}"
        self._draw_text(price_text, y=self.price_y, scale=self.price_scale, color=self.primary_color, center=self.price_center)

        # --- CHANGE ---
        change_text = f"{self.quote.change_pct:+.2f}%"
        change_color = self._color_for_change(self.quote.change_pct)
        self._draw_text(change_text, y=self.change_y, scale=self.change_scale, color=change_color, center=self.change_center)

    def _draw_text(self, text: str, y: int, scale: int, color, center: bool) -> None:
        assert self.renderer is not None

        w, h = measure_text(text, scale=scale, spacing=1)
        x = max(0, (self.renderer.width - w) // 2) if center else 0
        if y + h > self.renderer.height:
            y = max(0, self.renderer.height - h)
        draw_text(self.renderer, x, y, text, color, scale=scale, spacing=1)

    def _color_for_change(self, change_pct: float):
        if change_pct > 0:
            return hex_to_rgb("#00FF88")
        if change_pct < 0:
            return hex_to_rgb("#FF4444")
        return self.secondary_color

    def _fetch_quote(self) -> Optional[IndexQuote]:
        if self.provider == "stooq":
            return self._fetch_stooq()
        logger.warning("%s: unsupported provider '%s'", self.__class__.__name__, self.provider)
        return None

    def _fetch_stooq(self) -> Optional[IndexQuote]:
        if self._http is None:
            return None

        url = "https://stooq.com/q/d/l/"
        params = {"s": self.symbol, "i": "d"}

        try:
            r = self._http.get(url, params=params, timeout=6, stream=True)
            r.raise_for_status()

            lines = []
            for raw in r.iter_lines(decode_unicode=True):
                if raw:
                    lines.append(raw)
                if len(lines) >= 3:  # header + 2 rows
                    break

            if len(lines) < 3:
                logger.warning("%s: stooq returned too few lines for %s", self.__class__.__name__, self.symbol)
                return None

            header = lines[0].split(",")
            row1 = lines[1].split(",")
            row2 = lines[2].split(",")

            try:
                close_idx = header.index("Close")
            except ValueError:
                close_idx = 4

            price = float(row1[close_idx])
            prev = float(row2[close_idx])

            change = price - prev
            change_pct = (change / prev) * 100.0 if prev != 0 else 0.0

            return IndexQuote(price=price, prev_price=prev, change=change, change_pct=change_pct, ts=time.time())

        except Exception as e:
            logger.warning("%s: stooq fetch failed (%s): %s", self.__class__.__name__, self.symbol, e, exc_info=True)
            return None
