from __future__ import annotations

import pygame

from src.renderer.base_renderer import BaseRenderer, Color


class WindowRenderer(BaseRenderer):
    def __init__(
        self,
        width: int,
        height: int,
        scale: int = 10,
        window_title: str = "Pixel Display Simulator",
        show_grid: bool = False,
    ):
        super().__init__(width, height)
        self.scale = int(scale)
        self.show_grid = bool(show_grid)

        pygame.init()
        pygame.display.set_caption(window_title)
        self.screen = pygame.display.set_mode((self.width * self.scale, self.height * self.scale))
        self.clock = pygame.time.Clock()
        self._closed = False

        # backbuffer as Surface in "pixel" resolution
        self.surface = pygame.Surface((self.width, self.height))

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._closed = True

        if self._closed:
            raise SystemExit

    def clear(self, color: Color = (0, 0, 0)) -> None:
        self._handle_events()
        self.surface.fill(color)

    def set_pixel(self, x: int, y: int, color: Color) -> None:
        if 0 <= x < self.width and 0 <= y < self.height:
            self.surface.set_at((x, y), color)

    def present(self) -> None:
        self._handle_events()

        # upscale surface to window size
        scaled = pygame.transform.scale(self.surface, (self.width * self.scale, self.height * self.scale))
        self.screen.blit(scaled, (0, 0))

        if self.show_grid and self.scale >= 6:
            self._draw_grid()

        pygame.display.flip()

    def _draw_grid(self) -> None:
        w, h = self.width * self.scale, self.height * self.scale
        for x in range(0, w, self.scale):
            pygame.draw.line(self.screen, (30, 30, 30), (x, 0), (x, h))
        for y in range(0, h, self.scale):
            pygame.draw.line(self.screen, (30, 30, 30), (0, y), (w, y))

    def close(self) -> None:
        pygame.quit()
