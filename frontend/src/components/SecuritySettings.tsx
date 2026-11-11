import React from "react";

type SecuritySettingsProps = {
  token: string;
  onTokenChange: (value: string) => void;
  onSaveToken: () => void;
};

export default function SecuritySettings({ token, onTokenChange, onSaveToken }: SecuritySettingsProps) {
  return (
    <div className="panel-card">
      <div className="panel-header">
        <div>
          <h2>Settings</h2>
          <p className="hint">Security and local access controls.</p>
        </div>
      </div>

      <section className="settings-group">
        <div className="settings-group-header">
          <div>
            <h3>Security</h3>
            <p className="hint">Stored locally in the browser and sent as the X-API-Token header.</p>
          </div>
        </div>
        <label className="field-control field-control-column">
          <span>API token</span>
          <input
            type="password"
            value={token}
            onChange={(event) => onTokenChange(event.target.value)}
            placeholder="Enter API token"
          />
        </label>
        <div className="button-row">
          <button onClick={onSaveToken}>Save token</button>
        </div>
      </section>
    </div>
  );
}
