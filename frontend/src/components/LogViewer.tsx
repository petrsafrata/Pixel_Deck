import React, { useEffect, useMemo, useRef, useState } from "react";

import type { LogEntry } from "../types";

type LogViewerProps = {
  logs: LogEntry[];
  logLevel: string;
  limit: number;
  onLevelChange: (value: string) => void;
  onLimitChange: (value: number) => void;
  onRefresh: () => void;
  onClear: () => Promise<void> | void;
};

function formatIso(value: string): string {
  if (!value) {
    return "-";
  }
  try {
    return new Date(value).toLocaleString();
  } catch (error) {
    return value;
  }
}

export default function LogViewer({ logs, logLevel, limit, onLevelChange, onLimitChange, onRefresh, onClear }: LogViewerProps) {
  const [search, setSearch] = useState("");
  const [autoScroll, setAutoScroll] = useState(true);
  const containerRef = useRef<HTMLDivElement | null>(null);

  const visibleLogs = useMemo(() => {
    const needle = search.trim().toLowerCase();
    if (!needle) {
      return logs;
    }
    return logs.filter((entry) => {
      const haystack = [entry.timestamp, entry.level, entry.logger, entry.message].join(" ").toLowerCase();
      return haystack.includes(needle);
    });
  }, [logs, search]);

  useEffect(() => {
    if (!autoScroll || !containerRef.current) {
      return;
    }
    containerRef.current.scrollTop = containerRef.current.scrollHeight;
  }, [autoScroll, visibleLogs]);

  const handleCopyLogs = async () => {
    const text = visibleLogs
      .map((entry) => `${formatIso(entry.timestamp)} [${entry.level}] ${entry.logger}: ${entry.message}`)
      .join("\n");
    await navigator.clipboard.writeText(text);
  };

  return (
    <div className="panel-card">
      <div className="panel-header">
        <div>
          <h2>Logs</h2>
          <p className="hint">Search, filter, copy, and clear log output.</p>
        </div>
        <span className="badge">{visibleLogs.length} shown</span>
      </div>
      <div className="log-toolbar">
        <label>
          Level
          <select value={logLevel} onChange={(event) => onLevelChange(event.target.value)}>
            <option value="">All</option>
            <option value="DEBUG">DEBUG</option>
            <option value="INFO">INFO</option>
            <option value="WARNING">WARNING</option>
            <option value="ERROR">ERROR</option>
            <option value="CRITICAL">CRITICAL</option>
          </select>
        </label>
        <label>
          Entries
          <input type="number" min={20} max={2000} step={10} value={limit} onChange={(event) => onLimitChange(Number(event.target.value) || 200)} />
        </label>
        <label className="log-search">
          Search
          <input type="search" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search logs" />
        </label>
      </div>
      <div className="log-toolbar log-toolbar-actions">
        <label className="toggle-row">
          <input type="checkbox" checked={autoScroll} onChange={(event) => setAutoScroll(event.target.checked)} />
          <span>Auto-scroll</span>
        </label>
        <div className="button-row">
          <button className="secondary" onClick={handleCopyLogs} disabled={visibleLogs.length === 0}>
            Copy logs
          </button>
          <button className="secondary" onClick={onClear} disabled={visibleLogs.length === 0}>
            Clear logs
          </button>
          <button className="secondary" onClick={onRefresh}>
            Refresh
          </button>
        </div>
      </div>
      <div className="button-row log-actions-bottom">
        <button className="secondary" onClick={() => setSearch("")}>Clear search</button>
      </div>
      <div className="logs" ref={containerRef}>
        {visibleLogs.map((entry, index) => (
          <div key={`${entry.timestamp}-${index}`} className={`log-line log-level-${entry.level}`}>
            <span>{formatIso(entry.timestamp)}</span>
            <span className="log-badge">{entry.level}</span>
            <span>{entry.logger}</span>
            <span>{entry.message}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

