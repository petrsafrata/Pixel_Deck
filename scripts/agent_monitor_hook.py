from __future__ import annotations

import argparse
import json
import os
import sys
from urllib.request import Request, urlopen


def build_event(data: dict, agent: str) -> dict | None:
    session_id = data.get("session_id")
    if not isinstance(session_id, str) or not session_id.strip():
        return None

    # Track independent main sessions; child hooks must not overwrite them.
    if data.get("agent_id"):
        return None

    hook = data.get("hook_event_name")
    event = None

    if hook in {"UserPromptSubmit", "PreModelRequest", "PreCompact", "PostCompact"}:
        event = "working"

    elif hook == "PreToolUse":
        event = (
            "waiting"
            if data.get("tool_name") in {"AskUserQuestion", "ExitPlanMode"}
            else "working"
        )

    elif hook in {"PermissionRequest", "Elicitation"}:
        event = "waiting"

    elif hook in {"PostToolUse", "ElicitationResult"}:
        event = "working"

    elif hook == "PostToolUseFailure":
        event = "stopped" if data.get("is_interrupt") else "working"

    elif hook == "Stop":
        event = "done"

    elif hook in {"SessionEnd", "StopFailure", "Interrupt"}:
        event = "stopped"

    if event is None:
        return None

    return {
        "agent": agent,
        "session_id": session_id.strip(),
        "event": event,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--agent",
        choices=("claude", "codex"),
        required=True,
    )
    args = parser.parse_args()

    try:
        data = json.load(sys.stdin)
        if not isinstance(data, dict):
            raise ValueError("Hook input must be a JSON object")

        payload = build_event(data, args.agent)
        if payload is None:
            return 0

        base_url = (
            os.environ.get("PIXEL_DECK_URL", "")
            .strip()
            .rstrip("/")
        )
        token = os.environ.get("PIXEL_DECK_API_TOKEN", "").strip()

        if not base_url or not token:
            print(
                "PixelDeck: URL or API token is missing.",
                file=sys.stderr,
            )
            return 0

        request = Request(
            base_url + "/api/agent-monitor/events",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "X-API-Token": token,
            },
            method="POST",
        )

        with urlopen(request, timeout=1.0):
            pass

    except Exception as exc:
        # Monitoring failures must not change permissions or block work.
        # Avoid printing request contents or credentials.
        print(
            f"PixelDeck: event delivery failed ({type(exc).__name__}).",
            file=sys.stderr,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())