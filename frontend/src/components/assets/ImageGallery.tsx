import React, { useState } from "react";

import type { AssetItem } from "../../types";
import ImageCard from "./ImageCard";
import ImagePreviewModal from "./ImagePreviewModal";

type ImageGalleryProps = {
  images: AssetItem[];
  selectedFiles: string[];
  onChange: (files: string[]) => void;
  onDeleteImage?: (name: string) => void;
};

function isFileActive(path: string, selectedFiles: string[]): boolean {
  return selectedFiles.some((f) => f === path || f.endsWith(`/${path.split("/").pop()}`));
}

export default function ImageGallery({ images, selectedFiles, onChange, onDeleteImage }: ImageGalleryProps) {
  const [previewImage, setPreviewImage] = useState<AssetItem | null>(null);

  const isActive = (img: AssetItem) => isFileActive(img.path, selectedFiles);

  const handleToggle = (img: AssetItem) => {
    if (isActive(img)) {
      onChange(selectedFiles.filter((f) => f !== img.path && !f.endsWith(`/${img.name}`)));
    } else {
      onChange([...selectedFiles, img.path]);
    }
  };

  const handleDelete = (img: AssetItem) => {
    onDeleteImage?.(img.name);
    if (previewImage?.name === img.name) {
      setPreviewImage(null);
    }
  };

  const previewActive = previewImage ? isActive(previewImage) : false;

  return (
    <div className="img-gallery">
      {images.length === 0 ? (
        <p className="hint">
          No images in canvas directory. Upload images using the Assets section below.
        </p>
      ) : (
        <div className="img-gallery-grid">
          {images.map((img) => (
            <ImageCard
              key={img.name}
              image={img}
              isActive={isActive(img)}
              onToggle={() => handleToggle(img)}
              onPreview={() => setPreviewImage(img)}
              onDelete={onDeleteImage ? () => handleDelete(img) : undefined}
            />
          ))}
        </div>
      )}
      {previewImage && (
        <ImagePreviewModal
          image={previewImage}
          isActive={previewActive}
          onClose={() => setPreviewImage(null)}
          onToggle={() => {
            handleToggle(previewImage);
            setPreviewImage(null);
          }}
          onDelete={onDeleteImage ? () => handleDelete(previewImage) : undefined}
        />
      )}
    </div>
  );
}
