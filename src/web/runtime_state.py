from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class WebConfig:
    """
    Runtime configuration for the Pixel Deck web interface.

    The values are loaded from the `web` section of `config.yml` and control
    whether the web server is enabled, where it listens, and which sensitive
    control operations are allowed through the API.
    """
    enabled: bool = False
    host: str = "0.0.0.0"
    port: int = 8080
    api_token: str = ""
    allow_restart: bool = True
    allow_display_power_control: bool = True
    allow_debug_logging: bool = True

    @staticmethod
    def from_dict(data: dict | None) -> "WebConfig":
        """
        Create a WebConfig instance from a configuration dictionary.

        Missing values are replaced with safe defaults. Passing `None`
        produces a disabled web configuration with the default host, port,
        and permissions.

        Args:
            data: Parsed `web` section from `config.yml`.

        Returns:
            A normalized WebConfig instance.
        """
        data = data or {}
        return WebConfig(
            enabled=bool(data.get("enabled", False)),
            host=str(data.get("host", "0.0.0.0")),
            port=int(data.get("port", 8080)),
            api_token=str(data.get("api_token", "")),
            allow_restart=bool(data.get("allow_restart", True)),
            allow_display_power_control=bool(data.get("allow_display_power_control", True)),
            allow_debug_logging=bool(data.get("allow_debug_logging", True)),
        )


class RuntimeState:
    """
    Thread-safe shared runtime state for Pixel Deck and its Web API.

    The state object connects the main application loop, renderer, and web
    server. It stores the currently active scene, renderer reference, display
    state, timestamps, web configuration, and control events.

    Access to mutable renderer-related values is protected by a lock because
    the renderer loop and FastAPI endpoints may run in different threads.
    """

    def __init__(self, config_path: str | Path):
        """
        Initialize runtime state for a Pixel Deck application instance.

        Args:
            config_path: Path to the active `config.yml` file.
        """
        # Resolve to an absolute path immediately so that all downstream
        # operations (load, save, backup, tempfile) use a stable absolute
        # path regardless of later CWD changes or how the process was started
        # (e.g. Docker daemon thread, systemd service, dev shell).
        self.config_path = Path(config_path).resolve()
        self.reload_event = threading.Event()
        self.restart_event = threading.Event()
        self.started_at = time.time()

        self._lock = threading.Lock()
        self._active_scene: Optional[str] = None
        self._last_present_at: Optional[float] = None
        self._last_config_reload_at: Optional[float] = None
        self._renderer = None

        self.display_enabled = True
        self.renderer_mode = "window"
        self.web = WebConfig()
        self.registered_scenes: frozenset[str] = frozenset()

    def set_renderer(self, renderer) -> None:
        """
        Store the active renderer instance.

        The renderer may be either the development window renderer or the
        physical RGB matrix renderer.

        Args:
            renderer: Active renderer instance, or `None` when unavailable.
        """
        with self._lock:
            self._renderer = renderer

    def get_renderer(self):
        """
        Return the currently active renderer instance.

        Returns:
            The active renderer, or `None` if no renderer has been registered.
        """
        with self._lock:
            return self._renderer

    def set_active_scene(self, name: Optional[str]) -> None:
        """
        Update the name of the currently active scene.

        Args:
            name: Registered scene name, or `None` when no scene is active.
        """
        with self._lock:
            self._active_scene = name

    def mark_present(self) -> None:
        """
        Record that the renderer has presented a new frame.

        The timestamp is exposed through the status API and can be used to
        determine whether rendering is still active.
        """
        with self._lock:
            self._last_present_at = time.time()

    def mark_config_reload(self) -> None:
        """
        Record the time of the latest successful configuration reload.
        """
        with self._lock:
            self._last_config_reload_at = time.time()

    def set_display_enabled(self, enabled: bool) -> None:
        """
        Enable or disable display output.

        The state is stored even when no renderer is currently available.
        If the active renderer supports `set_output_enabled()`, the change is
        applied immediately.

        Args:
            enabled: `True` to enable output, `False` to disable it.
        """
        self.display_enabled = bool(enabled)
        renderer = self.get_renderer()
        if renderer is not None and hasattr(renderer, "set_output_enabled"):
            renderer.set_output_enabled(self.display_enabled)

    def apply_config(self, app_cfg: dict, display_cfg: dict, web_cfg: dict | None) -> None:
        """
        Apply relevant configuration sections to the runtime state.

        This method updates the renderer mode, display output state, and web
        configuration after initial startup or a configuration reload.

        Args:
            app_cfg: Parsed `app` section from `config.yml`.
            display_cfg: Parsed `display` section from `config.yml`.
            web_cfg: Parsed `web` section from `config.yml`, or `None`.
        """
        self.renderer_mode = str(app_cfg.get("render", "window"))
        output_enabled = bool(display_cfg.get("output_enabled", True))
        self.set_display_enabled(output_enabled)
        self.web = WebConfig.from_dict(web_cfg)

    def get_status(self) -> dict:
        """
        Return a snapshot of the current runtime status.

        The returned dictionary is suitable for serialization by the Web API.

        Returns:
            Runtime information including the active scene, renderer mode,
            display state, timestamps, uptime origin, and web server state.
        """
        with self._lock:
            return {
                "active_scene": self._active_scene,
                "display_enabled": self.display_enabled,
                "renderer_mode": self.renderer_mode,
                "last_present_at": self._last_present_at,
                "last_config_reload_at": self._last_config_reload_at,
                "started_at": self.started_at,
                "web_enabled": self.web.enabled,
            }

