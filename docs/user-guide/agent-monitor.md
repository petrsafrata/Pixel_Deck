# AI Agent Monitor

The `agent_monitor` scene displays the activity of AI coding agents on Pixel Deck.

The current integration has been tested with local Codex sessions in the ChatGPT desktop app on Windows. A Python hook script runs on the computer hosting Codex and sends authenticated HTTP events to Pixel Deck.

Pixel Deck can run on the same computer or on a Raspberry Pi reachable over the local network.

## States

| State   | Meaning                                  | Display                                        |
|---------|------------------------------------------|------------------------------------------------|
| Idle    | No active or recently completed sessions | Neutral robot and inactive traffic lights      |
| Working | An agent is processing a request         | Robot with a wrench and a red light            |
| Waiting | An agent requires user input or approval | Robot with a speech bubble and an orange light |
| Done    | An agent has finished its response       | Celebrating robot and a green light            |

Done indicates the end of an agent response. It does not verify that the requested task was completed successfully.

The `AI:` counter shows the number of Working and Waiting sessions. Sessions displaying Done are excluded from this counter.

## Scene rotation and automatic switching

With automatic switching enabled:

- Idle monitor frames participate in normal rotation when `agent_monitor` is included in `app.scene_order`.
- Working, Waiting, and Done take priority over other scenes.
- An active monitor remains visible even when its normal rotation duration expires.
- Normal scene rotation resumes when the aggregate state returns to Idle.
- A normal scene interrupted by the monitor resumes with a fresh display interval.

Other scenes remain enabled in the configuration. Automatic switching temporarily suspends their display.

When the monitor is manually selected in single-scene mode, it remains visible in Idle.

## Multiple sessions

Pixel Deck identifies each session by the combination of `agent` and `session_id`.

The aggregate display uses this priority:

1. Waiting
2. Working
3. Done
4. Idle

For example, if one session is Working and another is Waiting, the display shows Waiting. When the waiting session finishes, the display returns to Working while the other session remains active.

Each session has independent expiration timing:

| Setting                     | Current value                                      |
|-----------------------------|----------------------------------------------------|
| Working or Waiting watchdog | 15 minutes since the latest event for that session |
| Done display period         | 10 seconds since the Done event                    |
| Maximum retained sessions   | 256                                                |

These are implementation defaults in `AgentMonitor`, not YAML settings.

Done periods run independently, including while a higher-priority state is displayed. Pixel Deck does not queue an additional ten-second celebration for every completed session.

Expired Working and Waiting sessions are removed without being marked Done.

## Configure Pixel Deck

Merge the following settings into the existing `config/config.yml`. Preserve other scene definitions and application settings.

```yaml
app:
  mode: "rotate"
  scene_order:
    - "clock"
    - "agent_monitor"
    - "weather"

web:
  enabled: true
  host: "0.0.0.0"
  port: 8080
  api_token: "REPLACE_WITH_YOUR_TOKEN"

scenes:
  agent_monitor:
    enabled: true
    auto_switch: true
    duration_s: 10
    fps: 10
    background: "#000000"
```

| Field | Purpose |
|---|---|
| `enabled` | Makes the monitor available for rotation and automatic switching |
| `auto_switch` | Allows agent activity to interrupt normal scenes |
| `duration_s` | Monitor display duration during normal rotation |
| `fps` | Monitor rendering frame rate |
| `background` | Monitor background color |

`duration_s` does not control the watchdog or the Done period.

The monitor does not need to appear in `scene_order` for automatic switching to work. Include it when you also want to display Idle during normal rotation.

To keep displaying agent status without rotation:

```yaml
app:
  mode: "single"
  active_scene: "agent_monitor"
```

Restart Pixel Deck after editing the configuration directly.

## Configure the connection

The hook script reads two environment variables on the computer running Codex:

| Variable | Purpose |
|---|---|
| `PIXEL_DECK_URL` | Base URL of the running Pixel Deck instance |
| `PIXEL_DECK_API_TOKEN` | Token matching `web.api_token` in Pixel Deck |

The script automatically appends `/api/agent-monitor/events` to the base URL.

### Choose the correct URL

| Deployment | Example URL |
|---|---|
| Pixel Deck and Codex on the same computer | `http://localhost:8080` |
| Pixel Deck on a Raspberry Pi | `http://192.168.1.50:8080` |

Replace the example Raspberry Pi address with its actual IP address.

`localhost` always refers to the computer executing the hook script. It does not refer to a remote Raspberry Pi.

For a Raspberry Pi deployment:

- The Codex computer must be able to reach the Raspberry Pi.
- Pixel Deck must listen on a network-accessible interface.
- The firewall must allow the configured port.
- A Docker deployment must publish the web server port.

For example:

```yaml
ports:
  - "8080:8080"
```

Use a stable Raspberry Pi address, such as a DHCP reservation, to avoid changing the hook configuration when its IP changes.

### Set persistent variables on Windows

Run the following commands in PowerShell:

```powershell
[Environment]::SetEnvironmentVariable(
    "PIXEL_DECK_URL",
    "http://localhost:8080",
    "User"
)

[Environment]::SetEnvironmentVariable(
    "PIXEL_DECK_API_TOKEN",
    "REPLACE_WITH_YOUR_TOKEN",
    "User"
)
```

`"User"` means the currently signed-in Windows account. Do not replace it with your Windows username.

To target a Raspberry Pi, change the URL:

```powershell
[Environment]::SetEnvironmentVariable(
    "PIXEL_DECK_URL",
    "http://192.168.1.50:8080",
    "User"
)
```

Completely exit the ChatGPT desktop app, including any background instance, and reopen it after changing these variables.

Persistent changes do not update the environment of already-running processes.

### Set variables for a manual PowerShell test

To make the values available immediately in the current PowerShell:

```powershell
$env:PIXEL_DECK_URL = "http://localhost:8080"
$env:PIXEL_DECK_API_TOKEN = "REPLACE_WITH_YOUR_TOKEN"
```

These assignments affect the current PowerShell and processes started from it.

### Inspect the configuration

Read the saved URL:

```powershell
[Environment]::GetEnvironmentVariable("PIXEL_DECK_URL", "User")
```

Check whether a token is saved without printing it:

```powershell
$token = [Environment]::GetEnvironmentVariable(
    "PIXEL_DECK_API_TOKEN",
    "User"
)

-not [string]::IsNullOrWhiteSpace($token)
```

The token check should return `True`.

## Install the hook script

Place `scripts/agent_monitor_hook.py` on the computer running Codex.

The script uses the Python standard library. The agent computer does not need the Pixel Deck rendering dependencies.

The script may be stored outside the Pixel Deck repository. Use its actual absolute path in the hook configuration.

Verify that Python is available:

```powershell
python --version
```

If the desktop app cannot resolve `python`, use the absolute path to a Python executable in the hook commands.

Only the following fields are sent to Pixel Deck:

- `agent`
- `session_id`
- `event`

Prompt contents, tool arguments, and transcripts are not forwarded.

## Configure Codex hooks

For all local projects, create:

```text
%USERPROFILE%\.codex\hooks.json
```

Alternatively, use `.codex/hooks.json` inside a specific project.

Avoid registering the same integration in both locations, as matching hooks can run more than once.

If the file already exists, merge the following entries with its existing hooks.

Replace `C:/Projects/Pixel_Deck` in every command with the actual path to your script.

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python \"C:/Projects/Pixel_Deck/scripts/agent_monitor_hook.py\" --agent codex",
            "timeout": 3
          }
        ]
      }
    ],
    "PreModelRequest": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python \"C:/Projects/Pixel_Deck/scripts/agent_monitor_hook.py\" --agent codex",
            "timeout": 3
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python \"C:/Projects/Pixel_Deck/scripts/agent_monitor_hook.py\" --agent codex",
            "timeout": 3
          }
        ]
      }
    ],
    "PermissionRequest": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python \"C:/Projects/Pixel_Deck/scripts/agent_monitor_hook.py\" --agent codex",
            "timeout": 3
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python \"C:/Projects/Pixel_Deck/scripts/agent_monitor_hook.py\" --agent codex",
            "timeout": 3
          }
        ]
      }
    ],
    "PreCompact": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python \"C:/Projects/Pixel_Deck/scripts/agent_monitor_hook.py\" --agent codex",
            "timeout": 3
          }
        ]
      }
    ],
    "PostCompact": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python \"C:/Projects/Pixel_Deck/scripts/agent_monitor_hook.py\" --agent codex",
            "timeout": 3
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python \"C:/Projects/Pixel_Deck/scripts/agent_monitor_hook.py\" --agent codex",
            "timeout": 3
          }
        ]
      }
    ],
    "Interrupt": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python \"C:/Projects/Pixel_Deck/scripts/agent_monitor_hook.py\" --agent codex",
            "timeout": 3
          }
        ]
      }
    ],
    "SessionEnd": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python \"C:/Projects/Pixel_Deck/scripts/agent_monitor_hook.py\" --agent codex",
            "timeout": 3
          }
        ]
      }
    ]
  }
}
```

Ensure the file is named `hooks.json`, not `hooks.json.txt`.

### Enable and trust the hooks

In the ChatGPT desktop app:

1. Open the local Codex environment.
2. Open **Settings → Hooks** or the available **Review hooks** action.
3. Review the commands and grant trust.
4. Ensure the hooks are enabled.
5. Start a new local Codex conversation to test the integration.

This setup targets local Codex execution. Cloud-orchestrated ChatGPT Work does not load these local command hooks.

See the [official Codex hooks documentation](https://learn.chatgpt.com/docs/hooks) for environment support and trust requirements.

### Event mapping

| Codex hook | Pixel Deck event |
|---|---|
| `UserPromptSubmit` | `working` |
| `PreToolUse` | `working` |
| `PermissionRequest` | `waiting` |
| `PostToolUse` | `working` |
| `Stop` | `done` |
| `Interrupt` | `stopped` |
| `SessionEnd` | `stopped` |

The hook script ignores child-agent events containing `agent_id`. Independent main sessions are tracked separately.

## Verify the integration

Keep Pixel Deck running throughout these tests.

### Test the script directly

Set the connection variables in the current PowerShell, then send a simulated prompt event:

```powershell
'{"session_id":"codex-test","hook_event_name":"UserPromptSubmit"}' |
    python "C:/Projects/Pixel_Deck/scripts/agent_monitor_hook.py" --agent codex
```

Pixel Deck should display Working.

Send a completion event:

```powershell
'{"session_id":"codex-test","hook_event_name":"Stop"}' |
    python "C:/Projects/Pixel_Deck/scripts/agent_monitor_hook.py" --agent codex
```

Pixel Deck should display Done and return to normal scenes after ten seconds.

To remove the test session immediately:

```powershell
'{"session_id":"codex-test","hook_event_name":"SessionEnd"}' |
    python "C:/Projects/Pixel_Deck/scripts/agent_monitor_hook.py" --agent codex
```

### Test Codex

Open a local project in Codex and submit a short request, such as:

> Inspect the project structure and summarize its main components. Do not modify files.

Expected behavior:

1. Working appears while Codex processes the request.
2. Done appears when Codex finishes responding.
3. Normal rotation resumes after the Done period.
4. Idle appears when the monitor next reaches its normal position in rotation.

## HTTP API

Other integrations can report activity directly through the same API.

Both endpoints require either:

```http
X-API-Token: YOUR_TOKEN
```

or:

```http
Authorization: Bearer YOUR_TOKEN
```

### Submit an event

```http
POST /api/agent-monitor/events
Content-Type: application/json
```

Request body:

```json
{
  "agent": "codex",
  "session_id": "example-session",
  "event": "working"
}
```

| Field | Description |
|---|---|
| `agent` | Agent identifier, up to 64 characters |
| `session_id` | Session identifier, up to 256 characters |
| `event` | `working`, `waiting`, `done`, or `stopped` |

Use the same agent and session identifiers throughout a session.

Agent identifiers are normalized to lowercase. Session identifiers are case-sensitive. Leading and trailing whitespace is removed.

| Event | Effect |
|---|---|
| `working` | Marks the session Working and refreshes its watchdog |
| `waiting` | Marks the session Waiting and refreshes its watchdog |
| `done` | Starts a ten-second Done period for the session |
| `stopped` | Removes the session immediately |

A repeated Done event restarts that session's Done period.

Example PowerShell request:

```powershell
$headers = @{
    "X-API-Token" = $env:PIXEL_DECK_API_TOKEN
}

$body = @{
    agent = "codex"
    session_id = "example-session"
    event = "working"
} | ConvertTo-Json

Invoke-RestMethod `
    -Method Post `
    -Uri "$env:PIXEL_DECK_URL/api/agent-monitor/events" `
    -Headers $headers `
    -ContentType "application/json" `
    -Body $body
```

Example response:

```json
{
  "state": "working",
  "working_count": 1,
  "waiting_count": 0,
  "done_count": 0,
  "active_count": 1
}
```

### Read the current status

```http
GET /api/agent-monitor/status
```

```powershell
Invoke-RestMethod `
    -Method Get `
    -Uri "$env:PIXEL_DECK_URL/api/agent-monitor/status" `
    -Headers @{
        "X-API-Token" = $env:PIXEL_DECK_API_TOKEN
    }
```

Reading status removes expired sessions before returning the result. It does not refresh their watchdogs.

### Error responses

| HTTP status | Possible cause |
|---|---|
| `401` | Missing or invalid API token |
| `422` | Invalid event or request fields |
| `503` | No server API token configured, or the session limit was reached |

## Troubleshooting

### Manual events work, but Codex does not update the display

Check that:

- The hooks are loaded, trusted, and enabled.
- Every hook points to the correct script.
- Python is available to the desktop app.
- The app was fully restarted after environment variables were saved.
- The conversation runs in a local Codex environment.

Check any hook error messages reported by Codex.

### The script reports missing connection settings

Verify that both persistent environment variables exist.

For manual tests, also set `$env:PIXEL_DECK_URL` and `$env:PIXEL_DECK_API_TOKEN` in the current PowerShell, or open a new PowerShell that has loaded the updated environment.

### The API reports an invalid token

Use the token from the configuration of the Pixel Deck instance receiving the request.

A local development instance and a Raspberry Pi instance may have different tokens.

### The Raspberry Pi cannot be reached

Check its IP address, network connectivity, firewall, web server binding, and Docker port publishing.

From the Codex computer, open:

```text
http://<raspberry-pi-ip>:8080/
```

Do not use `localhost` to address a different computer.

### API status changes, but rotation continues

Check:

```yaml
scenes:
  agent_monitor:
    enabled: true
    auto_switch: true
```

Also verify that the application includes automatic monitor switching in its scene loop.

### Waiting remains visible after approval

The current integration restores Working through `PostToolUse`.

A long-running approved tool may therefore remain displayed as Waiting until the tool finishes.

### A session disappears during a long operation

There is no periodic heartbeat yet. Working and Waiting expire fifteen minutes after the latest event for that session.

A long operation without further events can exceed this timeout.

### Idle appears during normal rotation

This is expected when `agent_monitor` is included in `app.scene_order`.

Remove it from the rotation order if you only want to see the monitor during agent activity. Keep `enabled` and `auto_switch` set to `true`.

## Current limitations

- Periodic heartbeats are not implemented.
- Child agents are not tracked as independent sessions by the supplied script.
- Done represents response completion rather than verified task success.
- Waiting may remain visible until an approved tool finishes.
- Arbitrary questions in a completed response are not classified as Waiting.
- Hook delivery is best effort, with a one-second HTTP timeout and no retry queue.
- Sessions are held in memory and are cleared when Pixel Deck restarts.
- Activity is detected by the rendering loop, so a blocking scene update can delay switching.
- HTTP traffic is not encrypted by the built-in server; use this setup on a trusted local network.