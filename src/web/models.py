"""
Pydantic request and response models used by the Pixel Deck Web API.

This module defines the data contracts exchanged between the FastAPI backend
and the frontend control center. The models are responsible for validating
incoming requests, serializing API responses, and generating OpenAPI schema
documentation automatically.

The models cover:

- scene configuration updates,
- scene ordering,
- display power control,
- logging configuration,
- asset deletion,
- active scene changes,
- schema-driven scene field metadata,
- grouped scene configuration responses,
- log operation responses.

SceneFieldSchema, SceneFieldGroup, and SceneSchema form the metadata structure
used by the frontend to generate scene configuration forms dynamically. This
allows the Web UI to remain generic and avoids hardcoding configuration forms
for individual scenes.

All API endpoints should use these models instead of untyped dictionaries
wherever possible to keep frontend-backend communication explicit, validated,
and maintainable.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SceneUpdateRequest(BaseModel):
    enabled: Optional[bool] = None
    fields: Optional[Dict[str, Any]] = None


class SceneOrderRequest(BaseModel):
    order: List[str] = Field(default_factory=list)


class DisplayToggleRequest(BaseModel):
    enabled: bool


class LogLevelRequest(BaseModel):
    level: str


class AssetDeleteRequest(BaseModel):
    force: bool = False


class ConfigPatchRequest(BaseModel):
    active_scene: Optional[str] = None


class SceneFieldOption(BaseModel):
    label: str
    value: Any


class SceneFieldSchema(BaseModel):
    key: str
    label: str
    description: str
    type: str
    group: str
    value: Any = None
    unit: Optional[str] = None
    min: Optional[float] = None
    max: Optional[float] = None
    step: Optional[float] = None
    placeholder: Optional[str] = None
    rows: Optional[int] = None
    multiline: bool = False
    required: bool = False
    options: List[SceneFieldOption] = Field(default_factory=list)


class SceneFieldGroup(BaseModel):
    key: str
    label: str
    description: Optional[str] = None
    fields: List[SceneFieldSchema] = Field(default_factory=list)


class SceneSchema(BaseModel):
    name: str
    label: str
    description: Optional[str] = None
    enabled: bool
    groups: List[SceneFieldGroup] = Field(default_factory=list)


class ScenesResponse(BaseModel):
    order: List[str] = Field(default_factory=list)
    scenes: List[SceneSchema] = Field(default_factory=list)


class LogsClearResponse(BaseModel):
    cleared: bool = True
