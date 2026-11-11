# Raspberry Pi Deployment

Pixel Deck is designed to run on Raspberry Pi using Docker Compose.

## Requirements

- Raspberry Pi 4 or newer
- Compatible HUB75 RGB LED matrix
- Correct hardware mapping
- Docker and Docker Compose

## Deploy

```bash
chmod +x deploy.sh
./deploy.sh
```

The deployment script prepares writable runtime directories and permissions, builds the application image, and starts Pixel Deck.

When the Web Control Center is enabled and port 8080 is exposed, open:

```text
http://<raspberry-pi-ip>:8080
```

## Useful commands

| Command | Description |
|---|---|
| `docker compose ps` | Show container status |
| `docker compose logs -f` | Follow logs |
| `docker compose stop` | Stop Pixel Deck |
| `docker compose start` | Start Pixel Deck |
| `docker compose restart` | Restart Pixel Deck |
| `docker compose down` | Stop and remove the container |
| `docker compose up -d` | Create and start the container |
| `./deploy.sh` | Rebuild and redeploy |
