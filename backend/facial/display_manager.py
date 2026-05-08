import cv2
import numpy as np
import matplotlib.pyplot as plt
from app_config import (
    SHOW_EMOTION_GRAPH,
    SHOW_STRESS_GRAPH,
    SHOW_WEBCAM,
    SHOW_STRESS_OVERLAY_TEXT,
    SHOW_FACE_BOUNDING_BOX,
    SHOW_FACE_LANDMARKS,
    STRESS_HISTORY_LIMIT,
    WEBCAM_WINDOW_TITLE,
    SHOW_STATUS_WINDOW,
    STATUS_WINDOW_TITLE,
    BOUNDING_BOX_COLOR_BGR,
    BOUNDING_BOX_THICKNESS,
    SHOW_BOUNDING_BOX_CONFIDENCE,
    LANDMARK_COLOR_BGR,
    LANDMARK_RADIUS,
    LANDMARK_THICKNESS,
    SHOW_PERFORMANCE_OVERLAY,
    SHOW_PERFORMANCE_STATUS,
)


class LiveDisplayManager:
    """Owns all display concerns: webcam overlay and matplotlib graphs."""

    def __init__(self):
        self.latest_stress_text = "Stress: N/A"
        self.latest_face_boxes = []
        self.latest_landmark_points = []
        self.current_fps = 0.0
        self.current_queue_depth = 0
        self.current_queue_capacity = 0

        # Emotion graph state
        self.emotion_order = ["anger", "disgust", "fear", "happiness", "sadness", "surprise", "neutral"]
        self.emotion_fig = None
        self.emotion_ax = None
        self.emotion_bars = None

        # Stress graph state
        self.stress_fig = None
        self.stress_ax = None
        self.stress_raw_line = None
        self.stress_smooth_line = None
        self.stress_history_raw = []
        self.stress_history_smoothed = []
        self.stress_frame_index = 0
        self.stress_history_limit = STRESS_HISTORY_LIMIT

        # Status window state
        self.status_rows = {
            "Face detection": (False, "waiting"),
            "Bounding boxes": (False, "waiting"),
            "Landmark points": (False, "waiting"),
            "Emotion values": (False, "waiting"),
            "Stress value": (False, "waiting"),
            "Emotion graph": (SHOW_EMOTION_GRAPH, "enabled" if SHOW_EMOTION_GRAPH else "disabled"),
            "Stress graph": (SHOW_STRESS_GRAPH, "enabled" if SHOW_STRESS_GRAPH else "disabled"),
        }

    def initialize(self):
        """Initialize all graph windows in interactive mode."""
        plt.ion()
        if SHOW_EMOTION_GRAPH:
            self._init_emotion_graph()
        if SHOW_STRESS_GRAPH:
            self._init_stress_graph()

    def reset_stress_history(self):
        """Reset stress graph data for a new capture session."""
        self.stress_history_raw.clear()
        self.stress_history_smoothed.clear()
        self.stress_frame_index = 0

        if self.stress_raw_line is not None and self.stress_smooth_line is not None and SHOW_STRESS_GRAPH:
            self.stress_raw_line.set_data([], [])
            self.stress_smooth_line.set_data([], [])
            self.stress_ax.set_xlim(0, 1)
            self.stress_fig.canvas.draw_idle()
            self.stress_fig.canvas.flush_events()
            plt.pause(0.001)

    def set_stress_text(self, text):
        self.latest_stress_text = text

    def set_face_boxes(self, boxes):
        """Store latest face boxes as (x, y, w, h, score|None)."""
        self.latest_face_boxes = boxes or []

    def set_landmark_points(self, points):
        """Store latest landmark points as list of (x, y) tuples."""
        self.latest_landmark_points = points or []

    def set_status(self, key, ok, message):
        """Set a status row value shown in the status window."""
        self.status_rows[key] = (bool(ok), str(message))

    def set_runtime_metrics(self, fps, queue_depth, queue_capacity):
        """Store current runtime performance metrics for overlay/status display."""
        self.current_fps = float(max(0.0, fps))
        self.current_queue_depth = int(max(0, queue_depth))
        self.current_queue_capacity = int(max(0, queue_capacity))

    def _normalize_box_for_frame(self, x, y, w, h, frame_width, frame_height):
        """Normalize box to xywh pixels within current frame.

        Handles likely xyxy input and normalized [0,1] coordinates.
        """
        x = float(x)
        y = float(y)
        w = float(w)
        h = float(h)

        # If coordinates appear normalized (0..1), scale to pixels.
        if 0.0 <= x <= 1.0 and 0.0 <= y <= 1.0 and 0.0 < w <= 1.5 and 0.0 < h <= 1.5:
            x *= frame_width
            y *= frame_height
            w *= frame_width
            h *= frame_height

        # Heuristic: if box overflows heavily, it is likely xyxy (x1, y1, x2, y2).
        if (x + w > frame_width * 1.1 or y + h > frame_height * 1.1) and w > x and h > y:
            w = w - x
            h = h - y

        # Clamp to valid drawable region.
        x = max(0.0, min(x, frame_width - 1.0))
        y = max(0.0, min(y, frame_height - 1.0))
        w = max(1.0, min(w, frame_width - x))
        h = max(1.0, min(h, frame_height - y))

        return int(x), int(y), int(w), int(h)

    def update_emotions(self, emotions):
        """Update the emotion bar chart from a label->value mapping."""
        if self.emotion_bars is None:
            return

        if not emotions:
            values = [0.0 for _ in self.emotion_order]
        else:
            values = [float(emotions.get(label, 0.0)) for label in self.emotion_order]

        for bar, value in zip(self.emotion_bars, values):
            bar.set_height(value)

        self.emotion_fig.canvas.draw_idle()
        self.emotion_fig.canvas.flush_events()
        plt.pause(0.001)

    def update_stress(self, raw_stress, smoothed_stress):
        """Append and draw stress trend values."""
        if not SHOW_STRESS_GRAPH:
            return

        self.stress_history_raw.append((self.stress_frame_index, float(raw_stress)))
        self.stress_history_smoothed.append((self.stress_frame_index, float(smoothed_stress)))
        self.stress_frame_index += 1

        if len(self.stress_history_raw) > self.stress_history_limit:
            self.stress_history_raw = self.stress_history_raw[-self.stress_history_limit :]
            self.stress_history_smoothed = self.stress_history_smoothed[-self.stress_history_limit :]

        x_raw = [point[0] for point in self.stress_history_raw]
        y_raw = [point[1] for point in self.stress_history_raw]
        x_smooth = [point[0] for point in self.stress_history_smoothed]
        y_smooth = [point[1] for point in self.stress_history_smoothed]

        self.stress_raw_line.set_data(x_raw, y_raw)
        self.stress_smooth_line.set_data(x_smooth, y_smooth)

        if x_smooth:
            x_min = max(0, x_smooth[-1] - self.stress_history_limit)
            x_max = x_smooth[-1] + 1
            self.stress_ax.set_xlim(x_min, x_max)

        self.stress_fig.canvas.draw_idle()
        self.stress_fig.canvas.flush_events()
        plt.pause(0.001)

    def show_webcam_frame(self, frame):
        """Overlay stress text and show webcam frame."""
        if SHOW_WEBCAM:
            annotated = frame.copy()
            frame_height, frame_width = annotated.shape[:2]
            if SHOW_FACE_BOUNDING_BOX:
                for box in self.latest_face_boxes:
                    x, y, w, h, score = box
                    x, y, w, h = self._normalize_box_for_frame(x, y, w, h, frame_width, frame_height)
                    cv2.rectangle(
                        annotated,
                        (x, y),
                        (x + w, y + h),
                        BOUNDING_BOX_COLOR_BGR,
                        BOUNDING_BOX_THICKNESS,
                    )
                    if SHOW_BOUNDING_BOX_CONFIDENCE and score is not None:
                        label = f"face {score:.2f}"
                        cv2.putText(
                            annotated,
                            label,
                            (x, max(20, y - 8)),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.55,
                            BOUNDING_BOX_COLOR_BGR,
                            2,
                            cv2.LINE_AA,
                        )

            if SHOW_FACE_LANDMARKS:
                for x, y in self.latest_landmark_points:
                    cv2.circle(
                        annotated,
                        (int(x), int(y)),
                        LANDMARK_RADIUS,
                        LANDMARK_COLOR_BGR,
                        LANDMARK_THICKNESS,
                        cv2.LINE_AA,
                    )

            if SHOW_STRESS_OVERLAY_TEXT:
                cv2.putText(
                    annotated,
                    self.latest_stress_text,
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 0),
                    2,
                    cv2.LINE_AA,
                )

            if SHOW_PERFORMANCE_OVERLAY:
                cv2.putText(
                    annotated,
                    f"Processing FPS: {self.current_fps:.1f}",
                    (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    (0, 255, 255),
                    2,
                    cv2.LINE_AA,
                )
                cv2.putText(
                    annotated,
                    f"Frame queue: {self.current_queue_depth}/{self.current_queue_capacity}",
                    (10, 85),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 200, 255),
                    2,
                    cv2.LINE_AA,
                )
            cv2.imshow(WEBCAM_WINDOW_TITLE, annotated)

        self._render_status_window()

    def _render_status_window(self):
        """Render a separate status window for update/missing state diagnostics."""
        if not SHOW_STATUS_WINDOW:
            return

        canvas_height = 340 if SHOW_PERFORMANCE_STATUS else 260
        canvas_width = 560
        canvas = np.zeros((canvas_height, canvas_width, 3), dtype=np.uint8)
        canvas[:] = (28, 28, 28)

        cv2.putText(
            canvas,
            "Pipeline Status",
            (12, 28),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )

        row_y = 56
        for key, (ok, message) in self.status_rows.items():
            indicator = "UPDATED" if ok else "MISSED"
            color = (0, 200, 0) if ok else (0, 0, 220)
            text = f"{key}: {indicator} - {message}"
            cv2.putText(
                canvas,
                text,
                (12, row_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                color,
                2,
                cv2.LINE_AA,
            )
            row_y += 32

        if SHOW_PERFORMANCE_STATUS:
            fps_ok = self.current_fps > 0.0
            queue_ok = self.current_queue_capacity > 0 and self.current_queue_depth < self.current_queue_capacity

            fps_color = (0, 200, 0) if fps_ok else (0, 0, 220)
            queue_color = (0, 200, 0) if queue_ok else (0, 0, 220)

            cv2.putText(
                canvas,
                f"Processing FPS: {self.current_fps:.1f}",
                (12, row_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                fps_color,
                2,
                cv2.LINE_AA,
            )
            row_y += 32
            cv2.putText(
                canvas,
                f"Frame queue depth: {self.current_queue_depth}/{self.current_queue_capacity}",
                (12, row_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                queue_color,
                2,
                cv2.LINE_AA,
            )

        cv2.imshow(STATUS_WINDOW_TITLE, canvas)

    def should_quit(self):
        """Return True when the user requests to quit the webcam display."""
        if not SHOW_WEBCAM and not SHOW_STATUS_WINDOW:
            return False
        return (cv2.waitKey(1) & 0xFF) == ord("q")

    def shutdown(self):
        """Close display resources."""
        cv2.destroyAllWindows()
        # Some matplotlib backends (TkAgg on Windows) can throw during late teardown.
        try:
            plt.close("all")
        except Exception:
            pass

    def _init_emotion_graph(self):
        self.emotion_fig, self.emotion_ax = plt.subplots(figsize=(10, 6))
        self.emotion_bars = self.emotion_ax.bar(self.emotion_order, [0.0] * len(self.emotion_order), color="blue")
        self.emotion_ax.set_xlabel("Emotion")
        self.emotion_ax.set_ylabel("Confidence")
        self.emotion_ax.set_title("Detected Emotions")
        self.emotion_ax.set_ylim(0, 1)
        plt.xticks(rotation=45)
        self.emotion_fig.tight_layout()
        plt.show(block=False)

    def _init_stress_graph(self):
        self.stress_fig, self.stress_ax = plt.subplots(figsize=(9, 4))
        self.stress_raw_line, = self.stress_ax.plot([], [], color="tab:orange", linewidth=1.5, label="Raw")
        self.stress_smooth_line, = self.stress_ax.plot([], [], color="tab:green", linewidth=2.0, label="Smoothed")
        self.stress_ax.set_title("Live Stress Trend")
        self.stress_ax.set_xlabel("Processed Frame")
        self.stress_ax.set_ylabel("Stress (0-100)")
        self.stress_ax.set_ylim(0, 100)
        self.stress_ax.grid(alpha=0.3)
        self.stress_ax.legend(loc="upper left")
        self.stress_fig.tight_layout()
        plt.show(block=False)


live_display = LiveDisplayManager()
