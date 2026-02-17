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
class BitcoinQuote:
    price: float
    currency: str
    change_24h_percent: Optional[float] = None
    ts: float = 0.0


class BitcoinScene(BaseScene):
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
            "%s entered (coin_id=%s, currency=%s, refresh_s=%s, logo=%s)",
            self.__class__.__name__,
            self.coin_id,
            self.currency,
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
        # data
        self.coin_id: str = "bitcoin"
        self.currency: str = "czk"
        self.currency_label: str = "CZK"
        self.refresh_s: int = 30

        # http
        self._http: Optional[requests.Session] = None

        # colors
        self.primary_color: Tuple[int, int, int] = (255, 255, 255)
        self.secondary_color: Tuple[int, int, int] = (247, 147, 26)

        # layout (logo)
        self.logo_path: str = "assets/images/logo/btc.png"
        self.logo_size: int = 32
        self.logo_center: bool = False
        self.logo_x: int = 0
        self.logo_y: int = 4

        # layout (text)
        self.text_center: bool = False
        self.text_x: int = 0
        self.text_y: int = 42
        self.text_scale_pref: int = 1
        self.text_spacing: int = 1
        self.show_change: bool = True
        self.change_on_new_line: bool = True

        # assets
        self._logo_pixels = None
        self._logo_w = 0
        self._logo_h = 0

        # data cache
        self.quote: Optional[BitcoinQuote] = None
        self._last_fetch: float = 0.0

    def _load_config(self) -> None:
        data_cfg = self.config.get("data", {}) or {}
        self.coin_id = str(data_cfg.get("coin_id", "bitcoin"))
        self.currency = str(data_cfg.get("currency", "czk")).lower()
        self.currency_label = self.currency.upper()

        self.refresh_s = int(self.config.get("refresh_s", 30))

        font_cfg = (self.config.get("font") or {})
        self.primary_color = hex_to_rgb(font_cfg.get("primary_color", "#FFFFFF"))
        self.secondary_color = hex_to_rgb(font_cfg.get("secondary_color", "#F7931A"))

        layout = self.config.get("layout", {}) or {}

        logo_cfg = (layout.get("logo") or {})
        self.logo_path = str(logo_cfg.get("path", "assets/images/logo/btc.png"))
        self.logo_size = int(logo_cfg.get("size", 32))
        self.logo_center = bool(logo_cfg.get("center", False))
        self.logo_x = int(logo_cfg.get("x", 0))
        self.logo_y = int(logo_cfg.get("y", 4))

        text_cfg = (layout.get("text") or {})
        self.text_center = bool(text_cfg.get("center", False))
        self.text_x = int(text_cfg.get("x", 0))
        self.text_y = int(text_cfg.get("y", 42))
        self.text_scale_pref = int(text_cfg.get("scale", 1))
        self.text_spacing = int(text_cfg.get("spacing", 1))
        self.show_change = bool(text_cfg.get("show_change", True))
        self.change_on_new_line = bool(text_cfg.get("change_on_new_line", True))

    def _init_clients(self) -> None:
        self._http = requests.Session()

    def _close_clients(self) -> None:
        if self._http is not None:
            try:
                self._http.close()
            except Exception:
                # close should never be fatal
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
            q = self._fetch_quote_coingecko()
            if q is not None:
                self.quote = q
            self._last_fetch = now

    def _render(self) -> None:
        assert self.renderer is not None
        assert self.quote is not None

        # ----- LOGO -----
        if self._logo_pixels is not None:
            x_logo = max(0, (self.renderer.width - self._logo_w) // 2) if self.logo_center else self.logo_x
            draw_image_rgba(self.renderer, x_logo, self.logo_y, self._logo_pixels, self._logo_w, self._logo_h)

        # ----- PRICE -----
        compact = self._format_compact_price(self.quote.price)
        price_text = f"{compact} {self.currency_label}"

        scale = max(1, int(self.text_scale_pref))
        while scale > 1:
            w, _ = measure_text(price_text, scale=scale, spacing=self.text_spacing)
            if w <= self.renderer.width:
                break
            scale -= 1

        w, h = measure_text(price_text, scale=scale, spacing=self.text_spacing)

        x_price = max(0, (self.renderer.width - w) // 2) if self.text_center else self.text_x
        y_price = self.text_y
        if y_price + h > self.renderer.height:
            y_price = self.renderer.height - h

        draw_text(self.renderer, x_price, y_price, price_text, self.primary_color, scale=scale,
                  spacing=self.text_spacing)

        # ----- CHANGE -----
        if self.show_change and self.quote.change_24h_percent is not None:
            change_text = f"{self.quote.change_24h_percent:+.2f}%"
            ch_scale = 1
            ch_w, ch_h = measure_text(change_text, scale=ch_scale)

            if self.change_on_new_line:
                y_change = y_price + h + 2
                if y_change + ch_h > self.renderer.height:
                    return
                x_change = max(0, (self.renderer.width - ch_w) // 2) if self.text_center else self.text_x
            else:
                x_change = x_price + w + 2
                y_change = y_price
                if x_change + ch_w > self.renderer.width:
                    return

            draw_text(self.renderer, x_change, y_change, change_text, self.secondary_color, scale=ch_scale)

    def _format_compact_price(self, price: float) -> str:
        if price >= 1_000_000_000:
            return f"{price / 1_000_000_000:.2f}B"
        if price >= 1_000_000:
            return f"{price / 1_000_000:.2f}M"
        if price >= 1_000:
            return f"{price / 1_000:.2f}K"
        return f"{price:.0f}"

    def _fetch_quote_coingecko(self) -> Optional[BitcoinQuote]:
        if self._http is None:
            return None

        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": self.coin_id,
            "vs_currencies": self.currency,
            "include_24hr_change": "true",
        }

        try:
            resp = self._http.get(url, params=params, timeout=5)
            resp.raise_for_status()
            data = resp.json()

            coin = data.get(self.coin_id)
            if not isinstance(coin, dict):
                logger.warning("%s: unexpected response: %s", self.__class__.__name__, data)
                return None

            price = coin.get(self.currency)
            change = coin.get(f"{self.currency}_24h_change")
            if price is None:
                logger.warning("%s: missing price in response: %s", self.__class__.__name__, coin)
                return None

            return BitcoinQuote(
                price=float(price),
                currency=self.currency,
                change_24h_percent=float(change) if change is not None else None,
                ts=time.time(),
            )

        except requests.RequestException as e:
            logger.warning("%s: API error: %s", self.__class__.__name__, e, exc_info=True)
            return None
        except (ValueError, TypeError) as e:
            logger.warning("%s: parse error: %s", self.__class__.__name__, e, exc_info=True)
            return None
