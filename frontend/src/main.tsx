import React from "react";
import { createRoot } from "react-dom/client";

import App from "./App.tsx";
import "./styles.css";

const container = document.getElementById("root");
if (!container) {
  console.error("Root element not found - cannot bootstrap React application");
  throw new Error("Root element not found");
}

console.log("Root element found, rendering App...");

try {
  const root = createRoot(container);
  root.render(<App />);
  console.log("App rendered successfully");
} catch (error) {
  console.error("Error rendering app:", error);
  container.innerHTML = `<div style="padding: 20px; color: red;">Error rendering application: ${error instanceof Error ? error.message : String(error)}</div>`;
}

