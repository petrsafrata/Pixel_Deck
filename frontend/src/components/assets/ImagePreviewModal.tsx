import React, { useEffect } from "react";

import type { AssetItem } from "../../types";

type ImagePreviewModalProps = {
  image: AssetItem;
  isActive: boolean;
  onClose: () => void;
  onToggle: () => void;
  onDelete?: () => void;
};

export default function ImagePreviewModal({ image, isActive, onClose, onToggle, onDelete }: ImagePreviewModalProps) {
  const src = `/${image.path}`;

  useEffect(() => {
    const handleKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    };
    document.addEventListener("keydown", handleKey);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", handleKey);
      document.body.style.overflow = "";
    };
  }, [onClose]);

  return (
    <div className="modal-backdrop" onClick={onClose} role="dialog" aria-modal="true">
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>{image.name}</h3>
          <button className="secondary" onClick={onClose} aria-label="Close modal">
            ✕
          </button>
        </div>
        <div className="modal-preview">
          <img src={src} alt={image.name} />
        </div>
        <div className="modal-meta">
          {image.width != null && image.height != null && image.width > 0 && (
            <span>{image.width}×{image.height} px</span>
          )}
          {image.sizeBytes != null && image.sizeBytes > 0 && (
            <span>{Math.round(image.sizeBytes / 1024)} KB</span>
          )}
          <span className="hint" title={image.path}>{image.path}</span>
          {isActive && <span className="badge">Active in scene</span>}
        </div>
        <div className="button-row">
          <button onClick={onToggle}>{isActive ? "Remove from scene" : "Add to scene"}</button>
          {onDelete && (
            <button className="secondary danger" onClick={onDelete}>
              Delete file
            </button>
          )}
          <button className="secondary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}


