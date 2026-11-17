from __future__ import annotations

from PIL import Image, ImageDraw

from src.core.agent_monitor import AgentMonitor, AgentState
from src.gfx.draw import draw_image_rgb, draw_text, measure_text
from src.scenes.base_scene import BaseScene
from src.web.field_spec import (
    BACKGROUND_FIELD,
    FIELD_TYPE_BOOLEAN,
    FIELD_TYPE_NUMBER,
    FPS_FIELD,
    build_field_spec,
)


class AgentMonitorScene(BaseScene):
    scene_name = "agent_monitor"
    scene_label = "AI Agent Monitor"
    scene_description = (
        "Display AI agent activity and automatically pause scene rotation "
        "while agents are working or waiting for input."
    )

    scene_field_specs = (
        build_field_spec(
            "auto_switch",
            "Automatic switching",
            "Prioritize the monitor during agent activity and resume "
            "normal scenes when the monitor returns to Idle.",
            FIELD_TYPE_BOOLEAN,
            "General",
        ),
        build_field_spec(
            "duration_s",
            "Rotation duration",
            "How long the idle monitor appears during normal rotation. "
            "Does not limit active monitoring or change the Done period.",
            FIELD_TYPE_NUMBER,
            "General",
            unit="seconds",
            minimum=1,
            maximum=3600,
            step=1,
            numeric_type="int",
        ),
        FPS_FIELD,
        BACKGROUND_FIELD,
    )

    COLORS = {
        AgentState.IDLE: (130, 140, 155),
        AgentState.WORKING: (255, 65, 65),
        AgentState.WAITING: (255, 165, 30),
        AgentState.DONE: (55, 220, 95),
    }

    LABELS = {
        AgentState.IDLE: "IDLE",
        AgentState.WORKING: "WORKING",
        AgentState.WAITING: "WAITING",
        AgentState.DONE: "DONE",
    }

    def __init__(self, name: str, config: dict, renderer=None):
        super().__init__(name, config, renderer)
        self._monitor: AgentMonitor | None = None
        self._elapsed_s = 0.0
        self._frames: dict[tuple[AgentState, int], list] = {}

    def bind_monitor(self, monitor: AgentMonitor) -> None:
        """Use the same monitor instance as the Web API."""
        self._monitor = monitor

    def on_enter(self) -> None:
        if self._monitor is None:
            raise RuntimeError("Agent monitor has not been bound to the scene")

        super().on_enter()
        self._elapsed_s = 0.0
        self._frames = {
            (state, phase): self._make_frame(state, phase)
            for state in AgentState
            for phase in (0, 1)
        }

    def on_exit(self) -> None:
        self._frames.clear()
        super().on_exit()

    def update(self, dt: float) -> None:
        if self.renderer is None or self._monitor is None:
            return

        self._elapsed_s += max(0.0, dt)
        snapshot = self._monitor.get_snapshot()
        state = snapshot.state
        phase = int(self._elapsed_s * 2) % 2

        # The layout uses a logical 64x64 canvas.
        # Center it on larger displays and crop on smaller ones.
        offset_x = (self.renderer.width - 64) // 2
        offset_y = (self.renderer.height - 64) // 2
        pixels = self._frames[(state, phase)]

        if self.renderer.width >= 64 and self.renderer.height >= 64:
            draw_image_rgb(
                self.renderer, offset_x, offset_y, pixels, 64, 64
            )
        else:
            for y in range(64):
                for x in range(64):
                    px = offset_x + x
                    py = offset_y + y
                    if (
                        0 <= px < self.renderer.width
                        and 0 <= py < self.renderer.height
                    ):
                        self.renderer.set_pixel(px, py, pixels[y * 64 + x])

        color = self.COLORS[state]
        self._draw_label(
            f"AI:{snapshot.active_count}", offset_y + 2, (180, 190, 205)
        )
        self._draw_label(self.LABELS[state], offset_y + 56, color)

    def _draw_label(
        self,
        text: str,
        y: int,
        color: tuple[int, int, int],
    ) -> None:
        width, height = measure_text(text)
        x = (self.renderer.width - width) // 2

        if (
            x >= 0
            and y >= 0
            and y + height <= self.renderer.height
        ):
            draw_text(self.renderer, x, y, text, color)

    def _make_frame(self, state: AgentState, phase: int) -> list:
        image = Image.new("RGB", (64, 64), self.bg_rgb)
        draw = ImageDraw.Draw(image)

        color = self.COLORS[state]
        dark = (20, 25, 35)
        metal = (175, 190, 210)
        eyes = (100, 220, 255)

        # Traffic light: red = Working, orange = Waiting, green = Done.
        draw.rounded_rectangle(
            (51, 16, 62, 48),
            radius=3,
            fill=(25, 28, 35),
            outline=(65, 70, 80),
        )
        for light_state, y in (
            (AgentState.WORKING, 23),
            (AgentState.WAITING, 32),
            (AgentState.DONE, 41),
        ):
            light_color = (
                self.COLORS[light_state]
                if state == light_state
                else (40, 40, 45)
            )
            draw.ellipse((54, y - 3, 59, y + 2), fill=light_color)

        # Robot mascot.
        bob = phase if state == AgentState.WORKING else 0
        draw.line((24, 22 + bob, 24, 25 + bob), fill=metal)
        draw.rectangle((23, 20 + bob, 25, 22 + bob), fill=color)
        draw.rounded_rectangle(
            (13, 25 + bob, 35, 39 + bob),
            radius=3,
            fill=metal,
        )
        draw.rectangle((16, 28 + bob, 32, 35 + bob), fill=dark)
        draw.rectangle((18, 30 + bob, 20, 32 + bob), fill=eyes)
        draw.rectangle((28, 30 + bob, 30, 32 + bob), fill=eyes)
        draw.line((22, 37 + bob, 26, 37 + bob), fill=dark)

        draw.rounded_rectangle(
            (17, 41, 31, 49), radius=2, fill=metal
        )
        draw.rectangle((22, 43, 26, 46), fill=color)
        draw.line((20, 50, 20, 53), fill=metal, width=2)
        draw.line((28, 50, 28, 53), fill=metal, width=2)

        if state == AgentState.DONE:
            # Raised arms and a small celebration sparkle.
            draw.line((16, 43, 8, 34), fill=metal, width=2)
            draw.line((32, 43, 40, 34), fill=metal, width=2)
            sx = 10 if phase else 39
            draw.line((sx - 2, 17, sx + 2, 17), fill=color)
            draw.line((sx, 15, sx, 19), fill=color)

        elif state == AgentState.WORKING:
            # Raised tool arm and a wrench.
            draw.line((16, 43, 10, 48), fill=metal, width=2)
            draw.line((32, 43, 40, 38 + bob), fill=metal, width=2)
            draw.line(
                (40, 40 + bob, 40, 31 + bob),
                fill=color,
                width=2,
            )
            draw.arc(
                (36, 25 + bob, 44, 33 + bob),
                start=0,
                end=180,
                fill=color,
                width=2,
            )

        else:
            draw.line((16, 43, 11, 49), fill=metal, width=2)
            draw.line((32, 43, 37, 49), fill=metal, width=2)

        if state == AgentState.WAITING:
            # Speech bubble indicating that user input is required.
            draw.rounded_rectangle(
                (29, 12, 47, 21),
                radius=2,
                outline=color,
            )
            draw.line((33, 21, 31, 24), fill=color)
            for index in range(2 + phase):
                x = 33 + index * 4
                draw.point((x, 16), fill=color)

        return list(image.getdata())