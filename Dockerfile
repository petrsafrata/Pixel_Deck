# ------------------------------------------------------------
# Stage 1: build rpi-rgb-led-matrix + python bindings
# ------------------------------------------------------------
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    make \
    g++ \
    python3-dev \
    pkg-config \
    libjpeg-dev \
    libpng-dev \
    ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Build hzeller/rpi-rgb-led-matrix
RUN git clone --depth 1 https://github.com/hzeller/rpi-rgb-led-matrix.git

WORKDIR /build/rpi-rgb-led-matrix

# Build core library
RUN make -j"$(nproc)"

# Install python bindings into /install (we'll copy it to runtime image)
WORKDIR /build/rpi-rgb-led-matrix/bindings/python
RUN pip install --no-cache-dir --prefix=/install .


# ------------------------------------------------------------
# Stage 2: runtime
# ------------------------------------------------------------
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Minimal runtime deps (certs, tz)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    tzdata \
 && rm -rf /var/lib/apt/lists/*

# Copy rgbmatrix python package from builder
COPY --from=builder /install /usr/local

# Install app python deps
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy app
COPY . /app

# Default command (uprav dle toho jak spouštíš main)
CMD ["python", "main.py"]
