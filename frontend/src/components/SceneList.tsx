import React from "react";

import type { Scene } from "../types";
import SceneCard from "./SceneCard";

type SceneListProps = {
  scenes: Scene[];
  order: string[];
  selectedScene: string | null;
  activeScene: string | null;
  onSelect: (sceneName: string) => void;
  onReorder: (order: string[]) => void;
  onToggleEnabled: (sceneName: string, enabled: boolean) => void;
};

export default function SceneList({
  scenes,
  order,
  selectedScene,
  activeScene,
  onSelect,
  onReorder,
  onToggleEnabled,
}: SceneListProps) {
  const byName = new Map(scenes.map((scene) => [scene.name, scene]));
  const ordered = [
    ...(order.map((name) => byName.get(name)).filter(Boolean) as Scene[]),
    ...scenes.filter((scene) => !order.includes(scene.name)),
  ];

  const handleDragStart = (event: React.DragEvent<HTMLDivElement>, sceneName: string) => {
    event.dataTransfer.setData("text/plain", sceneName);
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>, targetName: string) => {
    event.preventDefault();
    const sourceName = event.dataTransfer.getData("text/plain");
    if (!sourceName || sourceName === targetName) {
      return;
    }
    const newOrder = [...order];
    const sourceIndex = newOrder.indexOf(sourceName);
    const targetIndex = newOrder.indexOf(targetName);
    if (sourceIndex === -1 || targetIndex === -1) {
      return;
    }
    newOrder.splice(sourceIndex, 1);
    newOrder.splice(targetIndex, 0, sourceName);
    onReorder(newOrder);
  };

  return (
    <div className="panel-card">
      <div className="panel-header">
        <h2>Scenes</h2>
        <span className="hint">Drag to reorder</span>
      </div>
      {ordered.length === 0 ? (
        <p className="hint">No scenes available. Please provide an API token and try again.</p>
      ) : (
        <div className="scene-list">
          {ordered.map((scene) => (
            <SceneCard
              key={scene.name}
              scene={scene}
              isSelected={scene.name === selectedScene}
              isActive={scene.name === activeScene}
              onSelect={() => onSelect(scene.name)}
              onToggleEnabled={(enabled) => onToggleEnabled(scene.name, enabled)}
              onDragStart={(event) => handleDragStart(event, scene.name)}
              onDragOver={(event) => event.preventDefault()}
              onDrop={(event) => handleDrop(event, scene.name)}
            />
          ))}
        </div>
      )}
    </div>
  );
}