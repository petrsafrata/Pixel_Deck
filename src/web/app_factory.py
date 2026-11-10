"""
FastAPI application factory for the Pixel Deck Web Control Center.

This module creates and configures the complete HTTP API used to control a
running Pixel Deck instance. It exposes endpoints for scene management,
configuration editing, asset management, diagnostics, logging and runtime
control.

The web API is intentionally designed as a thin layer over the core
application. Business logic such as configuration editing, validation and
scene metadata handling is delegated to dedicated service modules
(`config_editor`, `assets`, `runtime_state`, etc.), while this module is
primarily responsible for:

- registering API endpoints,
- request validation,
- converting exceptions into HTTP responses,
- coordinating runtime actions,
- serving the React frontend.

The application follows the Pixel Deck design principles:

- `config.yml` remains the single source of truth.
- The Web UI acts only as a safe editor of the configuration.
- Scene configuration is schema-driven rather than hardcoded.
- The same API supports both Window and Matrix rendering modes.
- Runtime operations (reload, restart, display control) are coordinated
  through `RuntimeState`.

This module intentionally contains very little business logic. Most endpoint
handlers delegate their work to dedicated helper modules to keep the API layer
small, maintainable and easy to test.
"""

from __future__ import annotations

import os
import time
from dataclasses import asdict
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from src.core.logging_config import clear_recent_logs, get_recent_logs, set_log_level
from src.web.assets import delete_uploaded_image, get_upload_dir, list_uploaded_images, save_uploaded_image
from src.web.auth import require_api_token
from src.web.config_editor import (
    apply_scene_order,
    apply_scene_update,
    get_scene_schemas,
    is_image_referenced,
    load_config_dict,
    sanitize_config,
    save_config_dict,
    set_active_scene,
    set_app_log_level,
    set_display_output_enabled,
)
from src.web.models import (
    ConfigPatchRequest,
    DisplayToggleRequest,
    LogLevelRequest,
    SceneOrderRequest,
    SceneUpdateRequest,
)
from src.web.runtime_state import RuntimeState


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"

OPENAPI_TAGS = [
    {
        "name": "Status",
        "description": "Runtime status and live display preview.",
    },
    {
        "name": "Configuration",
        "description": "Read and update the Pixel Deck configuration.",
    },
    {
        "name": "Scenes",
        "description": "Manage scene configuration, ordering and availability.",
    },
    {
        "name": "Display Control",
        "description": "Reload, restart, enable, disable or clear the display.",
    },
    {
        "name": "Assets",
        "description": "Upload, list, preview and delete image assets.",
    },
    {
        "name": "Logs",
        "description": "Read and manage application logs.",
    },
    {
        "name": "Diagnostics",
        "description": "Inspect renderer and application diagnostics.",
    },
    {
        "name": "System",
        "description": "Health checks and system-level endpoints.",
    },
]

def create_app(runtime: RuntimeState) -> FastAPI:
    app = FastAPI(title="Pixel Deck Web API", version="1.0.0", docs_url="/ui/docs", openapi_tags=OPENAPI_TAGS)
    app.state.runtime = runtime

    if FRONTEND_DIST.exists():
        app.mount("/ui", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")

    assets_path = PROJECT_ROOT / "assets"
    if assets_path.exists():
        app.mount("/assets", StaticFiles(directory=assets_path), name="assets")

    @app.get("/", include_in_schema=False)
    def serve_root() -> FileResponse:
        if FRONTEND_DIST.exists():
            return FileResponse(FRONTEND_DIST / "index.html")
        raise HTTPException(status_code=404, detail="Frontend not built")

    @app.get("/api/status", dependencies=[Depends(require_api_token)], tags=["status"])
    def get_status() -> dict:
        status = runtime.get_status()
        status["uptime_s"] = int(time.time() - runtime.started_at)
        return status

    @app.get("/api/preview", tags=["Status"])
    def get_preview() -> Response:
        renderer = runtime.get_renderer()
        if renderer is None or not hasattr(renderer, "get_preview_png"):
            raise HTTPException(status_code=503, detail="Preview not available")
        data = renderer.get_preview_png()
        return Response(content=data, media_type="image/png")

    @app.get("/api/config", dependencies=[Depends(require_api_token)], tags=["Configuration"])
    def get_config() -> dict:
        data = load_config_dict(runtime.config_path)
        return sanitize_config(data)

    @app.patch("/api/config", dependencies=[Depends(require_api_token)], tags=["Configuration"])
    def patch_config(payload: ConfigPatchRequest) -> dict:
        data = load_config_dict(runtime.config_path)
        changed = False

        if payload.active_scene:
            try:
                set_active_scene(data, payload.active_scene)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            changed = True

        if not changed:
            return {"updated": False}

        save_config_dict(runtime.config_path, data)
        runtime.reload_event.set()
        return {"updated": True}

    @app.get("/api/scenes", dependencies=[Depends(require_api_token)], tags=["Scenes"])
    def get_scenes() -> dict:
        data = load_config_dict(runtime.config_path)
        order = data.get("app", {}).get("scene_order", [])
        schemas = get_scene_schemas(data, registered_scenes=runtime.registered_scenes or None)
        return {"order": order, "scenes": [asdict(scene_schema) for scene_schema in schemas]}

    @app.patch("/api/scenes/order", dependencies=[Depends(require_api_token)], tags=["Scenes"])
    def update_scene_order(payload: SceneOrderRequest) -> dict:
        data = load_config_dict(runtime.config_path)
        try:
            apply_scene_order(data, payload.order)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        save_config_dict(runtime.config_path, data)
        runtime.reload_event.set()
        return {"updated": True}

    @app.patch("/api/scenes/{scene_name}", dependencies=[Depends(require_api_token)], tags=["Scenes"])
    def update_scene(scene_name: str, payload: SceneUpdateRequest) -> dict:
        data = load_config_dict(runtime.config_path)
        scenes = data.setdefault("scenes", {})
        if scene_name not in scenes:
            raise HTTPException(status_code=400, detail=f"Unknown scene: {scene_name}")

        changed = False
        if payload.enabled is not None:
            scenes[scene_name]["enabled"] = bool(payload.enabled)
            changed = True

        if payload.fields:
            try:
                apply_scene_update(data, scene_name, payload.fields)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            changed = True

        if not changed:
            return {"updated": False}

        save_config_dict(runtime.config_path, data)
        runtime.reload_event.set()
        return {"updated": True}

    @app.post("/api/actions/reload", dependencies=[Depends(require_api_token)], tags=["Display Control"])
    def reload_config() -> dict:
        runtime.reload_event.set()
        return {"queued": True}

    @app.post("/api/actions/restart", dependencies=[Depends(require_api_token)], tags=["Display Control"])
    def restart_app() -> dict:
        if not runtime.web.allow_restart:
            raise HTTPException(status_code=403, detail="Restart not allowed")
        runtime.restart_event.set()
        return {"queued": True}

    @app.post("/api/actions/display", dependencies=[Depends(require_api_token)], tags=["Display Control"])
    def toggle_display(payload: DisplayToggleRequest) -> dict:
        if not runtime.web.allow_display_power_control:
            raise HTTPException(status_code=403, detail="Display control not allowed")
        data = load_config_dict(runtime.config_path)
        set_display_output_enabled(data, payload.enabled)
        save_config_dict(runtime.config_path, data)
        runtime.set_display_enabled(payload.enabled)
        return {"enabled": runtime.display_enabled}

    @app.post("/api/actions/clear", dependencies=[Depends(require_api_token)], tags=["Display Control"])
    def clear_display() -> dict:
        renderer = runtime.get_renderer()
        if renderer is None or not hasattr(renderer, "clear_and_present"):
            raise HTTPException(status_code=503, detail="Renderer not ready")
        renderer.clear_and_present(force_output=True)
        return {"cleared": True}

    @app.get("/api/assets/images/{filename}", tags=["Assets"])
    def get_image(filename: str) -> FileResponse:
        safe_name = os.path.basename(filename)
        canvas_dir = PROJECT_ROOT / "assets" / "images" / "canvas"
        target = canvas_dir / safe_name
        if not target.exists() or not target.is_file():
            raise HTTPException(status_code=404, detail="Image not found")
        ext = target.suffix.lower()
        if ext not in {".png", ".jpg", ".jpeg"}:
            raise HTTPException(status_code=403, detail="Forbidden")
        media_type = "image/png" if ext == ".png" else "image/jpeg"
        return FileResponse(str(target), media_type=media_type)

    @app.get("/api/assets/images", dependencies=[Depends(require_api_token)], tags=["Assets"])
    def get_images() -> dict:
        upload_dir = get_upload_dir(PROJECT_ROOT)
        items = list_uploaded_images(upload_dir)
        return {"items": items}

    @app.post("/api/assets/images", dependencies=[Depends(require_api_token)], tags=["Assets"])
    async def upload_image(
        file: UploadFile = File(...),
        resize: bool = Query(default=False),
        target_size: int = Query(default=64),
    ) -> dict:
        upload_dir = get_upload_dir(PROJECT_ROOT)
        content = await file.read()
        try:
            saved = save_uploaded_image(upload_dir, file.filename, content, resize=resize, target_size=target_size)
        except FileExistsError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        items = list_uploaded_images(upload_dir)
        saved_info = next((item for item in items if item["name"] == saved.name), {"name": saved.name})
        return {"saved": saved_info}

    @app.delete("/api/assets/images/{name}", dependencies=[Depends(require_api_token)], tags=["Assets"])
    def delete_image(name: str, force: bool = Query(default=False)) -> dict:
        upload_dir = get_upload_dir(PROJECT_ROOT)
        if not force:
            data = load_config_dict(runtime.config_path)
            referenced, ref_scene = is_image_referenced(data, name)
            if referenced:
                raise HTTPException(
                    status_code=409,
                    detail=f"Image is referenced in scene '{ref_scene}'",
                )
        try:
            delete_uploaded_image(upload_dir, name)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return {"deleted": True}

    @app.get("/api/logs", dependencies=[Depends(require_api_token)], tags=["Logs"])
    def get_logs(limit: int = Query(default=200), level: str | None = Query(default=None)) -> dict:
        return {"items": get_recent_logs(limit=limit, level=level)}

    @app.post("/api/logs/level", dependencies=[Depends(require_api_token)], tags=["Logs"])
    def set_logs_level(payload: LogLevelRequest) -> dict:
        if not runtime.web.allow_debug_logging:
            raise HTTPException(status_code=403, detail="Debug logging control not allowed")
        data = load_config_dict(runtime.config_path)
        try:
            set_app_log_level(data, payload.level)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        save_config_dict(runtime.config_path, data)
        set_log_level(payload.level)
        return {"level": payload.level.upper()}

    @app.post("/api/logs/clear", dependencies=[Depends(require_api_token)], tags=["Logs"])
    def clear_logs() -> dict:
        clear_recent_logs()
        return {"cleared": True}

    @app.get("/api/diagnostics", dependencies=[Depends(require_api_token)], tags=["Diagnostics"])
    def get_diagnostics() -> dict:
        renderer = runtime.get_renderer()
        return {
            "renderer": renderer.__class__.__name__ if renderer else None,
            "preview_available": bool(renderer and hasattr(renderer, "get_preview_png")),
        }

    @app.get("/health", tags=["Health"])
    def health() -> dict:
        return {"ok": True}

    return app

