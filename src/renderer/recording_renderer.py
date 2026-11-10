from __future__ import annotations

import logging
import threading
from io import BytesIO
from typing import Callable, Optional

from PIL import Image

from src.renderer.base_renderer import BaseRenderer, Color

_log = logging.getLogger(__name__)


class RecordingRenderer(BaseRenderer):
    """
    Proxy renderer that records the latest frame into an in-memory buffer
    for preview purposes and allows output toggling.

    Acts as a transparent proxy around an inner renderer (window or matrix).
    When output is disabled, all draw calls are still recorded into the
    internal buffer (for the Web UI preview) but are not forwarded to the
    physical display.

    When toggling from enabled → disabled a single black frame is sent to
    the inner renderer immediately so the physical display goes dark rather
    than freezing on the last rendered frame.
    """

    def __init__(
        self,
        inner: BaseRenderer,
        on_present: Optional[Callable[[], None]] = None,
        output_enabled: bool = True,
    ):
        super().__init__(inner.width, inner.height)
        self._inner = inner
        self._on_present = on_present
        self._output_enabled = bool(output_enabled)
        self._buffer = bytearray(self.width * self.height * 3)
        self._lock = threading.Lock()

    def set_output_enabled(self, enabled: bool) -> None:
        """
        Enable or disable forwarding of draw calls to the physical display.

        When transitioning from enabled to disabled, a single black frame is
        pushed to the inner renderer so the physical display goes dark
        immediately instead of freezing on the last rendered frame.

        Args:
            enabled: True to enable output, False to disable it.
        """
        prev = self._output_enabled
        self._output_enabled = bool(enabled)

        if not enabled and prev:
            # Blank the physical display immediately on disable.
            # This must bypass the _output_enabled guard because the flag is
            # already False at this point.
            _log.info("RecordingRenderer: output disabled – blanking physical display")
            try:
                self._inner.clear()
                self._inner.present()
            except Exception:
                _log.warning("RecordingRenderer: failed to blank display on disable", exc_info=True)
        elif enabled and not prev:
            _log.info("RecordingRenderer: output enabled")

    def clear(self, color: Color = (0, 0, 0)) -> None:
        r, g, b = color
        with self._lock:
            for i in range(0, len(self._buffer), 3):
                self._buffer[i] = int(r)
                self._buffer[i + 1] = int(g)
                self._buffer[i + 2] = int(b)

        if self._output_enabled:
            self._inner.clear(color)

    def set_pixel(self, x: int, y: int, color: Color) -> None:
        if x < 0 or y < 0 or x >= self.width or y >= self.height:
            return

        r, g, b = color
        idx = (y * self.width + x) * 3
        with self._lock:
            self._buffer[idx] = int(r)
            self._buffer[idx + 1] = int(g)
            self._buffer[idx + 2] = int(b)

        if self._output_enabled:
            self._inner.set_pixel(x, y, color)

    def present(self) -> None:
        if self._output_enabled:
            self._inner.present()

        if self._on_present is not None:
            self._on_present()

    def clear_and_present(self, color: Color = (0, 0, 0), force_output: bool = False) -> None:
        """
        Clear the frame buffer and push it to the physical display.

        Unlike the regular clear() + present() pair, this method supports
        force_output which bypasses the _output_enabled guard.  It is used
        by the "clear display" API action to blank the matrix even when
        output is currently disabled.

        Args:
            color:        Fill color for the clear operation (default black).
            force_output: When True, forward to the inner renderer even if
                          output is currently disabled.
        """
        # Always update the internal preview buffer.
        r, g, b = color
        with self._lock:
            for i in range(0, len(self._buffer), 3):
                self._buffer[i] = int(r)
                self._buffer[i + 1] = int(g)
                self._buffer[i + 2] = int(b)

        if force_output or self._output_enabled:
            # Forward clear + present directly so the inner canvas is
            # actually cleared before presenting (fixes the case where
            # force_output=True is used while _output_enabled=False).
            self._inner.clear(color)
            self._inner.present()

    def get_preview_png(self) -> bytes:
        with self._lock:
            data = bytes(self._buffer)

        image = Image.frombytes("RGB", (self.width, self.height), data)
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()

    def close(self) -> None:
        self._inner.close()
