"""
Shared field specification models used by Pixel Deck scenes and the Web UI.

This module defines the metadata used to describe editable scene configuration.
Each editable configuration value is represented by a `FieldSpec`, which contains
all information required by the Web UI to automatically generate configuration
forms.

The field specifications are shared between scene implementations and the web
configuration layer, making the frontend completely schema-driven rather than
scene-specific.

The metadata describe:

- which configuration value is editable (`key`),
- how it should be presented (`label`, `description`, `group`),
- which editor should be used (`field_type`),
- optional validation rules (min/max/step),
- optional units and placeholders,
- selectable options for dropdown fields.

Common configuration fields such as duration, refresh interval and colors are
defined once in this module and reused across multiple scenes, ensuring a
consistent editing experience throughout the application.

Adding a new editable field to a scene typically consists of:

1. Defining a new `FieldSpec` (or reusing an existing shared one).
2. Including it in the scene's `_FIELD_SPECS` collection.
3. Exposing the scene metadata.

No frontend changes are required, as the React UI renders configuration forms
dynamically from these metadata.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

FIELD_TYPE_BOOLEAN = "boolean"
FIELD_TYPE_NUMBER = "number"
FIELD_TYPE_COLOR = "color"
FIELD_TYPE_TEXT = "text"
FIELD_TYPE_SELECT = "select"
FIELD_TYPE_STRING_LIST = "string_list"
FIELD_TYPE_IMAGE_GALLERY = "image-gallery"


@dataclass(frozen=True)
class FieldOption:
    label: str
    value: Any


@dataclass(frozen=True)
class FieldSpec:
    key: str
    label: str
    description: str
    field_type: str
    group: str
    unit: str | None = None
    minimum: float | None = None
    maximum: float | None = None
    step: float | None = None
    placeholder: str | None = None
    options: tuple[FieldOption, ...] = ()
    rows: int | None = None
    multiline: bool = False
    required: bool = False
    numeric_type: str | None = None


def build_field_spec(
    key: str,
    label: str,
    description: str,
    field_type: str,
    group: str,
    **kwargs: Any,
) -> FieldSpec:
    """Convenience constructor – avoids repeating positional args."""
    return FieldSpec(
        key=key,
        label=label,
        description=description,
        field_type=field_type,
        group=group,
        **kwargs,
    )


# ---------------------------------------------------------------------------
# Shared field specs reused across multiple scenes
# ---------------------------------------------------------------------------

DURATION_FIELD = build_field_spec(
    "duration_s",
    "Duration",
    "How long the scene stays visible.",
    FIELD_TYPE_NUMBER,
    "General",
    unit="seconds",
    minimum=1,
    maximum=3600,
    step=1,
    numeric_type="int",
)

REFRESH_FIELD = build_field_spec(
    "refresh_s",
    "Refresh interval",
    "How often the scene refreshes its data.",
    FIELD_TYPE_NUMBER,
    "General",
    unit="seconds",
    minimum=1,
    maximum=86400,
    step=1,
    numeric_type="int",
)

FPS_FIELD = build_field_spec(
    "fps",
    "Frame rate",
    "How many frames per second the scene renders.",
    FIELD_TYPE_NUMBER,
    "General",
    unit="fps",
    minimum=1,
    maximum=120,
    step=1,
    numeric_type="int",
)

BACKGROUND_FIELD = build_field_spec(
    "background",
    "Background color",
    "Base background color used by the scene.",
    FIELD_TYPE_COLOR,
    "Appearance",
)

PRIMARY_COLOR_FIELD = build_field_spec(
    "font.primary_color",
    "Primary text color",
    "Main text color used by the scene.",
    FIELD_TYPE_COLOR,
    "Appearance",
)

SECONDARY_COLOR_FIELD = build_field_spec(
    "font.secondary_color",
    "Secondary text color",
    "Accent text color used by the scene.",
    FIELD_TYPE_COLOR,
    "Appearance",
)



