#!/bin/bash

# ============================================================
# Pixel Deck - Raspberry Pi deployment script
#
# Prepares writable runtime directories and deploys Pixel Deck
# using Docker Compose.
#
# The RGB matrix driver drops application privileges after
# hardware initialization. The application therefore needs
# write access to directories modified at runtime:
#
#   config/ - Web UI configuration updates and backups
#   assets/ - image uploads and other writable assets
#
# Usage:
#   chmod +x deploy.sh
#   ./deploy.sh
# ============================================================

set -e

RUNTIME_UID=1
RUNTIME_GID=1

CONFIG_DIR="./config"
ASSETS_DIR="./assets"

echo "========================================"
echo " Pixel Deck deployment"
echo "========================================"

# ------------------------------------------------------------
# Validate required directories
# ------------------------------------------------------------

if [ ! -d "$CONFIG_DIR" ]; then
    echo "ERROR: Configuration directory '$CONFIG_DIR' does not exist."
    exit 1
fi

if [ ! -f "$CONFIG_DIR/config.yml" ]; then
    echo "ERROR: Configuration file '$CONFIG_DIR/config.yml' does not exist."
    exit 1
fi

if [ ! -d "$ASSETS_DIR" ]; then
    echo "ERROR: Assets directory '$ASSETS_DIR' does not exist."
    exit 1
fi


# ------------------------------------------------------------
# Configure runtime permissions
#
# Pixel Deck starts with elevated privileges required by the
# RGB matrix driver. The driver subsequently drops privileges.
#
# Writable directories therefore need to be owned by the
# resulting runtime UID/GID.
# ------------------------------------------------------------

echo
echo "Configuring runtime permissions..."

sudo chown -R "$RUNTIME_UID:$RUNTIME_GID" "$CONFIG_DIR"
sudo chown -R "$RUNTIME_UID:$RUNTIME_GID" "$ASSETS_DIR"

echo "Runtime permissions configured."


# ------------------------------------------------------------
# Build application image
# ------------------------------------------------------------

echo
echo "Building Pixel Deck..."

docker compose build


# ------------------------------------------------------------
# Start / recreate container
# ------------------------------------------------------------

echo
echo "Starting Pixel Deck..."

docker compose up -d


# ------------------------------------------------------------
# Show deployment status
# ------------------------------------------------------------

echo
echo "========================================"
echo " Pixel Deck deployment completed"
echo "========================================"
echo

docker compose ps

echo
echo "Useful commands:"
echo
printf "%-32s %s\n" "Command" "Description"
printf "%-32s %s\n" "------------------------------" "---------------------------------------------"
printf "%-32s %s\n" "docker compose logs -f" "Follow application logs"
printf "%-32s %s\n" "docker compose ps" "Show container status"
printf "%-32s %s\n" "docker compose stop" "Stop Pixel Deck"
printf "%-32s %s\n" "docker compose start" "Start stopped Pixel Deck"
printf "%-32s %s\n" "docker compose restart" "Restart Pixel Deck"
printf "%-32s %s\n" "docker compose down" "Stop and remove the container"
printf "%-32s %s\n" "docker compose up -d" "Create/start Pixel Deck"
printf "%-32s %s\n" "./deploy.sh" "Rebuild and redeploy Pixel Deck"
echo