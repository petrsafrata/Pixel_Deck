import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In production (`vite build`) the frontend is served by FastAPI under the
// /ui/ prefix (app.mount("/ui", StaticFiles(...))).  Setting base to "/ui/"
// makes Vite embed correct absolute paths in the built index.html so the
// browser requests /ui/assets/index-*.js instead of /assets/index-*.js,
// avoiding a collision with the Pixel Deck app-level /assets/ mount.
//
// In development (`vite dev`) base stays at "/" so the dev server works
// normally at http://localhost:5173/ and the /assets proxy still forwards
// Pixel Deck image requests to the FastAPI backend.
export default defineConfig(({ command }) => ({
  plugins: [react()],
  base: command === "build" ? "/ui/" : "/",
  server: {
    proxy: {
      "/api": "http://localhost:8080",
      "/assets": "http://localhost:8080",
    },
  },
}));


