from __future__ import annotations

import logging
import threading
import time
from pathlib import Path

import uvicorn

from src.core.app_config import Config, ConfigError
from src.core.logging_config import setup_logging
from src.renderer.recording_renderer import RecordingRenderer
from src.renderer.renderer_factory import create_renderer
from src.scenes.bitcoin import BitcoinScene
from src.scenes.calendar import CalendarScene
from src.scenes.clock import ClockScene
from src.scenes.day_state import DayStateScene
from src.scenes.f1_calendar import F1CalendarScene
from src.scenes.images_random import ImagesRandomScene
from src.scenes.registry import SceneRegistry
from src.scenes.show_app_logo import ShowAppLogo
from src.scenes.sp500 import SP500Scene
from src.scenes.text import TextScene
from src.scenes.weather import WeatherScene
from src.web.app_factory import create_app
from src.web.runtime_state import RuntimeState

logger = logging.getLogger(__name__)


def get_version() -> str:
    project_root = Path(__file__).resolve().parent
    version_file = project_root / "VERSION"
    if version_file.is_file():
        return version_file.read_text(encoding="utf-8").strip()
    return "0.0.0"


def build_registry() -> SceneRegistry:
    """
    Create and populate the scene registry with all available scene classes.

    Each scene class must declare ``scene_name`` as a class attribute.
    The registry uses that attribute as the lookup key, so the string no
    longer needs to be duplicated at the call site.

    To add a new scene: import its class and call ``reg.register(MyScene)``.
    """
    reg = SceneRegistry()
    reg.register(ClockScene)
    reg.register(BitcoinScene)
    reg.register(CalendarScene)
    reg.register(WeatherScene)
    reg.register(SP500Scene)
    reg.register(TextScene)
    reg.register(ImagesRandomScene)
    reg.register(DayStateScene)
    reg.register(F1CalendarScene)
    reg.register(ShowAppLogo)
    return reg


def build_renderer(cfg: Config):
    """Create the concrete renderer (Window or Matrix) based on app/display config."""
    return create_renderer(cfg.app, cfg.display)


def run_scene(scene, renderer, runtime: RuntimeState, duration_s: int | None = None) -> str:
    """
    Run a single scene until it finishes, is interrupted, or a signal arrives.

    The loop honours ``scene.fps`` for consistent tick-rate and sleeps the
    remaining frame budget to avoid busy-waiting.

    Parameters
    ----------
    scene:
        Fully constructed scene instance (``on_enter`` has *not* been called yet).
    renderer:
        Active renderer; ``clear`` and ``present`` are called each frame.
    runtime:
        Shared runtime state.  ``restart_event`` and ``reload_event`` are
        checked every frame so the loop can be interrupted without delay.
    duration_s:
        Maximum scene runtime in seconds.  ``None`` means run indefinitely
        (used in single-scene mode where the scene controls its own exit).

    Returns
    -------
    str
        ``"restart"``   – restart was requested via ``runtime.restart_event``
        ``"reload"``    – config reload was requested via ``runtime.reload_event``
        ``"completed"`` – scene ran for the full ``duration_s``
    """
    scene.on_enter()
    try:
        fps = max(1, int(scene.fps))
        frame_time = 1.0 / fps
        last = time.time()
        elapsed = 0.0

        while True:
            if runtime.restart_event.is_set():
                return "restart"
            if runtime.reload_event.is_set():
                return "reload"

            now = time.time()
            dt = max(0.0, now - last)
            last = now
            elapsed += dt

            renderer.clear(scene.bg_rgb)
            scene.update(dt)
            renderer.present()

            if duration_s is not None and elapsed >= duration_s:
                break

            sleep_time = max(0.0, frame_time - (time.time() - now))
            if sleep_time:
                time.sleep(sleep_time)

    finally:
        scene.on_exit()

    return "completed"


def run_startup_logo(cfg: Config, reg: SceneRegistry, renderer, runtime: RuntimeState) -> None:
    """
    Optionally display the application logo on startup before the main loop.

    Controlled by ``app.show_app_logo_on_start`` (default ``True``) and
    ``app.startup_logo_duration_s`` (default ``5`` s).  The function is a
    no-op when the flag is disabled so callers don't need to guard it.
    """
    if not cfg.app.get("show_app_logo_on_start", True):
        return

    duration = int(cfg.app.get("startup_logo_duration_s", 5))
    scene = reg.create("show_app_logo", {}, renderer=renderer)
    runtime.set_active_scene("show_app_logo")
    logger.info("Showing startup logo (duration=%ss)", duration)
    run_scene(scene, renderer, runtime, duration_s=duration)


def run_single(cfg: Config, reg: SceneRegistry, renderer, runtime: RuntimeState) -> str:
    """
    Run the scene specified by ``app.active_scene`` indefinitely.

    The scene is recreated on every reload so config changes take effect
    without restarting the process.  Returns as soon as a restart or reload
    signal is received.

    Returns
    -------
    str
        ``"restart"``, ``"reload"``, or ``"completed"``.
    """
    while True:
        scene_name = cfg.app.get("active_scene")
        if not scene_name:
            raise ConfigError("app.active_scene is not set")

        scene_cfg = cfg.get_scene_config(scene_name)
        scene = reg.create(scene_name, scene_cfg, renderer=renderer)
        runtime.set_active_scene(scene_name)
        logger.info("Running single scene: %s", scene_name)
        result = run_scene(scene, renderer, runtime, duration_s=None)

        if result == "restart":
            return "restart"
        if result == "reload":
            return "reload"

        break

    return "completed"


def run_rotate(cfg: Config, reg: SceneRegistry, renderer, runtime: RuntimeState) -> str:
    """
    Cycle through all enabled scenes in the order defined by ``app.scene_order``.

    Each iteration re-reads the enabled scene list and the rotation order from
    the current ``cfg`` snapshot so that a config reload mid-rotation picks up
    the new values on the next full cycle.  Scenes not present in the registry
    or disabled in config are silently skipped.

    The loop is infinite by design – it exits only when a restart or reload
    signal is detected (checked both between scenes and at the top of each
    full cycle).

    Returns
    -------
    str
        ``"restart"`` or ``"reload"`` (never ``"completed"`` in normal operation).
    """
    while True:
        if runtime.restart_event.is_set():
            return "restart"
        if runtime.reload_event.is_set():
            return "reload"

        order = cfg.app.get("scene_order", [])
        if not order:
            raise ConfigError("app.scene_order is empty")

        enabled = set(cfg.get_enabled_scenes())
        scenes = [s for s in order if s in enabled]
        if not scenes:
            raise ConfigError("No enabled scenes to rotate")

        logger.info("Rotating scenes: %s", scenes)

        for scene_name in scenes:
            if runtime.restart_event.is_set():
                return "restart"
            if runtime.reload_event.is_set():
                return "reload"

            scene_cfg = cfg.get_scene_config(scene_name)
            duration = int(scene_cfg.get("duration_s", 10))
            scene = reg.create(scene_name, scene_cfg, renderer=renderer)
            runtime.set_active_scene(scene_name)
            result = run_scene(scene, renderer, runtime, duration_s=duration)

            if result == "restart":
                return "restart"
            if result == "reload":
                return "reload"

    return "completed"


def start_web_server(runtime: RuntimeState):
    """
    Start the FastAPI/uvicorn web server in a daemon background thread.

    The server is created from ``runtime`` (host, port, and shared state) and
    runs for the lifetime of the process.  Returns the ``uvicorn.Server``
    instance so the caller can request a graceful shutdown via
    ``server.should_exit = True``.
    """
    app = create_app(runtime)
    config = uvicorn.Config(app, host=runtime.web.host, port=runtime.web.port, log_level="info")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    return server


def load_config(runtime: RuntimeState) -> Config:
    """
    Load (or reload) ``config.yml`` and synchronise runtime state.

    Applies the freshly parsed ``app`` and ``display`` sections to
    ``runtime`` and fires ``runtime.mark_config_reload()`` so any component
    waiting on a config-change signal is notified.

    Returns
    -------
    Config
        Fully parsed configuration object ready for use by renderers and scenes.
    """
    cfg = Config(runtime.config_path)
    runtime.apply_config(cfg.app, cfg.display, cfg._raw.get("web"))
    runtime.mark_config_reload()
    return cfg


def main() -> None:
    """
    Application entry point.

    Startup sequence
    ----------------
    1. Load config and configure logging.
    2. Build the scene registry.
    3. Create the renderer stack (concrete renderer wrapped in
       ``RecordingRenderer`` for live preview / frame capture).
    4. Optionally start the web server in a background thread.
    5. Show the startup logo (if enabled).
    6. Enter the main scene loop (single or rotate mode).

    Signal handling
    ---------------
    The main loop responds to two runtime signals emitted by the web layer:

    * ``restart_event`` – break out of the loop and exit the process
      (a process manager such as systemd is expected to restart it).
    * ``reload_event``  – reload ``config.yml`` in-place and continue
      without restarting the process.

    Errors
    ------
    ``ConfigError`` is caught and logged as a user-readable message.
    All other exceptions are logged with a full traceback via
    ``logger.exception``.  Either way the ``finally`` block ensures the
    web server and renderer are shut down cleanly.
    """
    renderer = None
    web_server = None
    runtime = RuntimeState("config/config.yml")

    try:
        cfg = Config(runtime.config_path)
        setup_logging(cfg.app.get("log_level", "INFO"))

        reg = build_registry()
        runtime.registered_scenes = frozenset(reg.available())
        mode = cfg.app.get("mode", "single")
        logger.info("Pixel Deck v%s starting...", get_version())
        logger.info("Mode: %s", mode)

        cfg = load_config(runtime)
        renderer = build_renderer(cfg)
        renderer = RecordingRenderer(
            renderer,
            on_present=runtime.mark_present,
            output_enabled=runtime.display_enabled,
        )
        runtime.set_renderer(renderer)

        if runtime.web.enabled:
            web_server = start_web_server(runtime)
            logger.info("Web UI enabled on %s:%s", runtime.web.host, runtime.web.port)

        run_startup_logo(cfg, reg, renderer, runtime)

        while True:
            if mode == "single":
                result = run_single(cfg, reg, renderer, runtime)
            elif mode == "rotate":
                result = run_rotate(cfg, reg, renderer, runtime)
            else:
                raise ConfigError(f"Unknown app.mode: {mode}")

            if result == "restart":
                logger.info("Restart requested")
                break
            if result == "reload":
                runtime.reload_event.clear()
                cfg = load_config(runtime)
                mode = cfg.app.get("mode", "single")
                logger.info("Config reloaded")
                continue

            break

    except ConfigError as exc:
        logger.error("CONFIG ERROR: %s", exc)
    except KeyboardInterrupt:
        logger.info("Stopped by user")
    except Exception:
        logger.exception("Unhandled exception")
    finally:
        if web_server is not None:
            web_server.should_exit = True
        if renderer is not None and hasattr(renderer, "close"):
            renderer.close()


if __name__ == "__main__":
    main()
