# Web Control Center

The Web Control Center provides browser-based management and monitoring through a React frontend and FastAPI backend.

## Features

- Live display preview
- Scene enable/disable
- Drag-and-drop scene ordering
- Scene-specific configuration
- Display output control
- Image gallery and uploads
- Runtime logs
- Application actions
- API token protection for protected operations

## Schema-driven forms

Scenes expose editable fields as metadata. The backend converts this metadata into scene schemas and React renders the corresponding controls dynamically.

This avoids scene-specific frontend forms for supported field types.

## Persistence

Configuration changes made in the UI are written to `config/config.yml` and can trigger a runtime reload.

## Production

The React application is compiled during the Docker build. The resulting `frontend/dist` files are included in the runtime image and served by FastAPI, so no Vite development server is required in production.
