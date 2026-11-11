# ============================================================
# Stage 1 - Build the React frontend
#
# The Web UI is built separately using Node.js. Only the
# compiled static files are copied into the final image,
# keeping the runtime image small and free of Node.js.
# ============================================================
FROM node:20-alpine AS frontend-builder

WORKDIR /frontend

# Install frontend dependencies
COPY frontend/package*.json /frontend/
RUN npm ci

# Build the production frontend
COPY frontend /frontend
RUN npm run build


# ============================================================
# Stage 2 - Pixel Deck runtime image
#
# Uses the custom Pixel Deck base image which already contains:
#   - Python 3.13
#   - rpi-rgb-led-matrix
#   - Pillow compatibility patches
#   - All native system dependencies required for Raspberry Pi
#
# This keeps the application Dockerfile focused only on the
# Pixel Deck application itself.
# ============================================================
FROM ghcr.io/petrsafrata/pixel-deck-base:latest
LABEL author="petrsafrata"
LABEL description="Docker image for running the pixel-deck application on Raspberry Pi hardware. Based on a custom base image with Python 3.13 and rpi-rgb-led-matrix library pre-installed."

# Application setup
WORKDIR /app

# ------------------------------------------------------------
# Install Python dependencies
#
# Only the requirements file is copied first so Docker can
# cache this layer. Dependencies are reinstalled only when
# requirements.txt changes.
# ------------------------------------------------------------
COPY requirements.txt /app/requirements.txt
RUN python3 -m pip install --no-cache-dir -r /app/requirements.txt

# ------------------------------------------------------------
# Copy the Pixel Deck source code
# ------------------------------------------------------------
COPY . /app

# ------------------------------------------------------------
# Copy the compiled frontend from the build stage.
#
# The runtime image contains only the static production build,
# avoiding the need for Node.js in the final container.
# ------------------------------------------------------------
COPY --from=frontend-builder /frontend/dist /app/frontend/dist

# ------------------------------------------------------------
# Start the Pixel Deck application
# ------------------------------------------------------------
CMD ["python3", "main.py"]