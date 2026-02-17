from __future__ import annotations

import logging
from typing import List, Tuple

from src.scenes.base_scene import BaseScene
from src.gfx.draw import draw_text, measure_text, hex_to_rgb

logger = logging.getLogger(__name__)


class TextScene(BaseScene):
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
            "%s entered (len=%d, max_lines=%d, pref_scale=%d, align=%s)",
            self.__class__.__name__,
            len(self.value),
            self.max_lines,
            self.pref_scale,
            self.align,
        )

    def on_exit(self) -> None:
        logger.info("%s exited", self.__class__.__name__)
        super().on_exit()

    def update(self, dt: float) -> None:
        if self.renderer is None or not self.value:
            return

        scale = max(1, int(self.pref_scale))
        lines: List[str] = []

        while scale >= 1:
            lines = self._wrap_text(self.value, scale=scale)
            if lines and self._fits_vertically(lines, scale=scale):
                break
            scale -= 1

        if not lines:
            return

        # even vertical distribution
        line_h = 7 * scale  # 5x7 font height scaled
        total_h = len(lines) * line_h + (len(lines) - 1) * self.line_gap
        start_y = max(0, (self.renderer.height - total_h) // 2)

        y = start_y
        for line in lines:
            w, _ = measure_text(line, scale=scale, spacing=self.spacing)

            if self.align == "left":
                x = 0
            else:
                x = max(0, (self.renderer.width - w) // 2)

            draw_text(
                self.renderer,
                x,
                y,
                line,
                self.primary_color,
                scale=scale,
                spacing=self.spacing,
            )
            y += line_h + self.line_gap

    # --------------------
    # Internal helpers
    # --------------------
    def _init_state_defaults(self) -> None:
        # colors
        self.primary_color: Tuple[int, int, int] = (255, 255, 255)

        # text config
        self.value: str = ""
        self.max_lines: int = 4
        self.pref_scale: int = 2
        self.spacing: int = 1
        self.line_gap: int = 2
        self.align: str = "center"

    def _load_config(self) -> None:
        font_cfg = (self.config.get("font") or {})
        self.primary_color = hex_to_rgb(font_cfg.get("primary_color", "#FFFFFF"))

        txt_cfg = (self.config.get("text") or {})
        self.value = str(txt_cfg.get("value", "")).strip()
        self.max_lines = int(txt_cfg.get("max_lines", 4))
        self.pref_scale = int(txt_cfg.get("scale", 2))
        self.spacing = int(txt_cfg.get("spacing", 1))
        self.line_gap = int(txt_cfg.get("line_gap", 2))
        self.align = str(txt_cfg.get("align", "center")).lower()

    def _wrap_text(self, text: str, scale: int) -> List[str]:
        """
        Word-wrap into max_lines so that each line does not exceed display width.
        If a word is longer than a line, it is split into parts.
        """
        words = text.split()
        if not words or self.renderer is None:
            return []

        lines: List[str] = []
        cur = ""

        def fits(s: str) -> bool:
            w, _ = measure_text(s, scale=scale, spacing=self.spacing)
            return w <= self.renderer.width

        for word in words:
            candidate = word if not cur else (cur + " " + word)

            if fits(candidate):
                cur = candidate
                continue

            if cur:
                lines.append(cur)
                cur = ""

            if not fits(word):
                parts = self._break_word(word, scale=scale)
                for p in parts[:-1]:
                    lines.append(p)
                    if len(lines) >= self.max_lines:
                        return lines[: self.max_lines]
                cur = parts[-1]
            else:
                cur = word

            if len(lines) >= self.max_lines:
                return lines[: self.max_lines]

        if cur and len(lines) < self.max_lines:
            lines.append(cur)

        return lines[: self.max_lines]

    def _break_word(self, word: str, scale: int) -> List[str]:
        """
        Cuts a word into parts so that each part fits on a line.
        """
        if self.renderer is None:
            return [word]

        parts: List[str] = []
        buf = ""

        for ch in word:
            cand = buf + ch
            w, _ = measure_text(cand, scale=scale, spacing=self.spacing)
            if w <= self.renderer.width:
                buf = cand
            else:
                if buf:
                    parts.append(buf)
                buf = ch

        if buf:
            parts.append(buf)

        return parts

    def _fits_vertically(self, lines: List[str], scale: int) -> bool:
        if self.renderer is None:
            return False
        line_h = 7 * scale
        total_h = len(lines) * line_h + (len(lines) - 1) * self.line_gap
        return total_h <= self.renderer.height
