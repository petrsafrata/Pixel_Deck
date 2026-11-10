from __future__ import annotations

import logging
import os
import re
import tempfile
from collections.abc import MutableMapping
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap

from src.web.field_spec import (
    FIELD_TYPE_BOOLEAN,
    FIELD_TYPE_COLOR,
    FIELD_TYPE_IMAGE_GALLERY,
    FIELD_TYPE_NUMBER,
    FIELD_TYPE_SELECT,
    FIELD_TYPE_STRING_LIST,
    FIELD_TYPE_TEXT,
    FieldOption,
    FieldSpec,
)

CONFIG_BACKUP_SUFFIX = ".bak"

HIDDEN_DISPLAY_KEYS = {
    "hardware_mapping",
    "rows",
    "cols",
    "chain_length",
    "parallel",
    "pwm_bits",
    "gpio_slowdown",
    "pwm_lsb_nanoseconds",
    "scan_mode",
    "row_address_type",
    "multiplexing",
    "panel_type",
    "led_rgb_sequence",
    "pixel_mapper_config",
    "show_refresh_rate",
    "limit_refresh_rate_hz",
    "disable_hardware_pulsing",
}

COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")

@dataclass
class EditableField:
    key: str
    label: str
    description: str
    field_type: str
    group: str
    value: Any
    unit: str | None = None
    minimum: float | None = None
    maximum: float | None = None
    step: float | None = None
    placeholder: str | None = None
    options: list[FieldOption] = field(default_factory=list)
    rows: int | None = None
    multiline: bool = False
    required: bool = False
    numeric_type: str | None = None


@dataclass
class SceneFieldGroup:
    key: str
    label: str
    description: str | None
    fields: list[EditableField] = field(default_factory=list)


@dataclass
class SceneSchema:
    name: str
    label: str
    description: str | None
    enabled: bool
    groups: list[SceneFieldGroup] = field(default_factory=list)
    capabilities: dict = field(default_factory=dict)


@dataclass
class SceneMeta:
    """All metadata for a single scene: display info, capabilities, and editable field specs."""
    label: str
    description: str | None = None
    capabilities: dict = field(default_factory=dict)
    field_specs: tuple[FieldSpec, ...] = ()


def _create_yaml() -> YAML:
    yaml = YAML(typ="rt")
    yaml.preserve_quotes = True
    yaml.width = 4096
    yaml.indent(mapping=2, sequence=4, offset=2)
    return yaml


def _build_scene_metadata() -> dict[str, SceneMeta]:
    """Build SCENE_METADATA from scene class declarations.

    Lazy imports break the circular-import risk: scene classes import
    FieldSpec from field_spec.py (not from config_editor), so there is
    no import cycle.

    When adding a new scene the following steps are needed:
      1. Create the scene class with scene_name / scene_label / scene_field_specs set.
      2. Register it in main.py:  reg.register(MyScene)
      3. Import and add MyScene to the scene_classes list below.
      4. Add the scene section to config.yml.
    """
    from src.scenes.bitcoin import BitcoinScene
    from src.scenes.calendar import CalendarScene
    from src.scenes.clock import ClockScene
    from src.scenes.day_state import DayStateScene
    from src.scenes.f1_calendar import F1CalendarScene
    from src.scenes.images_random import ImagesRandomScene
    from src.scenes.sp500 import SP500Scene
    from src.scenes.text import TextScene
    from src.scenes.weather import WeatherScene

    scene_classes = [
        BitcoinScene,
        CalendarScene,
        ClockScene,
        DayStateScene,
        F1CalendarScene,
        ImagesRandomScene,
        SP500Scene,
        TextScene,
        WeatherScene,
    ]
    return {
        cls.scene_name: SceneMeta(
            label=cls.scene_label or cls.scene_name.replace("_", " ").title(),
            description=cls.scene_description,
            capabilities=dict(cls.scene_capabilities),
            field_specs=cls.scene_field_specs,
        )
        for cls in scene_classes
        if cls.scene_name
    }


# Single source of scene metadata, derived from the scene class declarations.
# To add a new scene: register it in main.py and declare scene_name / scene_label /
# scene_field_specs on the class – SCENE_METADATA is rebuilt automatically.
SCENE_METADATA: dict[str, SceneMeta] = _build_scene_metadata()


def _scene_label(scene_name: str) -> str:
    meta = SCENE_METADATA.get(scene_name)
    return meta.label if meta else scene_name.replace("_", " ").title()


def _scene_description(scene_name: str) -> str | None:
    meta = SCENE_METADATA.get(scene_name)
    return meta.description if meta else None


def _to_field_schema(spec: FieldSpec, scene_cfg: dict[str, Any]) -> EditableField:
    return EditableField(
        key=spec.key,
        label=spec.label,
        description=spec.description,
        field_type=spec.field_type,
        group=spec.group,
        value=get_by_path(scene_cfg, spec.key),
        unit=spec.unit,
        minimum=spec.minimum,
        maximum=spec.maximum,
        step=spec.step,
        placeholder=spec.placeholder,
        options=list(spec.options),
        rows=spec.rows,
        multiline=spec.multiline,
        required=spec.required,
        numeric_type=spec.numeric_type,
    )


def load_config_dict(path: str | Path) -> dict:
    yaml = _create_yaml()
    with open(path, "r", encoding="utf-8") as handle:
        return yaml.load(handle) or {}


def save_config_dict(path: str | Path, data: dict) -> None:
    path = Path(path)
    if not isinstance(data, MutableMapping):
        raise ValueError("Config data must be a mapping")

    backup_path = path.with_suffix(path.suffix + CONFIG_BACKUP_SUFFIX)
    if path.exists():
        backup_path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

    yaml = _create_yaml()
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=str(path.parent),
            prefix=f"{path.stem}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            tmp_path = Path(handle.name)
            yaml.dump(data, handle)

        os.replace(tmp_path, path)
    finally:
        if tmp_path is not None and tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


def sanitize_config(data: dict) -> dict:
    cleaned = deepcopy(data)
    display = cleaned.get("display") or {}
    for key in list(display.keys()):
        if key in HIDDEN_DISPLAY_KEYS:
            display.pop(key, None)
    cleaned["display"] = display

    web_cfg = cleaned.get("web") or {}
    if "api_token" in web_cfg:
        web_cfg["api_token"] = "***"
    cleaned["web"] = web_cfg

    return cleaned


def get_scene_field_specs(scene_name: str) -> tuple[FieldSpec, ...]:
    meta = SCENE_METADATA.get(scene_name)
    return meta.field_specs if meta else ()


def get_editable_fields(scene_name: str, scene_cfg: dict) -> list[EditableField]:
    return [_to_field_schema(spec, scene_cfg) for spec in get_scene_field_specs(scene_name)]


def get_scene_schema(scene_name: str, scene_cfg: dict) -> SceneSchema:
    fields = get_editable_fields(scene_name, scene_cfg)
    specs = get_scene_field_specs(scene_name)
    grouped: dict[str, list[EditableField]] = {}
    group_labels: dict[str, str] = {}
    group_descriptions: dict[str, str | None] = {}
    for field_item, spec in zip(fields, specs, strict=True):
        grouped.setdefault(spec.group, []).append(field_item)
        group_labels.setdefault(spec.group, spec.group)
        group_descriptions.setdefault(spec.group, None)

    groups = [
        SceneFieldGroup(key=group_key, label=group_labels[group_key], description=group_descriptions[group_key], fields=items)
        for group_key, items in grouped.items()
    ]

    meta = SCENE_METADATA.get(scene_name)
    return SceneSchema(
        name=scene_name,
        label=_scene_label(scene_name),
        description=_scene_description(scene_name),
        enabled=bool(scene_cfg.get("enabled", False)),
        groups=groups,
        capabilities=dict(meta.capabilities) if meta else {},
    )


def get_scene_schemas(data: dict, registered_scenes: frozenset[str] | None = None) -> list[SceneSchema]:
    scenes = data.get("scenes", {}) or {}
    result = []
    for name, scene_cfg in scenes.items():
        if registered_scenes is not None and name not in registered_scenes:
            continue
        result.append(get_scene_schema(name, scene_cfg or {}))
    return result


def is_image_referenced(data: dict, filename: str) -> tuple[bool, str | None]:
    """Return (True, scene_name) if filename is referenced in any scene's image-gallery field.

    Checks all scenes that declare supportsAssets capability, so this generalizes
    to future asset-capable scenes without hardcoding scene names.
    """
    for scene_name, meta in SCENE_METADATA.items():
        if not meta.capabilities.get("supportsAssets"):
            continue
        scene_cfg = (data.get("scenes") or {}).get(scene_name, {})
        for spec in meta.field_specs:
            if spec.field_type == FIELD_TYPE_IMAGE_GALLERY:
                files = get_by_path(scene_cfg, spec.key) or []
                if any(Path(f).name == filename for f in files):
                    return True, scene_name
    return False, None


def apply_scene_update(data: dict, scene_name: str, update: dict) -> None:
    scenes = data.setdefault("scenes", {})
    if scene_name not in scenes:
        raise ValueError(f"Unknown scene: {scene_name}")

    scene_cfg = scenes[scene_name]
    specs = {spec.key: spec for spec in get_scene_field_specs(scene_name)}

    for key, value in update.items():
        if value is None:
            continue
        if key not in specs:
            raise ValueError(f"Field not editable: {key}")
        try:
            normalized = normalize_value(specs[key], value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid value for '{key}': {exc}") from exc
        set_by_path(scene_cfg, key, normalized)


def apply_scene_order(data: dict, order: list[str]) -> None:
    scenes = data.get("scenes", {})
    if not scenes:
        raise ValueError("No scenes defined")

    unknown = [name for name in order if name not in scenes]
    if unknown:
        raise ValueError(f"Unknown scenes in order: {unknown}")

    app_cfg = data.setdefault("app", {})
    app_cfg["scene_order"] = list(order)


def set_display_output_enabled(data: dict, enabled: bool) -> None:
    display_cfg = data.setdefault("display", {})
    display_cfg["output_enabled"] = bool(enabled)


def set_app_log_level(data: dict, level: str) -> None:
    normalized = str(level).upper()
    if not normalized or not hasattr(logging, normalized):
        raise ValueError(f"Unknown log level: {level}")
    app_cfg = data.setdefault("app", {})
    app_cfg["log_level"] = normalized


def set_active_scene(data: dict, scene_name: str) -> None:
    scenes = data.get("scenes", {})
    if scene_name not in scenes:
        raise ValueError(f"Unknown scene: {scene_name}")
    app_cfg = data.setdefault("app", {})
    app_cfg["active_scene"] = str(scene_name)


def get_by_path(data: dict, path: str) -> Any:
    current: Any = data
    for part in path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def set_by_path(data: dict, path: str, value: Any) -> None:
    parts = path.split(".")
    current = data
    for part in parts[:-1]:
        if part not in current or not isinstance(current[part], dict):
            current[part] = CommentedMap() if isinstance(current, CommentedMap) else {}
        current = current[part]
    current[parts[-1]] = value


def normalize_value(spec: FieldSpec, value: Any) -> Any:
    if value is None:
        raise ValueError("Value is required")

    if spec.field_type == FIELD_TYPE_TEXT:
        return str(value)

    if spec.field_type == FIELD_TYPE_NUMBER:
        normalized: Any
        if spec.numeric_type == "float":
            normalized = float(value)
        else:
            normalized = int(value)
        if spec.minimum is not None and normalized < spec.minimum:
            raise ValueError(f"must be at least {spec.minimum}")
        if spec.maximum is not None and normalized > spec.maximum:
            raise ValueError(f"must be at most {spec.maximum}")
        return normalized

    if spec.field_type == FIELD_TYPE_BOOLEAN:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in {"1", "true", "yes", "on"}:
                return True
            if lowered in {"0", "false", "no", "off"}:
                return False
            raise ValueError("expected a boolean value")
        return bool(value)

    if spec.field_type == FIELD_TYPE_COLOR:
        if not isinstance(value, str) or not COLOR_RE.match(value.strip()):
            raise ValueError("expected a color in #RRGGBB format")
        return value.strip()

    if spec.field_type == FIELD_TYPE_SELECT:
        normalized = str(value)
        allowed = {str(option.value) for option in spec.options}
        if allowed and normalized not in allowed:
            raise ValueError(f"must be one of {sorted(allowed)}")
        return normalized

    if spec.field_type in (FIELD_TYPE_STRING_LIST, FIELD_TYPE_IMAGE_GALLERY):
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            items = [line.strip() for line in value.splitlines()]
            return [item for item in items if item]
        raise ValueError("expected a list or newline-separated string")

    raise ValueError(f"Unsupported field type: {spec.field_type}")