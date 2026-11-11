# Configuration

`config/config.yml` is the central Pixel Deck configuration source.

Configuration can be managed through YAML or, for selected settings, through the Web Control Center. Web UI changes are persisted back to `config/config.yml`.

## Main sections

| Section | Purpose |
|---|---|
| `display` | Hardware and matrix settings |
| `scene_defaults` | Shared scene fallback values |
| `app` | Runtime behavior |
| `web` | Web Control Center and API |
| `scenes` | Individual scene configuration |

## Example

```yaml
scenes:
  clock:
    enabled: true
    duration_s: 5
    format: "%H:%M"
    layout:
      time:
        y: 22
        scale: 2
```

Common scene values include `duration_s`, `refresh_s`, `fps`, `background`, `font`, `layout`, and `data`. Exact settings depend on the scene.

## Resolution

1. `scene_defaults` provides shared fallbacks.
2. Scenes override the values they need.
3. Missing values fall back to shared defaults.
4. Scenes expose selected editable values through `FieldSpec`.
5. The Web Control Center generates controls from that metadata.
6. Valid UI changes are persisted to YAML.

## Web configuration

```yaml
web:
  enabled: true
  host: "0.0.0.0"
  port: 8080
  api_token: "CHANGE_ME"
  allow_restart: true
  allow_display_power_control: true
  allow_debug_logging: true
```

> **Important:** Change the default API token before exposing the Web Control Center on a network.
