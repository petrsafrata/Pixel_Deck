import React, { useEffect, useRef, useState } from "react";

import { uploadFile } from "../api";

type UploadQueueItem = {
  id: string;
  file: File;
  previewUrl: string;
  status: "queued" | "uploading" | "done" | "error";
  progress: number;
  error?: string;
};

type AssetManagerProps = {
  token: string;
  onRefresh: () => Promise<void> | void;
};

const SUPPORTED_EXTENSIONS = [".png", ".jpg", ".jpeg"];

function isSupportedFile(file: File): boolean {
  const lower = file.name.toLowerCase();
  return SUPPORTED_EXTENSIONS.some((ext) => lower.endsWith(ext));
}

function makeQueueItem(file: File): UploadQueueItem {
  return {
    id: `${file.name}-${file.lastModified}-${Math.random().toString(36).slice(2, 8)}`,
    file,
    previewUrl: URL.createObjectURL(file),
    status: "queued",
    progress: 0,
  };
}

export default function AssetManager({ token, onRefresh }: AssetManagerProps) {
  const [queue, setQueue] = useState<UploadQueueItem[]>([]);
  const [dragActive, setDragActive] = useState(false);
  const [resize, setResize] = useState(false);
  const [targetSize, setTargetSize] = useState(64);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const queueRef = useRef<UploadQueueItem[]>([]);

  useEffect(() => {
    queueRef.current = queue;
  }, [queue]);

  useEffect(() => {
    return () => {
      queueRef.current.forEach((item) => URL.revokeObjectURL(item.previewUrl));
    };
  }, []);

  const addFiles = (files: FileList | File[]) => {
    const nextQueue: UploadQueueItem[] = [];
    Array.from(files).forEach((file) => {
      if (!isSupportedFile(file)) {
        setError(`Unsupported file type: ${file.name}`);
        return;
      }
      nextQueue.push(makeQueueItem(file));
    });
    if (nextQueue.length > 0) {
      setQueue((prev) => [...prev, ...nextQueue]);
      setError("");
    }
  };

  const clearQueue = () => {
    queueRef.current.forEach((item) => URL.revokeObjectURL(item.previewUrl));
    queueRef.current = [];
    setQueue([]);
  };

  const handleUpload = async () => {
    setBusy(true);
    setError("");
    try {
      for (const item of queue) {
        if (item.status === "done") {
          continue;
        }
        setQueue((prev) =>
          prev.map((c) => (c.id === item.id ? { ...c, status: "uploading", progress: 0 } : c)),
        );
        await uploadFile("/api/assets/images", item.file, {
          token,
          query: { resize, target_size: targetSize },
          onProgress: (progress) => {
            setQueue((prev) => prev.map((c) => (c.id === item.id ? { ...c, progress } : c)));
          },
        });
        setQueue((prev) =>
          prev.map((c) => (c.id === item.id ? { ...c, status: "done", progress: 100 } : c)),
        );
      }
      await onRefresh();
    } catch (err) {
      const message = err instanceof Error ? err.message : "Upload failed";
      setError(message);
      setQueue((prev) =>
        prev.map((c) => (c.status === "uploading" ? { ...c, status: "error", error: message } : c)),
      );
    } finally {
      setBusy(false);
    }
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setDragActive(false);
    addFiles(event.dataTransfer.files);
  };

  const handleFileInput = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files) {
      addFiles(event.target.files);
      event.target.value = "";
    }
  };

  const pendingCount = queue.filter((i) => i.status !== "done").length;

  return (
    <div className="panel-card">
      <div className="panel-header">
        <div>
          <h2>Upload Images</h2>
          <p className="hint">Drag images here or choose files. Supported: PNG, JPG, JPEG.</p>
        </div>
        {queue.length > 0 && <span className="badge">{queue.length} queued</span>}
      </div>

      <div
        className={`upload-dropzone ${dragActive ? "upload-dropzone-active" : ""}`}
        onDragOver={(event) => {
          event.preventDefault();
          setDragActive(true);
        }}
        onDragLeave={() => setDragActive(false)}
        onDrop={handleDrop}
      >
        <div>
          <strong>Drop images here</strong>
          <p className="hint">Images will be saved to the canvas directory.</p>
        </div>
        <label className="upload-file-button">
          Choose files
          <input type="file" accept=".png,.jpg,.jpeg" multiple onChange={handleFileInput} />
        </label>
      </div>

      <div className="asset-controls asset-controls-stack">
        <label className="toggle-row">
          <input type="checkbox" checked={resize} onChange={(event) => setResize(event.target.checked)} />
          <span>Resize before upload</span>
        </label>
        <label>
          Target size
          <input type="number" min={16} max={1024} value={targetSize} onChange={(event) => setTargetSize(Number(event.target.value) || 64)} />
        </label>
        <div className="button-row">
          <button onClick={handleUpload} disabled={busy || queue.length === 0}>
            {pendingCount > 0 ? `Upload ${pendingCount} file${pendingCount > 1 ? "s" : ""}` : "Upload files"}
          </button>
          <button className="secondary" onClick={clearQueue} disabled={busy || queue.length === 0}>
            Clear queue
          </button>
        </div>
      </div>

      {error && <div className="error">{error}</div>}

      {queue.length > 0 && (
        <div className="upload-queue">
          {queue.map((item) => (
            <div key={item.id} className="upload-queue-item">
              <img src={item.previewUrl} alt={item.file.name} />
              <div className="upload-queue-meta">
                <strong>{item.file.name}</strong>
                <span>{Math.round(item.file.size / 1024)} KB</span>
                <div className="progress-bar">
                  <div className="progress-bar-fill" style={{ width: `${item.progress}%` }} />
                </div>
                <span className={`upload-status upload-status-${item.status}`}>{item.status}</span>
                {item.error && <span className="hint">{item.error}</span>}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}