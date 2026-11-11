# Creating a Custom Scene

Create a module under `src/scenes/`, for example `my_scene.py`.

```python
from src.scenes.base_scene import BaseScene

class MyScene(BaseScene):
    scene_name = "my_scene"
    scene_label = "My Scene"
    scene_description = "Example custom scene."

    def update(self, dt: float) -> None:
        if self.renderer is None:
            return
        ...
```

Register the scene in the application's `SceneRegistry` using the same key as its configuration.

Add configuration:

```yaml
scenes:
  my_scene:
    enabled: true
    duration_s: 10
```

Add it to rotation:

```yaml
app:
  scene_order:
    - "clock"
    - "my_scene"
```

To expose editable settings in the Web Control Center, define `scene_field_specs`. See [Web Configuration Schema](field-spec.md).

> The current repository implementation should remain the source of truth for the exact registry construction location.
