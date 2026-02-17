from __future__ import annotations

from typing import Any, Optional, Type

from src.scenes.base_scene import BaseScene


class SceneRegistry:
    """
    Simple registry / factory for scenes.
    Allows creating scenes by name without if/else in main loop.
    """

    def __init__(self):
        self._scenes: dict[str, Type[BaseScene]] = {}

    def register(self, name: str, scene_cls: Type[BaseScene]) -> None:
        key = name.strip().lower()
        if not key:
            raise ValueError("Scene name cannot be empty")
        self._scenes[key] = scene_cls

    def create(self, name: str, config: dict[str, Any], renderer: Optional[Any] = None) -> BaseScene:
        key = name.strip().lower()
        if key not in self._scenes:
            available = ", ".join(sorted(self._scenes.keys()))
            raise KeyError(f"Unknown scene '{name}'. Available: {available}")
        return self._scenes[key](name=key, config=config, renderer=renderer)

    def available(self) -> list[str]:
        return sorted(self._scenes.keys())
