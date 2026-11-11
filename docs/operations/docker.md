# Docker and Runtime Permissions

The Matrix renderer requires low-level Raspberry Pi hardware access. The current Compose setup therefore uses elevated container access and `/dev/mem`.

## Writable directories

The Web Control Center writes configuration and uploaded assets at runtime. These locations must be writable:

```text
/app/config
/app/assets
```

Configuration updates create backup and temporary files in the configuration directory. A writable mount of only `config.yml` is therefore insufficient for the current atomic-save approach.

`deploy.sh` prepares the required host-side directories and permissions.

## Build

The application Dockerfile uses a multi-stage build:

1. Node.js builds the React/Vite frontend.
2. The Pixel Deck runtime installs Python dependencies and source.
3. The compiled frontend is copied into the runtime image.

## Base image and Pillow

The Pixel Deck base image contains native dependencies and `rpi-rgb-led-matrix`. It also disables the library's unsafe Pillow fast path because it caused instability and rendering problems in the Docker environment.

The tradeoff is slightly lower performance in exchange for stable rendering.
