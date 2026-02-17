from __future__ import annotations

import logging
from typing import Any, Dict, Tuple

logger = logging.getLogger(__name__)


def _get_int(d: Dict[str, Any], key: str, default: int) -> int:
    try:
        return int(d.get(key, default))
    except Exception:
        return default


def _get_bool(d: Dict[str, Any], key: str, default: bool) -> bool:
    try:
        return bool(d.get(key, default))
    except Exception:
        return default


def _get_str(d: Dict[str, Any], key: str, default: str) -> str:
    try:
        v = d.get(key, default)
        return default if v is None else str(v)
    except Exception:
        return default


def create_renderer(app_cfg: Dict[str, Any], display_cfg: Dict[str, Any]):
    """
    Creates renderer based on app.render:
      - window
      - matrix

    Reads all relevant parameters from config.yml:
      app.render
      display.*
    """
    render_mode = _get_str(app_cfg, "render", "window").lower()

    if render_mode == "window":
        # Development renderer (desktop window)
        from src.renderer.window_renderer import WindowRenderer

        width = _get_int(display_cfg, "width", 64)
        height = _get_int(display_cfg, "height", 64)

        logger.info("Creating WindowRenderer (%dx%d)", width, height)
        return WindowRenderer(width=width, height=height)

    if render_mode == "matrix":
        # Hardware renderer (rpi-rgb-led-matrix)
        from src.renderer.matrix_renderer import MatrixRenderer, MatrixRendererConfig

        cfg = MatrixRendererConfig(
            hardware_mapping=_get_str(display_cfg, "hardware_mapping", "adafruit-hat-pwm"),
            rows=_get_int(display_cfg, "rows", 64),
            cols=_get_int(display_cfg, "cols", 64),
            chain_length=_get_int(display_cfg, "chain_length", 1),
            parallel=_get_int(display_cfg, "parallel", 1),
            pwm_bits=_get_int(display_cfg, "pwm_bits", 11),
            pwm_lsb_nanoseconds=_get_int(display_cfg, "pwm_lsb_nanoseconds", 130),
            brightness=_get_int(display_cfg, "brightness", 70),
            gpio_slowdown=_get_int(display_cfg, "gpio_slowdown", 2),
            scan_mode=_get_int(display_cfg, "scan_mode", 1),
            disable_hardware_pulsing=_get_bool(display_cfg, "disable_hardware_pulsing", False),
        )

        logger.info(
            "Creating MatrixRenderer (rows=%d, cols=%d, chain=%d, parallel=%d, mapping=%s)",
            cfg.rows, cfg.cols, cfg.chain_length, cfg.parallel, cfg.hardware_mapping
        )
        return MatrixRenderer(cfg)

    raise ValueError(f"Unknown app.render mode: {render_mode}")
