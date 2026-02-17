from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Tuple


Color = Tuple[int, int, int]  # RGB 0-255


class BaseRenderer(ABC):
    def __init__(self, width: int, height: int):
        self.width = int(width)
        self.height = int(height)

    @abstractmethod
    def clear(self, color: Color = (0, 0, 0)) -> None:
        ...

    @abstractmethod
    def set_pixel(self, x: int, y: int, color: Color) -> None:
        ...

    @abstractmethod
    def present(self) -> None:
        """
        Push the current frame to the output (window / hardware).
        """
        ...

    @abstractmethod
    def close(self) -> None:
        ...
