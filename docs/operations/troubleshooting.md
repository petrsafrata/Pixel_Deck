# Troubleshooting

## Wrong colors

```yaml
led_rgb_sequence: "RGB"
brightness: 40
```

Verify the power supply as well; high brightness can expose power-related color issues.

## Flickering

```yaml
gpio_slowdown: 10
```

The project also uses `pwm_lsb_nanoseconds` tuning for affected panels.

## Distorted output

```yaml
rows: 64
cols: 64
```

Verify the E-line configuration where E → GPIO8 is required.

## Web UI cannot save configuration

Errors such as:

```text
PermissionError: [Errno 13] Permission denied
```

usually indicate that the mounted configuration directory is not writable by the runtime process.

Use:

```bash
./deploy.sh
```

and verify permissions on `config/` and `assets/`.

## Frontend static assets return 404

The production image must contain the compiled `frontend/dist` output. Rebuild after frontend changes:

```bash
./deploy.sh
```

## Known hardware considerations

- Some panels require an E-line fix.
- Undersized or poor-quality power supplies can cause instability.
- High brightness can require stronger panel/HAT power delivery.
