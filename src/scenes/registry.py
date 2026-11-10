from __future__ import annotations

from typing import Any, Optional, Type

from src.scenes.base_scene import BaseScene


class SceneRegistry:
    """
    Simple registry / factory for scenes.
    Allows creating scenes by name without if/else in main loop.

    Registration uses the class-level ``scene_name`` attribute as the key,
    so the name is declared exactly once – on the scene class itself.
    """

    def __init__(self):
        self._scenes: dict[str, Type[BaseScene]] = {}

    def register(self, scene_cls: Type[BaseScene]) -> None:
        """Register a scene class.  The registry key is taken from
        ``scene_cls.scene_name``; it must be a non-empty string.
        """
        key = scene_cls.scene_name.strip().lower()
        if not key:
            raise ValueError(
                f"{scene_cls.__name__}.scene_name is empty – "
                "set scene_name = '<key>' on the class before registering."
            )
        self._scenes[key] = scene_cls

    def create(self, name: str, config: dict[str, Any], renderer: Optional[Any] = None) -> BaseScene:
        key = name.strip().lower()
        if key not in self._scenes:
            available = ", ".join(sorted(self._scenes.keys()))
            raise KeyError(f"Unknown scene '{name}'. Available: {available}")
        return self._scenes[key](name=key, config=config, renderer=renderer)

    def available(self) -> list[str]:
        return sorted(self._scenes.keys())
