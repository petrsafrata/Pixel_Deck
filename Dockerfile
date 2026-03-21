# Base image with Python 3.13 on Debian Bookworm
FROM python:3.13-bookworm

# Environment configuration
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV TZ=Europe/Prague
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/opt/rpi-rgb-led-matrix/bindings/python/samples

# Install system dependencies required for building and running rpi-rgb-led-matrix and related libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    make \
    g++ \
    gcc \
    pkg-config \
    python3-dev \
    python-dev-is-python3 \
    cython3 \
    cmake \
    ninja-build \
    tzdata \
    libjpeg-dev \
    libpng-dev \
    libfreetype6-dev \
    libasound2-dev \
    libportmidi-dev \
    libsdl2-dev \
    libsdl2-image-dev \
    libsdl2-mixer-dev \
    libsdl2-ttf-dev \
    && rm -rf /var/lib/apt/lists/*

# Clone the official RGB matrix library
WORKDIR /opt
RUN git clone --depth=1 https://github.com/hzeller/rpi-rgb-led-matrix.git

WORKDIR /opt/rpi-rgb-led-matrix

# Build the native C++ library (required for hardware control)
RUN make -j"$(nproc)" all

# Apply patch to disable unsafe Pillow fast-path and ensure compatibility in Docker environment
# Replace Pillow shim implementation with a safe stub
RUN python3 - <<'PY'
from pathlib import Path

root = Path("/opt/rpi-rgb-led-matrix")

pillow_c = root / "bindings/python/rgbmatrix/shims/pillow.c"
pillow_c.write_text(
    '#include "pillow.h"\n'
    'int** get_image32(void* im) { (void)im; return 0; }\n',
    encoding="utf-8"
)

core_pyx = root / "bindings/python/rgbmatrix/core.pyx"
txt = core_pyx.read_text(encoding="utf-8")

txt = txt.replace(
    "def SetImage(self, image, int offset_x = 0, int offset_y = 0, unsafe=True):",
    "def SetImage(self, image, int offset_x = 0, int offset_y = 0, unsafe=False):"
)

start = txt.index("        if unsafe:")
end = txt.index("        else:", start)

txt = (
    txt[:start]
    + '        if unsafe:\n'
      '            raise Exception("unsafe Pillow fast-path is disabled in this Docker build")\n'
    + txt[end:]
)

core_pyx.write_text(txt, encoding="utf-8")
PY

# Install the Python bindings for the RGB matrix library
RUN python3 -m pip install --no-cache-dir .
RUN python3 -c "import rgbmatrix.core; from rgbmatrix import RGBMatrix, RGBMatrixOptions; print('rgbmatrix.core OK')"

# Application setup
WORKDIR /app

# Install Python dependencies
COPY requirements.txt /app/requirements.txt
RUN python3 -m pip install --no-cache-dir -r /app/requirements.txt

# Copy the rest of the application source code
COPY . /app

# Default command to run the application
CMD ["python3", "main.py"]