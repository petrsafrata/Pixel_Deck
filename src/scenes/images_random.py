from __future__ import annotations

import logging
import random
from typing import List, Optional

from src.scenes.base_scene import BaseScene
from src.gfx.draw import draw_image_rgba
from src.gfx.image_loader import load_rgba_pixels
from src.web.field_spec import (
    BACKGROUND_FIELD,
    DURATION_FIELD,
    FIELD_TYPE_BOOLEAN,
    FIELD_TYPE_IMAGE_GALLERY,
    FIELD_TYPE_NUMBER,
    FIELD_TYPE_SELECT,
    FPS_FIELD,
    FieldOption,
    FieldSpec,
    build_field_spec,
)

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------
# Editable configuration fields exposed by the Web UI.
#
# Each scene declares a tuple of FieldSpec objects describing which
# configuration values can be edited from the frontend.
#
# These metadata are consumed by the schema-driven Web UI to generate
# the Scene Settings panel automatically. Any field defined here will
# be rendered in the frontend without additional React changes.
#
# Common fields (duration, colors, refresh interval, etc.) are reused
# across multiple scenes, while scene-specific fields are defined
# locally using build_field_spec().
# -------------------------------------------------------------------------
_FIELD_SPECS: tuple[FieldSpec, ...] = (
    DURATION_FIELD,
    FPS_FIELD,
    BACKGROUND_FIELD,
    build_field_spec(
        "images.mode",
        "Image order",
        "How the next image is selected.",
        FIELD_TYPE_SELECT,
        "Image settings",
        options=(
            FieldOption(label="Random", value="random"),
            FieldOption(label="Ordered", value="ordered"),
        ),
    ),
    build_field_spec(
        "images.avoid_repeat",
        "Avoid repeated images",
        "Skip the most recently shown image when possible.",
        FIELD_TYPE_BOOLEAN,
        "Image settings",
    ),
    build_field_spec(
        "images.size",
        "Image size",
        "Square image size used for rendering.",
        FIELD_TYPE_NUMBER,
        "Image settings",
        unit="px",
        minimum=1,
        maximum=512,
        step=1,
        numeric_type="int",
    ),
    build_field_spec(
        "images.files",
        "Image gallery",
        "Select images to include in this scene.",
        FIELD_TYPE_IMAGE_GALLERY,
        "Image gallery",
        multiline=True,
        rows=6,
    ),
)


class ImagesRandomScene(BaseScene):
    scene_name = "images"
    scene_label = "Images"
    scene_description = "Cycle through uploaded or bundled images."
    scene_capabilities = {"supportsAssets": True, "supportsImageGallery": True}
    scene_field_specs = _FIELD_SPECS
    """
    Standardized scene structure:
      - on_enter(): init defaults -> load config -> load assets -> finalize
      - on_exit(): cleanup
      - update(): render only
    """

    def on_enter(self) -> None:
        super().on_enter()
        self._init_state_defaults()
        self._load_config()
        self._load_assets()
        logger.info(
            "%s entered (mode=%s, avoid_repeat=%s, size=%s, files=%d, selected=%s)",
            self.__class__.__name__,
            self.mode,
            self.avoid_repeat,
            self.size,
            len(self.files),
            self._path,
        )

    def on_exit(self) -> None:
        # no external resources here, but keep the hook for symmetry/standardization.
        logger.info("%s exited", self.__class__.__name__)
        super().on_exit()

    def update(self, dt: float) -> None:
        if self.renderer is None or self._img is None:
            return
        # Entire display from (0,0)
        draw_image_rgba(self.renderer, 0, 0, self._img, self._w, self._h)

    # --------------------
    # Internal helpers
    # --------------------
    def _init_state_defaults(self) -> None:
        self.mode: str = "random"
        self.avoid_repeat: bool = True
        self.size: int = 64
        self.files: List[str] = []

        self._img: Optional[list[int]] = None
        self._w: int = 0
        self._h: int = 0
        self._path: Optional[str] = None

    def _load_config(self) -> None:
        cfg = (self.config.get("images") or {})

        self.mode = str(cfg.get("mode", "random")).lower()
        self.avoid_repeat = bool(cfg.get("avoid_repeat", True))
        self.size = int(cfg.get("size", 64))
        self.files = cfg.get("files", []) or []

        if not isinstance(self.files, list):
            logger.warning(
                "%s: invalid config (images.files must be list)",
                self.__class__.__name__,
            )
            self.files = []

        if not self.files:
            logger.warning(
                "%s: no images configured (expected scenes.<scene>.images.files)",
                self.__class__.__name__,
            )

    def _load_assets(self) -> None:
        if not self.files:
            self._img, self._w, self._h, self._path = None, 0, 0, None
            return

        path = self._pick_image_path(self.files)

        try:
            img, w, h = load_rgba_pixels(path, self.size)
            self._img, self._w, self._h = img, w, h
            self._path = path
        except Exception as e:
            logger.warning(
                "%s: failed to load '%s': %s",
                self.__class__.__name__,
                path,
                e,
                exc_info=True,
            )
            self._img, self._w, self._h, self._path = None, 0, 0, None

    def _pick_image_path(self, files: List[str]) -> str:
        candidates = list(files)

        # avoid repeating last image across scene switches via renderer attribute
        last = getattr(self.renderer, "_last_random_image", None) if self.renderer else None
        if self.avoid_repeat and last in candidates and len(candidates) > 1:
            candidates.remove(last)

        # use instance RNG if BaseScene provides it, otherwise fallback
        rng = getattr(self, "rng", None)
        if rng is None:
            chosen = random.choice(candidates)
        else:
            chosen = rng.choice(candidates)

        if self.renderer is not None:
            setattr(self.renderer, "_last_random_image", chosen)

        return chosen
