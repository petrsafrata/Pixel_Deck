from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class MatrixRendererConfig:
    """
    Hardware config for rpi-rgb-led-matrix.

    IMPORTANT:
    - width/height are derived from rows/cols/chain_length/parallel
      so users only need to change the hardware parameters in config.yml.
    """
    hardware_mapping: str = "adafruit-hat-pwm"
    rows: int = 64
    cols: int = 64
    chain_length: int = 1
    parallel: int = 1

    pwm_bits: int = 11
    pwm_lsb_nanoseconds: int = 130
    brightness: int = 70
    gpio_slowdown: int = 2
    scan_mode: int = 1
    disable_hardware_pulsing: bool = False


class MatrixRenderer:
    """
    Hardware renderer using hzeller/rpi-rgb-led-matrix Python bindings.

    Minimal interface expected by gfx helpers:
      - width, height
      - clear()
      - set_pixel(x, y, r, g, b)
      - present()

    Display size is derived from config:
      width  = cols * chain_length
      height = rows * parallel

    Then verified against the actual canvas size returned by RGBMatrix.
    """

    def __init__(self, cfg: MatrixRendererConfig):
        self.cfg = cfg

        # Derived logical size from config (what user controls in config.yml)
        self.width = int(cfg.cols * cfg.chain_length)
        self.height = int(cfg.rows * cfg.parallel)

        self._matrix = None
        self._canvas = None

        self._init_matrix()

    def _init_matrix(self) -> None:
        try:
            from rgbmatrix import RGBMatrix, RGBMatrixOptions  # type: ignore
        except Exception as e:
            logger.error(
                "MatrixRenderer: rgbmatrix not available. "
                "On Raspberry Pi this will be provided in the Docker image (step B). "
                "Error: %s",
                e,
            )
            raise

        options = RGBMatrixOptions()
        options.hardware_mapping = self.cfg.hardware_mapping
        options.rows = int(self.cfg.rows)
        options.cols = int(self.cfg.cols)
        options.chain_length = int(self.cfg.chain_length)
        options.parallel = int(self.cfg.parallel)

        options.pwm_bits = int(self.cfg.pwm_bits)
        options.pwm_lsb_nanoseconds = int(self.cfg.pwm_lsb_nanoseconds)
        options.brightness = int(self.cfg.brightness)
        options.gpio_slowdown = int(self.cfg.gpio_slowdown)
        options.scan_mode = int(self.cfg.scan_mode)
        options.disable_hardware_pulsing = bool(self.cfg.disable_hardware_pulsing)

        self._matrix = RGBMatrix(options=options)
        self._canvas = self._matrix.CreateFrameCanvas()

        # Verify actual size from the driver and prefer the real values
        real_w = int(getattr(self._canvas, "width", self.width))
        real_h = int(getattr(self._canvas, "height", self.height))

        if real_w != self.width or real_h != self.height:
            logger.warning(
                "MatrixRenderer: derived size %dx%d differs from driver canvas %dx%d. "
                "Using driver canvas size.",
                self.width,
                self.height,
                real_w,
                real_h,
            )

        self.width = real_w
        self.height = real_h

        logger.info(
            "MatrixRenderer initialized: %dx%d (rows=%d, cols=%d, chain=%d, parallel=%d, mapping=%s, brightness=%d)",
            self.width,
            self.height,
            self.cfg.rows,
            self.cfg.cols,
            self.cfg.chain_length,
            self.cfg.parallel,
            self.cfg.hardware_mapping,
            self.cfg.brightness,
        )

    def clear(self) -> None:
        if self._canvas is None:
            return
        self._canvas.Clear()

    def set_pixel(self, x: int, y: int, r: int, g: int, b: int) -> None:
        if self._canvas is None:
            return
        if x < 0 or y < 0 or x >= self.width or y >= self.height:
            return
        self._canvas.SetPixel(int(x), int(y), int(r), int(g), int(b))

    def present(self) -> None:
        """
        Swap frame onto the display. Call once per frame after drawing.
        """
        if self._matrix is None or self._canvas is None:
            return
        self._canvas = self._matrix.SwapOnVSync(self._canvas)
