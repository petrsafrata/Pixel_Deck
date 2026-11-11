# 🌐 Pixel Deck Web Control Center

The **Pixel Deck Web Control Center** is the React-based frontend for managing and monitoring Pixel Deck through a web browser.

It communicates with the Pixel Deck FastAPI backend and provides a user-friendly interface for runtime configuration, scene management, display control, and monitoring.

## 🛠 Technologies

- React 18.3.1
- TypeScript
- Vite 5.4.2
- FastAPI backend API

## ⭐ Features

The Web Control Center provides:

- Live display preview
- Scene enable/disable controls
- Drag-and-drop scene ordering
- Scene-specific configuration
- Dynamically generated configuration forms
- Display power control
- Image gallery management and uploads
- Runtime log viewer
- Application controls

Scene configuration forms are generated dynamically from metadata provided by the backend. This allows new editable scene fields to be added without creating scene-specific React forms.

## 📂 Structure

```text
frontend/
│
├── src/              # React application source code
├── package.json      # Frontend dependencies and scripts
├── tsconfig.json     # TypeScript configuration
└── vite.config.ts    # Vite configuration
```

## 🖥 Development

Install the frontend dependencies:

```bash
cd frontend
npm install
```

Start the Vite development server:

```bash
npm run dev
```

The development server provides hot module replacement (HMR), so frontend changes are reflected automatically while developing.

> [!NOTE]
> The Pixel Deck FastAPI backend must also be running for API-dependent functionality to work.

## 📦 Production Build

Create a production build with:

```bash
npm run build
```

The compiled frontend is generated in:

```text
frontend/dist/
```

During Docker deployment, the frontend is built automatically using the Node.js build stage defined in the main project `Dockerfile`.

The compiled files are then copied into the final Pixel Deck runtime image and served by the FastAPI application.

There is therefore no separate Vite development server required in production.

## ⚙ Configuration

The frontend communicates with the Pixel Deck REST API provided by FastAPI.

Scene configuration is schema-driven. Editable fields are defined by the backend using `FieldSpec` metadata and returned to the frontend through the API.

Supported field types include:

- Boolean
- Number
- Color
- Text
- Select
- String list
- Image gallery

This keeps the frontend generic and allows scenes to expose new configuration options without requiring scene-specific UI implementations.

## 🔗 Main Project

For Pixel Deck installation, Raspberry Pi deployment, hardware setup, configuration, and architecture, see the main [`README.md`](../README.md).