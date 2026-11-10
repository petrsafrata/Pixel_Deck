from __future__ import annotations

import logging
import os
from io import BytesIO
from pathlib import Path

from PIL import Image

_log = logging.getLogger(__name__)


ALLOWED_IMAGE_EXTS = {".png", ".jpg", ".jpeg"}
_CANVAS_REL = Path("assets") / "images" / "canvas"


def get_upload_dir(project_root: Path) -> Path:
    return project_root / "assets" / "images" / "canvas"


def list_uploaded_images(upload_dir: Path) -> list[dict]:
    """
    Scan the upload directory and return metadata for all supported images.

    The returned structure is used by the Web UI to populate the
    Image Gallery component.
    """
    upload_dir.mkdir(parents=True, exist_ok=True)
    items = []
    for path in sorted(upload_dir.iterdir()):
        if not path.is_file():
            continue
        if path.suffix.lower() not in ALLOWED_IMAGE_EXTS:
            continue
        width, height = _get_image_dimensions(path)
        items.append(
            {
                "name": path.name,
                "path": str(_CANVAS_REL / path.name),
                "url": f"/api/assets/images/{path.name}",
                "width": width,
                "height": height,
                "sizeBytes": path.stat().st_size,
            }
        )
    return items


def _get_image_dimensions(path: Path) -> tuple[int, int]:
    try:
        with Image.open(path) as img:
            return img.width, img.height
    except Exception:
        _log.warning("Could not read image dimensions for %s", path)
        return 0, 0


def save_uploaded_image(
    upload_dir: Path,
    filename: str,
    content: bytes,
    resize: bool = False,
    target_size: int = 64,
) -> Path:
    """
    Validate and save an uploaded image.

    Optionally resizes the image to a square of the requested size before
    saving it. When resizing is enabled, the image is always saved as PNG
    to preserve quality and transparency.

    Raises:
        ValueError:
            Unsupported file type.

        FileExistsError:
            A file with the same name already exists.
    """
    upload_dir.mkdir(parents=True, exist_ok=True)
    safe_name = os.path.basename(filename)
    ext = Path(safe_name).suffix.lower()
    if ext not in ALLOWED_IMAGE_EXTS:
        raise ValueError("Unsupported file type")

    dest = upload_dir / safe_name
    if dest.exists():
        raise FileExistsError("File already exists")

    with Image.open(BytesIO(content)) as img:
        img = img.convert("RGBA")
        if resize:
            img = img.resize((target_size, target_size), Image.LANCZOS)
            dest = dest.with_suffix(".png")
            img.save(dest, format="PNG")
            return dest
        img.save(dest)

    return dest


def delete_uploaded_image(upload_dir: Path, name: str) -> Path:
    safe_name = os.path.basename(name)
    target = upload_dir / safe_name
    if not target.exists():
        raise FileNotFoundError("Image not found")
    target.unlink()
    return target
