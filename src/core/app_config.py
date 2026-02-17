from pathlib import Path
import yaml
from copy import deepcopy


class ConfigError(Exception):
    pass


class Config:
    def __init__(self, config_path: str | Path):
        self.config_path = Path(config_path)

        if not self.config_path.exists():
            raise ConfigError(f"Config file not found: {self.config_path}")

        self._raw = self._load_yaml()
        self.display = self._raw.get("display", {})
        self.scene_defaults = self._raw.get("scene_defaults", {})
        self.app = self._raw.get("app", {})
        self.scenes = self._raw.get("scenes", {})

        self._validate()

    # ---------- Loading ----------

    def _load_yaml(self) -> dict:
        with open(self.config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    # ---------- Validation ----------

    def _validate(self):
        if not self.display:
            raise ConfigError("Missing 'display' section in config.yml")

        if not self.scenes:
            raise ConfigError("No scenes defined in config.yml")

        for name, scene in self.scenes.items():
            if "enabled" not in scene:
                raise ConfigError(f"Scene '{name}' is missing 'enabled' flag")

    # ---------- Public API ----------

    def get_scene_config(self, scene_name: str) -> dict:
        """
        Returns merged config:
        scene_defaults + scenes[scene_name]
        """
        if scene_name not in self.scenes:
            raise ConfigError(f"Scene '{scene_name}' not found")

        scene_cfg = deepcopy(self.scene_defaults)
        self._deep_update(scene_cfg, self.scenes[scene_name])

        return scene_cfg

    def get_enabled_scenes(self) -> list[str]:
        return [
            name for name, scene in self.scenes.items()
            if scene.get("enabled", False)
        ]

    # ---------- Utils ----------

    def _deep_update(self, base: dict, override: dict):
        """
        Recursive dict merge
        """
        for key, value in override.items():
            if isinstance(value, dict) and isinstance(base.get(key), dict):
                self._deep_update(base[key], value)
            else:
                base[key] = value
