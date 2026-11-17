from __future__ import annotations

import math
import threading
import time
from dataclasses import dataclass
from enum import Enum


class AgentState(str, Enum):
    IDLE = "idle"
    WORKING = "working"
    WAITING = "waiting"
    DONE = "done"


class AgentEvent(str, Enum):
    WORKING = "working"
    WAITING = "waiting"
    DONE = "done"
    STOPPED = "stopped"


@dataclass(frozen=True)
class AgentSession:
    agent: str
    session_id: str
    state: AgentState
    updated_at: float


@dataclass(frozen=True)
class AgentMonitorSnapshot:
    state: AgentState
    working_count: int
    waiting_count: int
    done_count: int

    @property
    def active_count(self) -> int:
        return self.working_count + self.waiting_count


class AgentMonitor:
    """
    Thread-safe session state shared by the API and rendering loop.

    Expiration uses monotonic time, so system clock changes do not affect
    the watchdog or the duration of the Done state.

    Expired sessions are removed when an event or snapshot is processed.
    No background thread is required.
    """

    def __init__(
        self,
        watchdog_timeout_s: float = 900.0,
        done_duration_s: float = 10.0,
        max_sessions: int = 256,
    ):
        self._watchdog_timeout_s = self._positive_duration(
            watchdog_timeout_s, "watchdog_timeout_s"
        )
        self._done_duration_s = self._positive_duration(
            done_duration_s, "done_duration_s"
        )

        if (
            isinstance(max_sessions, bool)
            or not isinstance(max_sessions, int)
            or max_sessions < 1
        ):
            raise ValueError("max_sessions must be a positive integer")

        self._max_sessions = max_sessions
        self._lock = threading.Lock()
        self._sessions: dict[tuple[str, str], AgentSession] = {}

    @staticmethod
    def _positive_duration(value: float, name: str) -> float:
        duration = float(value)
        if not math.isfinite(duration) or duration <= 0:
            raise ValueError(f"{name} must be a finite positive number")
        return duration

    def handle_event(
        self,
        agent: str,
        session_id: str,
        event: AgentEvent | str,
    ) -> AgentMonitorSnapshot:
        """
        Apply an event and return the resulting aggregate state.

        Working and Waiting refresh that session's watchdog.
        Done starts the session's completion display period.
        Stopped removes the session immediately.

        Raises ValueError for invalid input and OverflowError when a new
        session would exceed the configured capacity.
        """
        agent = agent.strip().lower()
        session_id = session_id.strip()
        event = AgentEvent(event)

        if not agent:
            raise ValueError("agent must not be empty")
        if not session_id:
            raise ValueError("session_id must not be empty")

        key = (agent, session_id)

        with self._lock:
            now = time.monotonic()
            self._remove_expired(now)

            if event == AgentEvent.STOPPED:
                self._sessions.pop(key, None)
            else:
                if (
                    key not in self._sessions
                    and len(self._sessions) >= self._max_sessions
                ):
                    raise OverflowError("Agent monitor session limit reached")

                self._sessions[key] = AgentSession(
                    agent=agent,
                    session_id=session_id,
                    state=AgentState(event.value),
                    updated_at=now,
                )

            return self._build_snapshot()

    def get_snapshot(self) -> AgentMonitorSnapshot:
        """Return an immutable snapshot after removing expired sessions."""
        with self._lock:
            self._remove_expired(time.monotonic())
            return self._build_snapshot()

    def _remove_expired(self, now: float) -> None:
        """Called only while holding the lock."""
        expired = []

        for key, session in self._sessions.items():
            timeout = (
                self._done_duration_s
                if session.state == AgentState.DONE
                else self._watchdog_timeout_s
            )

            if now - session.updated_at >= timeout:
                expired.append(key)

        for key in expired:
            del self._sessions[key]

    def _build_snapshot(self) -> AgentMonitorSnapshot:
        """Called only while holding the lock."""
        working = 0
        waiting = 0
        done = 0

        for session in self._sessions.values():
            if session.state == AgentState.WAITING:
                waiting += 1
            elif session.state == AgentState.WORKING:
                working += 1
            elif session.state == AgentState.DONE:
                done += 1

        if waiting:
            state = AgentState.WAITING
        elif working:
            state = AgentState.WORKING
        elif done:
            state = AgentState.DONE
        else:
            state = AgentState.IDLE

        return AgentMonitorSnapshot(
            state=state,
            working_count=working,
            waiting_count=waiting,
            done_count=done,
        )