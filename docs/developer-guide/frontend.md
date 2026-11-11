# Frontend Development

The Pixel Deck Web Control Center uses React 18.3.1, TypeScript, and Vite 5.4.2.

## Run locally

```bash
cd frontend
npm install
npm run dev
```

The FastAPI backend must also be running for API-dependent features.

## Production build

```bash
npm run build
```

Output:

```text
frontend/dist/
```

During Docker deployment the frontend is built automatically and copied into the final runtime image.

## Configuration UI

The frontend receives scene metadata from FastAPI and dynamically renders Boolean, Number, Color, Text, Select, String List, and Image Gallery controls.
