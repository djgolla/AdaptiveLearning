import os
import csv
import cv2
import numpy as np
import queue
import threading
from datetime import datetime
from facial_recog_pyfeat import df_from_frame, get_emotion_label
from stress_calculator import StressCalculator
from display_manager import live_display
from app_config import (
    FRAMES_DIR,
    SAVE_STRESS_CSV,
    STRESS_CSV_FILENAME,
    STRESS_WINDOW_SIZE,
    STRESS_EMA_ALPHA,
    STRESS_GEOMETRY_WEIGHT,
    STRESS_EMOTION_WEIGHT,
    STRESS_AU_WEIGHT,
    SHOW_EMOTION_GRAPH,
    SHOW_STRESS_GRAPH,
    SAVE_CAPTURE_IMAGES,
    ENABLE_ASYNC_IMAGE_SAVE,
)

# folder to store frames
frames_dir = FRAMES_DIR

# Rolling multi-frame stress estimator.
stress_calculator = StressCalculator(
    window_size=STRESS_WINDOW_SIZE,
    ema_alpha=STRESS_EMA_ALPHA,
    geometry_weight=STRESS_GEOMETRY_WEIGHT,
    emotion_weight=STRESS_EMOTION_WEIGHT,
    au_weight=STRESS_AU_WEIGHT,
)
stress_csv_path = None
folder_path = None

_csv_write_queue = None
_image_save_queue = None
_csv_worker_thread = None
_image_worker_thread = None
_csv_worker_stop = None
_image_worker_stop = None


def _extract_bounding_boxes(detected_faces):
    """Parse py-feat face detections into (x, y, w, h, score|None) tuples."""
    if detected_faces is None:
        return []

    boxes = []

    # DataFrame/Fex-style output with named columns.
    if hasattr(detected_faces, "columns"):
        columns = set(str(col) for col in detected_faces.columns)
        required = {"FaceRectX", "FaceRectY", "FaceRectWidth", "FaceRectHeight"}
        if required.issubset(columns):
            for _, row in detected_faces.iterrows():
                score = float(row["FaceScore"]) if "FaceScore" in columns else None
                boxes.append(
                    (
                        float(row["FaceRectX"]),
                        float(row["FaceRectY"]),
                        float(row["FaceRectWidth"]),
                        float(row["FaceRectHeight"]),
                        score,
                    )
                )
            return boxes

    # Numeric array-style output, expecting rows like [x, y, w, h, (optional score), ...].
    arr = np.asarray(detected_faces)
    if arr.size == 0:
        return []

    if arr.ndim == 1 and arr.shape[0] >= 4:
        score = float(arr[4]) if arr.shape[0] > 4 else None
        return [(float(arr[0]), float(arr[1]), float(arr[2]), float(arr[3]), score)]

    if arr.ndim >= 2 and arr.shape[-1] >= 4:
        rows = arr.reshape(-1, arr.shape[-1])
        for row in rows:
            score = float(row[4]) if row.shape[0] > 4 else None
            boxes.append(
                (float(row[0]), float(row[1]), float(row[2]), float(row[3]), score)
            )

    return boxes


def _extract_landmark_points(detected_landmarks):
    """Parse py-feat landmarks into a flat list of (x, y) points for drawing."""
    if detected_landmarks is None:
        return []

    arr = np.asarray(detected_landmarks)
    if arr.size == 0:
        return []

    # Common case: (..., 68, 2)
    if arr.shape[-2:] == (68, 2):
        faces = arr.reshape(-1, 68, 2)
        points = []
        for face_points in faces:
            for point in face_points:
                points.append((float(point[0]), float(point[1])))
        return points

    # Fallback for flattened arrays with pairs.
    if arr.ndim == 2 and arr.shape[1] == 2:
        return [(float(point[0]), float(point[1])) for point in arr]

    return []


def create_timestamped_folder(base_dir):
    """
    Creates a timestamped folder within the specified base directory.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H;%M;%S")
    folder_path = os.path.join(base_dir, f"frame_{timestamp}")
    os.makedirs(folder_path, exist_ok=True)
    return folder_path


def save_frame(frame, folder_path, timestamp):
    """
    Saves the given frame to the specified folder with a timestamped filename.
    """
    filename = f"frame_{timestamp:.2f}.jpg"
    file_path = os.path.join(folder_path, filename)
    cv2.imwrite(file_path, frame)
    return file_path


def _csv_writer_loop(stop_event, csv_path, csv_queue):
    """Background CSV writer to avoid blocking the processing loop on disk I/O."""
    while not stop_event.is_set() or not csv_queue.empty():
        try:
            payload = csv_queue.get(timeout=0.1)
        except queue.Empty:
            continue

        if payload is None:
            break

        timestamp, stress_result = payload
        with open(csv_path, "a", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(
                [
                    datetime.now().isoformat(),
                    f"{timestamp:.3f}",
                    f"{stress_result.raw_stress_0_100:.4f}",
                    f"{stress_result.smoothed_stress_0_100:.4f}",
                    f"{stress_result.geometric_stress_0_1:.6f}",
                    (
                        ""
                        if stress_result.au_stress_0_1 is None
                        else f"{stress_result.au_stress_0_1:.6f}"
                    ),
                    (
                        ""
                        if stress_result.emotion_stress_0_1 is None
                        else f"{stress_result.emotion_stress_0_1:.6f}"
                    ),
                    f"{stress_result.eye_openness:.6f}",
                    f"{stress_result.eyebrow_distance:.6f}",
                    f"{stress_result.mouth_tension:.6f}",
                    stress_result.frames_in_window,
                ]
            )


def _image_writer_loop(stop_event, image_queue):
    """Background image writer so optional frame snapshots do not stall processing."""
    while not stop_event.is_set() or not image_queue.empty():
        try:
            payload = image_queue.get(timeout=0.1)
        except queue.Empty:
            continue

        if payload is None:
            break

        frame, current_folder_path, timestamp = payload
        save_frame(frame, current_folder_path, timestamp)


def _start_background_workers():
    """Start optional background workers for CSV and image write paths."""
    global _csv_write_queue
    global _image_save_queue
    global _csv_worker_thread
    global _image_worker_thread
    global _csv_worker_stop
    global _image_worker_stop

    # Reset worker state on every session init.
    _csv_write_queue = None
    _image_save_queue = None
    _csv_worker_thread = None
    _image_worker_thread = None
    _csv_worker_stop = None
    _image_worker_stop = None

    if SAVE_STRESS_CSV and stress_csv_path is not None:
        _csv_write_queue = queue.Queue(maxsize=256)
        _csv_worker_stop = threading.Event()
        _csv_worker_thread = threading.Thread(
            target=_csv_writer_loop,
            args=(_csv_worker_stop, stress_csv_path, _csv_write_queue),
            daemon=True,
            name="stress-csv-writer",
        )
        _csv_worker_thread.start()

    if SAVE_CAPTURE_IMAGES and ENABLE_ASYNC_IMAGE_SAVE:
        _image_save_queue = queue.Queue(maxsize=32)
        _image_worker_stop = threading.Event()
        _image_worker_thread = threading.Thread(
            target=_image_writer_loop,
            args=(_image_worker_stop, _image_save_queue),
            daemon=True,
            name="frame-image-writer",
        )
        _image_worker_thread.start()


def shutdown_background_workers():
    """Flush and stop all frame handler worker threads."""
    global _csv_worker_thread
    global _image_worker_thread

    if _csv_worker_stop is not None:
        _csv_worker_stop.set()
    if _image_worker_stop is not None:
        _image_worker_stop.set()

    if _csv_write_queue is not None:
        try:
            _csv_write_queue.put_nowait(None)
        except queue.Full:
            pass

    if _image_save_queue is not None:
        try:
            _image_save_queue.put_nowait(None)
        except queue.Full:
            pass

    if _csv_worker_thread is not None:
        _csv_worker_thread.join(timeout=1.5)
    if _image_worker_thread is not None:
        _image_worker_thread.join(timeout=1.5)


def recieve_frame(frame, timestamp):
    """
    Handles the received frame,
    """
    global folder_path
    if folder_path is None:
        print("Error: Folder path not initialized.")
        return
    if SAVE_CAPTURE_IMAGES:
        if ENABLE_ASYNC_IMAGE_SAVE and _image_save_queue is not None:
            try:
                # Copy to avoid accidental mutation before async write.
                _image_save_queue.put_nowait((frame.copy(), folder_path, timestamp))
            except queue.Full:
                pass
        else:
            save_frame(frame, folder_path, timestamp)

    # Face detection
    result = df_from_frame(frame)

    # result tuple format from facial_recog.py:
    # (emotion_result, detected_faces, detected_landmarks, au_result)
    emotion_result, detected_faces, detected_landmarks, au_result = result
    face_boxes = _extract_bounding_boxes(detected_faces)
    landmark_points = _extract_landmark_points(detected_landmarks)
    live_display.set_face_boxes(face_boxes)
    live_display.set_landmark_points(landmark_points)

    if face_boxes:
        live_display.set_status("Face detection", True, f"{len(face_boxes)} face(s)")
        live_display.set_status("Bounding boxes", True, "updated")
        live_display.set_status(
            "Landmark points",
            bool(landmark_points),
            "updated" if landmark_points else "not available",
        )
    else:
        live_display.set_status("Face detection", False, "no face detected")
        live_display.set_status("Bounding boxes", False, "not available")
        live_display.set_status("Landmark points", False, "not available")

    # Only compute stress when at least one face was detected.
    if detected_landmarks is not None and len(detected_landmarks) > 0:
        try:
            stress_result = stress_calculator.process_frame(
                detected_landmarks=detected_landmarks,
                emotion_output=emotion_result,
                au_output=au_result,
                face_index=0,
            )
            live_display.set_stress_text(
                f"Stress {stress_result.smoothed_stress_0_100:.1f}/100 "
                f"(raw {stress_result.raw_stress_0_100:.1f})"
            )

            live_display.update_stress(
                stress_result.raw_stress_0_100,
                stress_result.smoothed_stress_0_100,
            )
            live_display.set_status("Stress value", True, "updated")
            live_display.set_status(
                "Stress graph",
                SHOW_STRESS_GRAPH,
                "updated" if SHOW_STRESS_GRAPH else "disabled",
            )
            _append_stress_row(timestamp, stress_result)
        except ValueError as exc:
            live_display.set_stress_text("Stress: invalid landmarks")
            live_display.set_status("Stress value", False, "invalid landmarks")
            live_display.set_status(
                "Stress graph",
                False,
                "not updated",
            )
    else:
        live_display.set_stress_text("Stress: no face")
        live_display.set_status("Stress value", False, "not available")
        live_display.set_status("Stress graph", False, "not updated")

    emotions = get_emotion_label(emotion_result)
    live_display.update_emotions(emotions)
    if emotions:
        live_display.set_status("Emotion values", True, "updated")
        live_display.set_status(
            "Emotion graph",
            SHOW_EMOTION_GRAPH,
            "updated" if SHOW_EMOTION_GRAPH else "disabled",
        )
    else:
        live_display.set_status("Emotion values", False, "not available")
        live_display.set_status("Emotion graph", False, "not updated")


def _append_stress_row(timestamp, stress_result):
    """Append a per-frame stress snapshot to the current session CSV."""
    if stress_csv_path is None or not SAVE_STRESS_CSV:
        return

    if _csv_write_queue is not None:
        try:
            _csv_write_queue.put_nowait((timestamp, stress_result))
            return
        except queue.Full:
            pass

    # Fallback keeps data safe if queue is unavailable/full.
    with open(stress_csv_path, "a", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(
            [
                datetime.now().isoformat(),
                f"{timestamp:.3f}",
                f"{stress_result.raw_stress_0_100:.4f}",
                f"{stress_result.smoothed_stress_0_100:.4f}",
                f"{stress_result.geometric_stress_0_1:.6f}",
                (
                    ""
                    if stress_result.au_stress_0_1 is None
                    else f"{stress_result.au_stress_0_1:.6f}"
                ),
                (
                    ""
                    if stress_result.emotion_stress_0_1 is None
                    else f"{stress_result.emotion_stress_0_1:.6f}"
                ),
                f"{stress_result.eye_openness:.6f}",
                f"{stress_result.eyebrow_distance:.6f}",
                f"{stress_result.mouth_tension:.6f}",
                stress_result.frames_in_window,
            ]
        )


def initiate_folder_structure():
    """
    Initializes the folder structure for storing frames.
    """
    os.makedirs(frames_dir, exist_ok=True)
    global folder_path
    global stress_csv_path

    stress_calculator.reset()
    live_display.initialize()
    live_display.reset_stress_history()

    folder_path = create_timestamped_folder(frames_dir)

    if SAVE_STRESS_CSV:
        stress_csv_path = os.path.join(folder_path, STRESS_CSV_FILENAME)
        with open(stress_csv_path, "w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(
                [
                    "iso_time",
                    "capture_elapsed_seconds",
                    "raw_stress_0_100",
                    "smoothed_stress_0_100",
                    "geometric_stress_0_1",
                    "au_stress_0_1",
                    "emotion_stress_0_1",
                    "eye_openness",
                    "eyebrow_distance",
                    "mouth_tension",
                    "frames_in_window",
                ]
            )
    else:
        stress_csv_path = None

    _start_background_workers()

    return folder_path


def show_live_frame(frame):
    """Render webcam frame through the centralized display manager."""
    live_display.show_webcam_frame(frame)


def update_runtime_metrics(fps, frame_queue_depth, frame_queue_capacity):
    """Push live runtime metrics into the display manager."""
    live_display.set_runtime_metrics(fps, frame_queue_depth, frame_queue_capacity)


def should_quit_live_display():
    """Check whether the user requested to quit the live display."""
    return live_display.should_quit()


def shutdown_live_display():
    """Close live display windows and figures."""
    live_display.shutdown()
