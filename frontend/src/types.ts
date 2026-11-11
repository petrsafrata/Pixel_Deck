/**
 * Shared TypeScript models for the Pixel Deck Web UI.
 *
 * These interfaces define the data contracts exchanged between the React
 * frontend and the FastAPI backend. They mirror the Pydantic models exposed
 * by the backend API and provide strong typing throughout the application.
 *
 * The models cover:
 *
 * - Scene metadata and configuration
 * - Dynamic field definitions used to build configuration forms
 * - Runtime status information
 * - Log entries
 * - Uploaded image assets
 *
 * Scene configuration is schema-driven. The frontend does not contain
 * hardcoded forms for individual scenes. Instead, it renders editors
 * dynamically from the metadata received from the backend.
 *
 * Any changes to the backend API models should be reflected in this file
 * to keep both sides synchronized.
 */

export type FieldType = "boolean" | "number" | "color" | "text" | "select" | "string_list" | "image-gallery";

export type FieldOption = {
  label: string;
  value: string | number | boolean;
};

export type EditableField = {
  key: string;
  label: string;
  description: string;
  field_type: FieldType;
  group: string;
  value: unknown;
  unit?: string | null;
  minimum?: number | null;
  maximum?: number | null;
  step?: number | null;
  placeholder?: string | null;
  rows?: number | null;
  multiline?: boolean;
  required?: boolean;
  numeric_type?: "int" | "float" | null;
  options?: FieldOption[];
};

export type SceneFieldGroup = {
  key: string;
  label: string;
  description?: string | null;
  fields: EditableField[];
};

export type SceneCapabilities = {
  supportsAssets?: boolean;
  supportsImageGallery?: boolean;
};

export type Scene = {
  name: string;
  label: string;
  description?: string | null;
  enabled: boolean;
  groups: SceneFieldGroup[];
  capabilities?: SceneCapabilities;
};

export type SceneOrderResponse = {
  order: string[];
  scenes: Scene[];
};

export type StatusResponse = {
  active_scene: string | null;
  display_enabled: boolean;
  renderer_mode: string;
  last_present_at: number | null;
  last_config_reload_at: number | null;
  started_at: number;
  web_enabled: boolean;
  uptime_s: number;
};

export type LogEntry = {
  timestamp: string;
  level: string;
  levelno: number;
  logger: string;
  message: string;
};

export type AssetItem = {
  name: string;
  path: string;
  url?: string;
  width?: number;
  height?: number;
  sizeBytes?: number;
};
