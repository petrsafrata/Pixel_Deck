# Scenes

Pixel Deck renders content through independent scenes.

| Scene | Description |
|---|---|
| `clock` | Digital clock |
| `calendar` | Date and calendar information |
| `weather` | Weather from Open-Meteo |
| `bitcoin` | Cryptocurrency data from CoinGecko |
| `sp500` | S&P 500 data from Stooq |
| `text` | Multi-line text |
| `images` | Configurable/random image gallery |
| `day_state` | Day-state information from Open-Meteo |
| `f1_calendar` | Upcoming Formula 1 race information |

## Rotation

```yaml
app:
  scene_order:
    - "clock"
    - "weather"
    - "images"
```

Scenes can also be enabled or disabled individually. All scenes inherit from `BaseScene`.
