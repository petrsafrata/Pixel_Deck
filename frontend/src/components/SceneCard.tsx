import React from "react";

import type { Scene } from "../types";

type SceneCardProps = {
  scene: Scene;
  isSelected: boolean;
  isActive: boolean;
  onSelect: () => void;
  onToggleEnabled: (enabled: boolean) => void;
  onDragStart: (event: React.DragEvent<HTMLDivElement>) => void;
  onDrop: (event: React.DragEvent<HTMLDivElement>) => void;
  onDragOver: (event: React.DragEvent<HTMLDivElement>) => void;
};

export default function SceneCard({
  scene,
  isSelected,
  isActive,
  onSelect,
  onToggleEnabled,
  onDragStart,
  onDrop,
  onDragOver,
}: SceneCardProps) {
  const fieldCount = scene.groups.reduce((count, group) => count + group.fields.length, 0);

  return (
    <div
      className={`scene-card ${isSelected ? "scene-card-selected" : ""}`}
      onClick={onSelect}
      draggable
      onDragStart={onDragStart}
      onDragOver={onDragOver}
      onDrop={onDrop}
    >
      <div className="scene-card-header">
        <div>
          <h3>{scene.label}</h3>
          <div className="scene-card-meta">
            <span>{scene.name}</span>
            <span>{fieldCount} fields</span>
          </div>
        </div>
        {isActive && <span className="badge">Active</span>}
      </div>
      <p className="hint scene-card-description">{scene.description || "No description available."}</p>
      <label className="toggle-row" onClick={(event) => event.stopPropagation()}>
        <input
          type="checkbox"
          checked={scene.enabled}
          onChange={(event) => onToggleEnabled(event.target.checked)}
        />
        <span>{scene.enabled ? "Enabled" : "Disabled"}</span>
      </label>
    </div>
  );
}