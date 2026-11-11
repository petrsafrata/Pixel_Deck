import React from "react";

import type { AssetItem, EditableField, Scene } from "../types";
import ImageGallery from "./assets/ImageGallery";

type ConfigFormProps = {
  scene: Scene | null;
  values: Record<string, unknown>;
  onFieldChange: (path: string, value: unknown) => void;
  onSave: () => void;
  images?: AssetItem[];
  onDeleteImage?: (name: string) => void;
};

type FieldInputProps = {
  field: EditableField;
  value: unknown;
  onChange: (value: unknown) => void;
  images?: AssetItem[];
  onDeleteImage?: (name: string) => void;
};

function formatNumberValue(value: unknown): string {
  if (value === undefined || value === null) {
    return "";
  }
  return String(value);
}

function FieldInput({ field, value, onChange, images, onDeleteImage }: FieldInputProps) {
  const fieldType = field.field_type;

  if (fieldType === "image-gallery") {
    return (
      <div className="field-control field-control-column">
        <span>{field.label}</span>
        <ImageGallery
          images={images || []}
          selectedFiles={Array.isArray(value) ? (value as string[]) : []}
          onChange={onChange}
          onDeleteImage={onDeleteImage}
        />
        <p className="field-description">{field.description}</p>
      </div>
    );
  }

  if (fieldType === "boolean") {
    return (
      <label className="field-control field-control-inline">
        <input type="checkbox" checked={Boolean(value)} onChange={(event) => onChange(event.target.checked)} />
        <span>{field.label}</span>
      </label>
    );
  }

  if (fieldType === "number") {
    return (
      <label className="field-control">
        <div className="field-label-row">
          <span>{field.label}</span>
          {field.unit && <span className="field-unit">{field.unit}</span>}
        </div>
        <input
          type="number"
          min={field.minimum ?? undefined}
          max={field.maximum ?? undefined}
          step={field.step ?? (field.numeric_type === "float" ? 0.01 : 1)}
          value={formatNumberValue(value)}
          onChange={(event) => onChange(event.target.value)}
        />
        <p className="field-description">{field.description}</p>
      </label>
    );
  }

  if (fieldType === "color") {
    const colorValue = typeof value === "string" && value ? value : "#000000";
    return (
      <label className="field-control">
        <span>{field.label}</span>
        <div className="color-row">
          <input type="color" value={colorValue} onChange={(event) => onChange(event.target.value)} />
          <input type="text" value={typeof value === "string" ? value : ""} onChange={(event) => onChange(event.target.value)} />
        </div>
        <p className="field-description">{field.description}</p>
      </label>
    );
  }

  if (fieldType === "select") {
    return (
      <label className="field-control">
        <span>{field.label}</span>
        <select value={typeof value === "string" ? value : String(value ?? "")} onChange={(event) => onChange(event.target.value)}>
          {(field.options || []).map((option) => (
            <option key={String(option.value)} value={String(option.value)}>
              {option.label}
            </option>
          ))}
        </select>
        <p className="field-description">{field.description}</p>
      </label>
    );
  }

  if (fieldType === "string_list") {
    const displayValue = Array.isArray(value) ? (value as string[]).join("\n") : (value as string) || "";
    return (
      <label className="field-control field-control-column">
        <span>{field.label}</span>
        <textarea rows={field.rows || 4} value={displayValue} onChange={(event) => onChange(event.target.value)} />
        <p className="field-description">{field.description}</p>
      </label>
    );
  }

  const rows = field.multiline ? field.rows || 4 : 1;
  return (
    <label className="field-control field-control-column">
      <span>{field.label}</span>
      {field.multiline ? (
        <textarea
          rows={rows}
          value={(value as string) || ""}
          placeholder={field.placeholder || ""}
          onChange={(event) => onChange(event.target.value)}
        />
      ) : (
        <input
          type="text"
          value={(value as string) || ""}
          placeholder={field.placeholder || ""}
          onChange={(event) => onChange(event.target.value)}
        />
      )}
      <p className="field-description">{field.description}</p>
    </label>
  );
}

export default function ConfigForm({ scene, values, onFieldChange, onSave, images, onDeleteImage }: ConfigFormProps) {
  if (!scene) {
    return (
      <div className="panel-card">
        <div className="panel-header">
          <h2>Scene Settings</h2>
        </div>
        <p className="hint">Select a scene to edit its configuration.</p>
      </div>
    );
  }

  return (
    <div className="panel-card">
      <div className="panel-header">
        <div>
          <h2>Scene Settings</h2>
          <p className="hint">{scene.description || "Edit the selected scene using the controls below."}</p>
        </div>
        <button onClick={onSave}>Save scene</button>
      </div>
      <div className="scene-settings-groups">
        {scene.groups.map((group) => (
          <section key={group.key} className="settings-group">
            <div className="settings-group-header">
              <div>
                <h3>{group.label}</h3>
                {group.description && <p className="hint">{group.description}</p>}
              </div>
            </div>
            <div className="config-list">
              {group.fields.map((field) => (
                <FieldInput
                  key={field.key}
                  field={field}
                  value={values[field.key] ?? field.value}
                  onChange={(nextValue) => onFieldChange(field.key, nextValue)}
                  images={images}
                  onDeleteImage={onDeleteImage}
                />
              ))}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}