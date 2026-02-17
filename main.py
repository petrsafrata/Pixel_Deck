import time
import logging

from src.core.app_config import Config, ConfigError
from src.core.logging_config import setup_logging

from src.scenes.registry import SceneRegistry
from src.scenes.clock import ClockScene
from src.scenes.bitcoin import BitcoinScene
from src.scenes.calendar import CalendarScene
from src.scenes.weather import WeatherScene
from src.scenes.sp500 import SP500Scene
from src.scenes.text import TextScene
from src.scenes.images_random import ImagesRandomScene

from src.renderer.renderer_factory import create_renderer

logger = logging.getLogger(__name__)


def build_registry() -> SceneRegistry:
    reg = SceneRegistry()
    reg.register("clock", ClockScene)
    reg.register("bitcoin", BitcoinScene)
    reg.register("calendar", CalendarScene)
    reg.register("weather", WeatherScene)
    reg.register("sp500", SP500Scene)
    reg.register("text", TextScene)
    reg.register("images", ImagesRandomScene)
    return reg


def build_renderer(cfg: Config):
    """
    Renderer factory wrapper.

    Uses:
      app.render
      display.*
      simulator.* (for window mode only)
    """
    app_cfg = cfg.app
    display_cfg = cfg.display

    renderer = create_renderer(app_cfg, display_cfg)

    return renderer


def run_scene(scene, renderer, duration_s: int | None = None):
    scene.on_enter()
    try:
        fps = max(1, int(scene.fps))
        frame_time = 1.0 / fps

        last = time.time()
        start = last

        while True:
            now = time.time()
            dt = now - last
            last = now

            renderer.clear(scene.bg_rgb)
            scene.update(dt)
            renderer.present()

            if duration_s is not None and (now - start) >= duration_s:
                break

            sleep_for = frame_time - (time.time() - now)
            if sleep_for > 0:
                time.sleep(sleep_for)

    finally:
        scene.on_exit()


def run_single(cfg: Config, reg: SceneRegistry, renderer):
    scene_name = cfg.app.get("active_scene")
    if not scene_name:
        raise ConfigError("app.active_scene is not set")

    scene_cfg = cfg.get_scene_config(scene_name)
    scene = reg.create(scene_name, scene_cfg, renderer=renderer)

    logger.info("Running single scene: %s", scene_name)
    run_scene(scene, renderer, duration_s=None)


def run_rotate(cfg: Config, reg: SceneRegistry, renderer):
    order = cfg.app.get("scene_order", [])
    if not order:
        raise ConfigError("app.scene_order is empty")

    enabled = set(cfg.get_enabled_scenes())
    scenes = [s for s in order if s in enabled]

    if not scenes:
        raise ConfigError("No enabled scenes to rotate")

    logger.info("Rotating scenes: %s", scenes)

    while True:
        for scene_name in scenes:
            scene_cfg = cfg.get_scene_config(scene_name)
            duration = int(scene_cfg.get("duration_s", 10))

            scene = reg.create(scene_name, scene_cfg, renderer=renderer)
            logger.info("Switching to scene: %s (duration=%ss)", scene_name, duration)
            run_scene(scene, renderer, duration_s=duration)


def main():
    renderer = None
    try:
        cfg = Config("config.yml")
        setup_logging(cfg.app.get("log_level", "INFO"))

        reg = build_registry()
        renderer = build_renderer(cfg)

        mode = cfg.app.get("mode", "single")
        logger.info("Mode: %s", mode)

        if mode == "single":
            run_single(cfg, reg, renderer)
        elif mode == "rotate":
            run_rotate(cfg, reg, renderer)
        else:
            raise ConfigError(f"Unknown app.mode: {mode}")

    except ConfigError as e:
        logger.error("CONFIG ERROR: %s", e)
    except KeyboardInterrupt:
        logger.info("Stopped by user")
    except Exception:
        logger.exception("Unhandled exception")
    finally:
        if renderer is not None and hasattr(renderer, "close"):
            renderer.close()


if __name__ == "__main__":
    main()
