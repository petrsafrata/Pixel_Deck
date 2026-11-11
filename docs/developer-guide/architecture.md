# Architecture

```text
Pixel Deck
│
├── Scene System
│   ├── BaseScene
│   └── Scene implementations
├── Renderer
│   ├── WindowRenderer
│   └── MatrixRenderer
└── Web Control Center
    ├── FastAPI backend
    └── React frontend
```

## Scene system

Every scene inherits from `BaseScene`. It provides lifecycle management, shared configuration properties, renderer access, and scene metadata.

## Renderer

`WindowRenderer` supports local development and `MatrixRenderer` renders on the physical RGB LED matrix.

## Web Control Center

FastAPI exposes runtime state and configuration operations while React provides the browser interface.

## Scene lifecycle

```python
class ExampleScene(BaseScene):
    def on_enter(self) -> None:
        super().on_enter()

    def update(self, dt: float) -> None:
        ...

    def on_exit(self) -> None:
        super().on_exit()
```

- `on_enter()` runs once when activated.
- `update(dt)` runs repeatedly and is required for concrete scenes.
- `on_exit()` runs once when deactivated.

`BaseScene` exposes `fps`, `duration_s`, `background`, and `bg_rgb`.

Scene metadata can include `scene_name`, `scene_label`, `scene_description`, `scene_capabilities`, and `scene_field_specs`.
