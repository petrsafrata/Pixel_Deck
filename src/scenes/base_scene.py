from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional
from src.gfx.draw import hex_to_rgb


class BaseScene(ABC):
    """
    Base class for all scenes.

    Lifecycle:
      - on_enter()  : called once when scene becomes active
      - update(dt)  : called repeatedly; dt is seconds since last update
      - on_exit()   : called once when scene is deactivated
    """

    def __init__(self, name: str, config: dict[str, Any], renderer: Optional[Any] = None):
        self.name = name
        self.config = config
        self.renderer = renderer
        self._running = False

    def on_enter(self) -> None:
        self._running = True

    @abstractmethod
    def update(self, dt: float) -> None:
        """
        Implement scene logic and drawing here.
        dt: time delta in seconds since last update call
        """
        raise NotImplementedError

    def on_exit(self) -> None:
        self._running = False

    @property
    def fps(self) -> int:
        return int(self.config.get("fps", 30))

    @property
    def duration_s(self) -> int:
        return int(self.config.get("duration_s", 10))

    @property
    def background(self) -> str:
        return str(self.config.get("background", "#000000"))

    @property
    def bg_rgb(self) -> tuple[int, int, int]:
        return hex_to_rgb(self.config.get("background", "#000000"))
