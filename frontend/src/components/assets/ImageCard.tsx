import React from "react";

import type { AssetItem } from "../../types";

type ImageCardProps = {
  image: AssetItem;
  isActive: boolean;
  onToggle: () => void;
  onPreview: () => void;
  onDelete?: () => void;
};

export default function ImageCard({ image, isActive, onToggle, onPreview, onDelete }: ImageCardProps) {
  const src = `/${image.path}`;

  return (
    <div className={`img-card ${isActive ? "img-card-active" : ""}`}>
      <div className="img-card-thumb" onClick={onPreview} title="Click to preview">
        <img src={src} alt={image.name} />
        {isActive && <div className="img-card-active-badge">✓ Active</div>}
      </div>
      <div className="img-card-info">
        <span className="img-card-name" title={image.name}>
          {image.name}
        </span>
        {image.width != null && image.height != null && image.width > 0 && (
          <span className="img-card-dims">
            {image.width}×{image.height}
          </span>
        )}
        <div className="button-row">
          <button className={`small ${isActive ? "secondary" : ""}`} onClick={onToggle}>
            {isActive ? "Remove" : "Add"}
          </button>
          {onDelete && (
            <button className="secondary small danger" onClick={onDelete} title="Delete file from disk">
              ✕
            </button>
          )}
        </div>
      </div>
    </div>
  );
}


