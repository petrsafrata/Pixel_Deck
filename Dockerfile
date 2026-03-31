# Base image with Python and necessary dependencies for running pixel-deck application.
FROM ghcr.io/petrsafrata/pixel-deck-base:1.0.0
LABEL author="petrsafrata"
LABEL description="Docker image for running the pixel-deck application on Raspberry Pi hardware. Based on a custom base image with Python 3.13 and rpi-rgb-led-matrix library pre-installed."

# Application setup
WORKDIR /app

# Install Python dependencies
COPY requirements.txt /app/requirements.txt
RUN python3 -m pip install --no-cache-dir -r /app/requirements.txt

# Copy the rest of the application source code
COPY . /app

# Default command to run the application
CMD ["python3", "main.py"]