"""Background pollers — one per active student session.
Each poller pulls latest state from the EEG sidecar and inserts a row
into Supabase `cognitive_signals`."""
from __future__ import annotations

import os
import threading
import time
from typing import Dict

import eeg_client

POLL_INTERVAL = 1.0 / max(0.5, float(os.getenv("EEG_POLL_HZ", "1")))


class _Poller(threading.Thread):
    def __init__(self, supabase, user_id: str, session_id: str):
        super().__init__(daemon=True)
        self.supabase   = supabase
        self.user_id    = user_id
        self.session_id = session_id
        self._stop      = threading.Event()
        self.last_ts    = None
        self.samples    = 0
        self.errors     = 0

    def run(self):
        # ensure the sidecar's stream is running
        try:
            eeg_client.start_session()
        except Exception as e:
            print(f"[eeg-poller] could not start eeg session: {e}")

        print(f"[eeg-poller] started user={self.user_id[:8]} session={self.session_id[:8]}")

        while not self._stop.is_set():
            data = eeg_client.get_state()
            if data and data.get("timestamp") and data["timestamp"] != self.last_ts:
                self.last_ts = data["timestamp"]
                row = eeg_client.map_eeg_to_cognitive(data, self.session_id, self.user_id)
                try:
                    self.supabase.table("cognitive_signals").insert(row).execute()
                    self.samples += 1
                except Exception as e:
                    self.errors += 1
                    if self.errors <= 3:
                        print(f"[eeg-poller] insert failed: {e}")
            time.sleep(POLL_INTERVAL)

        print(f"[eeg-poller] stopped user={self.user_id[:8]} session={self.session_id[:8]} samples={self.samples}")

    def stop(self):
        self._stop.set()


# session_id -> Poller
_active: Dict[str, _Poller] = {}
_lock = threading.Lock()


def start(supabase, user_id: str, session_id: str) -> dict:
    with _lock:
        if session_id in _active and _active[session_id].is_alive():
            return {"running": True, "already": True}
        # only one live poller per learner
        for sid, p in list(_active.items()):
            if p.user_id == user_id:
                p.stop()
                _active.pop(sid, None)
        p = _Poller(supabase, user_id, session_id)
        p.start()
        _active[session_id] = p
        return {"running": True, "already": False}


def stop(session_id: str) -> dict:
    with _lock:
        p = _active.pop(session_id, None)
        if p:
            p.stop()
            return {"running": False, "samples": p.samples}
        return {"running": False, "samples": 0}


def stop_for_user(user_id: str) -> int:
    stopped = 0
    with _lock:
        for sid, p in list(_active.items()):
            if p.user_id == user_id:
                p.stop()
                _active.pop(sid, None)
                stopped += 1
    return stopped


def status(user_id: str) -> dict:
    with _lock:
        for sid, p in _active.items():
            if p.user_id == user_id and p.is_alive():
                return {
                    "running":    True,
                    "session_id": sid,
                    "samples":    p.samples,
                    "errors":     p.errors,
                    "last_ts":    p.last_ts,
                }
    return {"running": False}