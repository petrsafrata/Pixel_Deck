"""
Core configuration loader for Pixel Deck.

Reads ``config.yml`` (YAML) and exposes its sections as typed attributes.
``Config`` is the single entry point for all configuration access; the rest
of the application should never read the YAML file directly.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from ruamel.yaml import YAML


class ConfigError(Exception):
    """Raised for any configuration problem (missing file, invalid structure, etc.)."""


class Config:
    """
    Parsed representation of ``config.yml``.

    Attributes
    ----------
    config_path:
        Absolute path to the YAML file that was loaded.
    display:
        Raw ``display`` section dict (hardware / canvas settings).
    scene_defaults:
        Raw ``scene_defaults`` section dict used as fallback values for every scene.
    app:
        Raw ``app`` section dict (mode, render target, log level, …).
    scenes:
        Raw ``scenes`` section dict keyed by scene name.
    """

    def __init__(self, config_path: str | Path):
        """
        Load and validate ``config_path``.

        Raises
        ------
        ConfigError
            If the file does not exist, a required section is missing, or any
            scene is missing its ``enabled`` flag.
        """
        # Resolve to absolute path immediately – prevents CWD-dependent
        # behaviour when the config is read after a directory change.
        self.config_path = Path(config_path).resolve()

        if not self.config_path.exists():
            raise ConfigError(f"Config file not found: {self.config_path}")

        self._raw = self._load_yaml()
        self.display = self._raw.get("display", {})
        self.scene_defaults = self._raw.get("scene_defaults", {})
        self.app = self._raw.get("app", {})
        self.scenes = self._raw.get("scenes", {})

        self._validate()

    def _load_yaml(self) -> dict:
        """Read the YAML file and return its contents as a plain dict."""
        yaml = YAML(typ="safe")
        with open(self.config_path, "r", encoding="utf-8") as handle:
            return yaml.load(handle) or {}

    def _validate(self):
        """
        Perform basic structural validation after loading.

        Checks that the ``display`` and ``scenes`` sections are present and
        that every scene declares an ``enabled`` flag.  Raises ``ConfigError``
        on the first violation found.
        """
        if not self.display:
            raise ConfigError("Missing 'display' section in config.yml")

        if not self.scenes:
            raise ConfigError("No scenes defined in config.yml")

        for name, scene in self.scenes.items():
            if "enabled" not in scene:
                raise ConfigError(f"Scene '{name}' is missing 'enabled' flag")

    def get_scene_config(self, scene_name: str) -> dict:
        """
        Return the merged configuration for *scene_name*.

        The returned dict is a deep copy of ``scene_defaults`` with the
        scene-specific overrides applied on top, so callers may mutate it
        freely without affecting the cached raw data.

        Parameters
        ----------
        scene_name:
            Key that must exist in the ``scenes`` section of the config.

        Raises
        ------
        ConfigError
            If *scene_name* is not found in ``scenes``.
        """
        if scene_name not in self.scenes:
            raise ConfigError(f"Scene '{scene_name}' not found")

        scene_cfg = deepcopy(self.scene_defaults)
        self._deep_update(scene_cfg, self.scenes[scene_name])
        return scene_cfg

    def get_enabled_scenes(self) -> list[str]:
        """Return a list of scene names whose ``enabled`` flag is ``True``."""
        return [name for name, scene in self.scenes.items() if scene.get("enabled", False)]

    def _deep_update(self, base: dict, override: dict):
        """
        Recursively merge *override* into *base* in-place.

        Nested dicts are merged rather than replaced, so a scene can override
        a single font colour without losing the rest of the ``font`` block
        inherited from ``scene_defaults``.
        """
        for key, value in override.items():
            if isinstance(value, dict) and isinstance(base.get(key), dict):
                self._deep_update(base[key], value)
            else:
                base[key] = value
