import React from "react";

import type { StatusResponse } from "../types";

type PreviewPanelProps = {
  status: StatusResponse | null;
  previewTick: number;
  onToggleDisplay: () => void;
  onClearDisplay: () => void;
  onReloadConfig: () => void;
  onRestart: () => void;
};

function formatTimestamp(value: number | null | undefined): string {
  if (!value) {
    return "-";
  }
  try {
    return new Date(value * 1000).toLocaleString();
  } catch (error) {
    return String(value);
  }
}

export default function PreviewPanel({
  status,
  previewTick,
  onToggleDisplay,
  onClearDisplay,
  onReloadConfig,
  onRestart,
}: PreviewPanelProps) {
  return (
    <div className="panel-card">
      <div className="panel-header">
        <h2>Live Preview</h2>
        <span className="badge">64×64</span>
      </div>
      <div className="preview-frame">
        <img src={`/api/preview?ts=${previewTick}`} alt="Preview" />
      </div>
      <div className="status-grid">
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
        <div>
          <span>Last present</span>
          <strong>{formatTimestamp(status?.last_present_at)}</strong>
        </div>
        <div>
          <span>Last reload</span>
          <strong>{formatTimestamp(status?.last_config_reload_at)}</strong>
        </div>
      </div>
      <div className="button-row">
        <button onClick={onToggleDisplay}>
          {status?.display_enabled ? "Turn display off" : "Turn display on"}
        </button>
        <button onClick={onClearDisplay}>Clear matrix</button>
        <button onClick={onReloadConfig}>Reload config</button>
        <button onClick={onRestart}>Restart app</button>
      </div>
    </div>
  );
}

