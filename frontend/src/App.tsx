import React, { useCallback, useEffect, useMemo, useState } from "react";

import { apiRequest, getStoredToken, storeToken } from "./api";
import AssetManager from "./components/AssetManager";
import ConfigForm from "./components/ConfigForm";
import LogViewer from "./components/LogViewer";
import PreviewPanel from "./components/PreviewPanel";
import SceneList from "./components/SceneList";
import SecuritySettings from "./components/SecuritySettings";
import type { AssetItem, EditableField, LogEntry, Scene, SceneOrderResponse, StatusResponse } from "./types";

const REFRESH_INTERVAL_MS = 3000;
const DEFAULT_LOG_LIMIT = 200;

type SceneEdits = Record<string, Record<string, unknown>>;

function useInterval(callback: () => void, delay: number | null) {
  useEffect(() => {
    if (delay === null) {
      return undefined;
    }
    const id = window.setInterval(callback, delay);
    return () => window.clearInterval(id);
  }, [callback, delay]);
}

function flattenSceneFields(scene: Scene): EditableField[] {
  return scene.groups.flatMap((group) => group.fields);
}

function buildSceneEdits(scenes: Scene[]): SceneEdits {
  const edits: SceneEdits = {};
  scenes.forEach((scene) => {
    const fieldValues: Record<string, unknown> = {};
    flattenSceneFields(scene).forEach((field) => {
      fieldValues[field.key] = field.value;
    });
    edits[scene.name] = fieldValues;
  });
  return edits;
}

function getSceneMap(scenes: Scene[]): Map<string, Scene> {
  return new Map(scenes.map((scene) => [scene.name, scene]));
}

function normalizeListValue(value: unknown): string[] {
  if (Array.isArray(value)) {
    return value.map((item) => String(item).trim()).filter(Boolean);
  }
  if (typeof value === "string") {
    return value
      .split(/\r?\n/)
      .map((item) => item.trim())
      .filter(Boolean);
  }
  return [];
}

function sanitizeSceneUpdate(scene: Scene, edits: Record<string, unknown>): Record<string, unknown> {
  const payload: Record<string, unknown> = {};
  flattenSceneFields(scene).forEach((field) => {
    const value = edits[field.key];
    if (value === undefined || value === null) {
      return;
    }
    if (field.field_type === "number" && value === "") {
      return;
    }
    if (field.field_type === "string_list" || field.field_type === "image-gallery") {
      payload[field.key] = normalizeListValue(value);
      return;
    }
    payload[field.key] = value;
  });
  return payload;
}

export default function App() {
  const [token, setToken] = useState<string>(getStoredToken());
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [scenes, setScenes] = useState<Scene[]>([]);
  const [sceneOrder, setSceneOrder] = useState<string[]>([]);
  const [sceneEdits, setSceneEdits] = useState<SceneEdits>({});
  const [selectedScene, setSelectedScene] = useState<string | null>(null);
  const [images, setImages] = useState<AssetItem[]>([]);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [error, setError] = useState<string>("");
  const [previewTick, setPreviewTick] = useState<number>(Date.now());
  const [logLevel, setLogLevel] = useState<string>("");
  const [logLimit, setLogLimit] = useState<number>(DEFAULT_LOG_LIMIT);

  const authToken = token.trim();

  const setErrorMessage = useCallback((message: string) => {
    setError(message || "");
  }, []);

  const refreshStatus = useCallback(async () => {
    try {
      const data = await apiRequest<StatusResponse>("/api/status", { token: authToken });
      setStatus(data);
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "Failed to load status");
    }
  }, [authToken, setErrorMessage]);

  const refreshScenes = useCallback(async () => {
    try {
      const data = await apiRequest<SceneOrderResponse>("/api/scenes", { token: authToken });
      const nextScenes = data.scenes || [];
      setScenes(nextScenes);
      setSceneOrder(data.order || []);
      setSceneEdits(buildSceneEdits(nextScenes));
      setSelectedScene((current) => {
        if (current && nextScenes.some((scene) => scene.name === current)) {
          return current;
        }
        return data.order?.[0] || nextScenes[0]?.name || null;
      });
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "Failed to load scenes");
    }
  }, [authToken, setErrorMessage]);

  const refreshImages = useCallback(async () => {
    try {
      const data = await apiRequest<{ items: AssetItem[] }>("/api/assets/images", { token: authToken });
      setImages(data.items || []);
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "Failed to load assets");
    }
  }, [authToken, setErrorMessage]);

  const refreshLogs = useCallback(async () => {
    try {
      const data = await apiRequest<{ items: LogEntry[] }>("/api/logs", {
        token: authToken,
        query: { limit: logLimit, level: logLevel || undefined },
      });
      setLogs(data.items || []);
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "Failed to load logs");
    }
  }, [authToken, logLevel, logLimit, setErrorMessage]);

  useEffect(() => {
    if (authToken) {
      refreshStatus();
      refreshScenes();
      refreshImages();
      refreshLogs();
    }
  }, [authToken, refreshImages, refreshLogs, refreshScenes, refreshStatus]);

  useInterval(() => {
    if (!authToken) {
      return;
    }
    refreshStatus();
    setPreviewTick(Date.now());
  }, REFRESH_INTERVAL_MS);

  useEffect(() => {
    if (authToken) {
      refreshLogs();
    }
  }, [authToken, logLevel, logLimit, refreshLogs]);

  const handleSaveToken = () => {
    storeToken(authToken);
  };

  const handleSceneFieldChange = (sceneName: string, path: string, value: unknown) => {
    setSceneEdits((prev) => ({
      ...prev,
      [sceneName]: {
        ...prev[sceneName],
        [path]: value,
      },
    }));
  };

  const handleSaveScene = async (sceneName: string) => {
    try {
      const sceneMap = getSceneMap(scenes);
      const scene = sceneMap.get(sceneName);
      if (!scene) {
        return;
      }
      const payload = sanitizeSceneUpdate(scene, sceneEdits[sceneName] || {});
      if (Object.keys(payload).length === 0) {
        return;
      }
      await apiRequest(`/api/scenes/${sceneName}`, {
        method: "PATCH",
        token: authToken,
        body: { fields: payload },
      });
      await refreshScenes();
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "Failed to save scene");
    }
  };

  const handleToggleSceneEnabled = async (sceneName: string, enabled: boolean) => {
    try {
      await apiRequest(`/api/scenes/${sceneName}`, {
        method: "PATCH",
        token: authToken,
        body: { enabled },
      });
      await refreshScenes();
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "Failed to update scene state");
    }
  };

  const handleToggleDisplay = async () => {
    try {
      const enabled = !(status && status.display_enabled);
      await apiRequest("/api/actions/display", {
        method: "POST",
        token: authToken,
        body: { enabled },
      });
      await refreshStatus();
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "Failed to toggle display");
    }
  };

  const handleClearDisplay = async () => {
    try {
      await apiRequest("/api/actions/clear", { method: "POST", token: authToken });
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "Failed to clear display");
    }
  };

  const handleReloadConfig = async () => {
    try {
      await apiRequest("/api/actions/reload", { method: "POST", token: authToken });
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "Failed to reload config");
    }
  };

  const handleRestart = async () => {
    try {
      await apiRequest("/api/actions/restart", { method: "POST", token: authToken });
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "Failed to restart app");
    }
  };

  const handleDeleteImage = async (name: string) => {
    try {
      await apiRequest(`/api/assets/images/${name}`, {
        method: "DELETE",
        token: authToken,
      });
      await refreshImages();
      await refreshScenes();
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "Failed to delete image");
    }
  };

  const handleSceneOrderUpdate = async (order: string[]) => {
    setSceneOrder(order);
    try {
      await apiRequest("/api/scenes/order", {
        method: "PATCH",
        token: authToken,
        body: { order },
      });
      await refreshScenes();
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "Failed to update scene order");
    }
  };

  const handleClearLogs = async () => {
    try {
      await apiRequest("/api/logs/clear", { method: "POST", token: authToken });
      await refreshLogs();
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "Failed to clear logs");
    }
  };

  const sceneMap = useMemo(() => getSceneMap(scenes), [scenes]);
  const selected = selectedScene ? sceneMap.get(selectedScene) || null : null;
  const selectedDrafts = selected ? sceneEdits[selected.name] || {} : {};
  const showAssets = Boolean(selected?.capabilities?.supportsAssets);

  return (
    <div className="app">
      <header className="header">
        <div className="header-copy">
          <h1>Pixel Deck Control Center</h1>
          <p>Manage scenes, preview, assets, logs, and device controls from one place.</p>
        </div>
        <div className="header-status">
          <div>
            <span>Renderer mode</span>
            <strong>{status?.renderer_mode || "-"}</strong>
          </div>
          <div>
            <span>Display</span>
            <strong>{status?.display_enabled ? "Enabled" : "Disabled"}</strong>
          </div>
          <div>
            <span>Active scene</span>
            <strong>{status?.active_scene || "-"}</strong>
          </div>
          <div>
            <span>Uptime</span>
            <strong>{status?.uptime_s ? `${status.uptime_s}s` : "-"}</strong>
          </div>
        </div>
      </header>

      {error && <div className="error">{error}</div>}

      <section className="dashboard">
        <aside className="dashboard-column">
          <SceneList
            scenes={scenes}
            order={sceneOrder}
            selectedScene={selectedScene}
            activeScene={status?.active_scene || null}
            onSelect={setSelectedScene}
            onReorder={handleSceneOrderUpdate}
            onToggleEnabled={handleToggleSceneEnabled}
          />
        </aside>

        <main className="dashboard-column dashboard-main">
          <PreviewPanel
            status={status}
            previewTick={previewTick}
            onToggleDisplay={handleToggleDisplay}
            onClearDisplay={handleClearDisplay}
            onReloadConfig={handleReloadConfig}
            onRestart={handleRestart}
          />
        </main>

        <aside className="dashboard-column">
          <ConfigForm
            scene={selected}
            values={selectedDrafts}
            onFieldChange={(path, value) => selected && handleSceneFieldChange(selected.name, path, value)}
            onSave={() => selected && handleSaveScene(selected.name)}
            images={images}
            onDeleteImage={handleDeleteImage}
          />
          {showAssets && (
            <AssetManager
              token={authToken}
              onRefresh={async () => {
                await refreshImages();
                await refreshScenes();
              }}
            />
          )}
        </aside>
      </section>

      <section className="bottom-section">
        <div className="bottom-logs">
          <LogViewer
            logs={logs}
            logLevel={logLevel}
            limit={logLimit}
            onLevelChange={setLogLevel}
            onLimitChange={setLogLimit}
            onRefresh={refreshLogs}
            onClear={handleClearLogs}
          />
        </div>
        <div className="bottom-settings">
          <SecuritySettings token={token} onTokenChange={setToken} onSaveToken={handleSaveToken} />
        </div>
      </section>
    </div>
  );
}