"""Simple HTTP API for controlling the stress detection pipeline.

Endpoints:
- GET  /api/health  : Health check and run-state snapshot
- GET  /api/status  : Latest runtime metrics
- POST /api/start   : Start camera + stress detection loop (accepts JSON overrides)
- POST /api/stop    : Stop camera + stress detection loop

This server uses only Python standard library modules.
"""

from __future__ import annotations

import importlib
import json
import os
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Optional

import app_config

HOST = os.getenv("FACIAL_API_HOST", "127.0.0.1")
PORT = int(os.getenv("FACIAL_API_PORT", "8002"))


class PipelineController:
    """Thread-safe controller for the stress detection runtime.

    This controller defers importing the heavy `stress_detector` module until
    after any runtime configuration overrides are applied to `app_config`.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._running = False
        self._worker: threading.Thread | None = None
        self._last_error: str | None = None
        self._stress_detector = None

    @staticmethod
    def get_config_keys() -> Dict[str, Any]:
        """Return a dict of all configurable (uppercase) keys and their current values."""
        result = {}
        for key in dir(app_config):
            if key.startswith("_"):
                continue
            if key.isupper():
                try:
                    result[key] = getattr(app_config, key)
                except Exception:
                    pass
        return result

    def _apply_config_overrides(self, overrides: Optional[Dict[str, Any]]) -> tuple[bool, Optional[str]]:
        """Apply config overrides with validation.

        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        if not overrides:
            return (True, None)

        errors = []
        for key, value in overrides.items():
            if not isinstance(key, str):
                errors.append(f"Key must be string, got {type(key).__name__}")
                continue

            if not key.isupper():
                errors.append(f"Key '{key}' must be uppercase (config keys are UPPERCASE_LIKE)")
                continue

            if not hasattr(app_config, key):
                errors.append(f"Unknown config key '{key}'")
                continue

            try:
                old_value = getattr(app_config, key)
                old_type = type(old_value)

                # Try to coerce value to the original type if needed.
                if not isinstance(value, old_type):
                    if old_type is bool and isinstance(value, str):
                        value = value.lower() in ("true", "1", "yes")
                    elif old_type is (int, float) and isinstance(value, str):
                        value = old_type(value)
                    elif isinstance(value, (int, float)) and old_type in (int, float):
                        value = old_type(value)

                setattr(app_config, key, value)
            except Exception as exc:
                errors.append(f"Failed to set '{key}' to {value!r}: {exc}")

        if errors:
            return (False, "; ".join(errors))
        return (True, None)

    def start(self, config_overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        with self._lock:
            if self._running:
                return {
                    "ok": True,
                    "message": "Pipeline already running",
                    "running": True,
                }

            self._last_error = None

            # Apply config overrides before importing the pipeline modules so
            # modules that import values from `app_config` at import-time will
            # pick up the updated values.
            success, error_msg = self._apply_config_overrides(config_overrides)
            if not success:
                self._last_error = error_msg
                return {"ok": False, "message": f"Config validation failed: {error_msg}", "running": False}

            try:
                self._stress_detector = importlib.import_module("stress_detector")
            except Exception as exc:
                self._last_error = f"Failed to import pipeline modules: {exc}"
                return {"ok": False, "message": self._last_error, "running": False}

            try:
                self._stress_detector.start_stress_detection()
            except Exception as exc:
                self._last_error = str(exc)
                return {"ok": False, "message": f"Failed to start pipeline: {exc}", "running": False}

            self._running = True
            self._worker = threading.Thread(
                target=self._worker_loop,
                daemon=True,
                name="stress-api-worker",
            )
            self._worker.start()

            return {
                "ok": True,
                "message": "Pipeline started",
                "running": True,
            }

    def stop(self) -> Dict[str, Any]:
        with self._lock:
            if not self._running:
                return {
                    "ok": True,
                    "message": "Pipeline already stopped",
                    "running": False,
                }

            self._running = False

        worker = self._worker
        if worker is not None:
            worker.join(timeout=2.0)

        with self._lock:
            try:
                if self._stress_detector is not None:
                    self._stress_detector.stop_stress_detection()
            except Exception:
                pass
            self._worker = None
            self._stress_detector = None
            return {
                "ok": True,
                "message": "Pipeline stopped",
                "running": False,
            }

    def status(self) -> Dict[str, Any]:
        with self._lock:
            status = {}
            try:
                if self._stress_detector is not None:
                    status = self._stress_detector.get_current_status()
            except Exception:
                status = {}

            return {
                "ok": True,
                "running": self._running,
                "last_error": self._last_error,
                "status": status,
            }

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "ok": True,
                "running": self._running,
                "last_error": self._last_error,
            }

    def _worker_loop(self) -> None:
        while True:
            with self._lock:
                if not self._running:
                    break

            try:
                if self._stress_detector is not None:
                    self._stress_detector.process_next_step()
            except Exception as exc:  # Keep endpoint responsive on runtime failures.
                with self._lock:
                    self._last_error = str(exc)
                    self._running = False
                break


controller = PipelineController()


class StressAPIHandler(BaseHTTPRequestHandler):
    """HTTP request handler exposing a minimal REST-like interface."""

    server_version = "StressAPIServer/1.0"

    def do_OPTIONS(self) -> None:
        self._send_json(HTTPStatus.NO_CONTENT, {})

    def do_GET(self) -> None:
        if self.path == "/api/health":
            self._send_json(HTTPStatus.OK, controller.snapshot())
            return

        if self.path == "/api/status":
            self._send_json(HTTPStatus.OK, controller.status())
            return

        if self.path == "/api/config":
            config = PipelineController.get_config_keys()
            self._send_json(HTTPStatus.OK, {
                "ok": True,
                "config": config,
            })
            return

        self._send_json(
            HTTPStatus.NOT_FOUND,
            {"ok": False, "error": f"Unknown endpoint: {self.path}"},
        )

    def _read_json_body(self) -> Optional[Dict[str, Any]]:
        length = int(self.headers.get("Content-Length", 0) or 0)
        if length <= 0:
            return None
        try:
            raw = self.rfile.read(length)
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return None

    def do_POST(self) -> None:
        if self.path == "/api/start":
            try:
                overrides = self._read_json_body()
                if overrides is not None and not isinstance(overrides, dict):
                    self._send_json(
                        HTTPStatus.BAD_REQUEST,
                        {"ok": False, "error": "Request body must be a JSON object with config overrides."},
                    )
                    return

                payload = controller.start(config_overrides=overrides)
                status_code = HTTPStatus.OK if payload.get("ok", False) else HTTPStatus.BAD_REQUEST
                self._send_json(status_code, payload)
            except Exception as exc:
                self._send_json(
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    {"ok": False, "error": f"Failed to start pipeline: {exc}"},
                )
            return

        if self.path == "/api/stop":
            try:
                payload = controller.stop()
                self._send_json(HTTPStatus.OK, payload)
            except Exception as exc:
                self._send_json(
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    {"ok": False, "error": f"Failed to stop pipeline: {exc}"},
                )
            return

        self._send_json(
            HTTPStatus.NOT_FOUND,
            {"ok": False, "error": f"Unknown endpoint: {self.path}"},
        )

    def log_message(self, format: str, *args: Any) -> None:
        # Keep terminal output concise while serving frontend requests.
        return

    def _send_json(self, status: HTTPStatus, payload: Dict[str, Any]) -> None:
        response = json.dumps(payload).encode("utf-8")

        self.send_response(status.value)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

        if self.command != "OPTIONS":
            self.wfile.write(response)


def run_server(host: str = HOST, port: int = PORT) -> None:
    """Run the API server until interrupted."""
    server = ThreadingHTTPServer((host, port), StressAPIHandler)
    print(f"Stress API server listening on http://{host}:{port}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        try:
            controller.stop()
        except Exception:
            pass
        server.server_close()
        print("Stress API server shut down.")


if __name__ == "__main__":
    run_server()
