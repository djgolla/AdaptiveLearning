# Requires opencv-python
"""Core frame extraction and processing module.

This module handles camera capture, frame processing, and stress detection.
It provides functions for the stress detection pipeline.
"""

import cv2
import time
import queue
import threading
from app_config import CAMERA_INDEX, FRAME_INTERVAL_SECONDS
from frame_handler import (
    recieve_frame,
    initiate_folder_structure,
    show_live_frame,
    should_quit_live_display,
    shutdown_live_display,
    shutdown_background_workers,
    update_runtime_metrics,
)


class FrameCaptureThread(threading.Thread):
    """Capture frames continuously so camera I/O does not block processing."""

    def __init__(self, camera, frame_queue, stop_event):
        super().__init__(daemon=True, name="frame-capture")
        self.camera = camera
        self.frame_queue = frame_queue
        self.stop_event = stop_event

    def run(self):
        while not self.stop_event.is_set():
            ret, frame = self.camera.read()
            if not ret:
                continue

            # Keep newest frames for low latency if consumer falls behind.
            if self.frame_queue.full():
                try:
                    self.frame_queue.get_nowait()
                except queue.Empty:
                    pass

            try:
                self.frame_queue.put_nowait(frame)
            except queue.Full:
                pass


class FrameExtractor:
    """Manages frame extraction and stress detection pipeline."""

    def __init__(self):
        self.camera = None
        self.frame_queue = None
        self.capture_thread = None
        self.capture_stop = None
        self.is_running = False
        self.start_time = None
        self.initial_time = None
        self.last_processed_time = None
        self.processing_fps = 0.0
        self.processing_fps_alpha = 0.35

    def initialize_camera(self):
        """Open the default camera and initialize capture infrastructure."""
        self.camera = cv2.VideoCapture(CAMERA_INDEX)

        if not self.camera.isOpened():
            raise RuntimeError("Error: Could not open camera")

        initiate_folder_structure()

    def start_capture_thread(self):
        """Start the frame capture background thread."""
        self.frame_queue = queue.Queue(maxsize=4)
        self.capture_stop = threading.Event()
        self.capture_thread = FrameCaptureThread(
            self.camera, self.frame_queue, self.capture_stop
        )
        self.capture_thread.start()

        self.start_time = time.time()
        self.initial_time = self.start_time
        self.last_processed_time = self.start_time
        self.processing_fps = 0.0
        self.is_running = True

    def get_next_frame(self, timeout=1.0):
        """
        Retrieve the next frame from the queue.

        Args:
            timeout: Timeout in seconds to wait for a frame.

        Returns:
            Frame array or None if timeout occurs.

        Raises:
            queue.Empty: If no frame is available within timeout.
        """
        if not self.is_running or self.frame_queue is None:
            raise RuntimeError("Frame extractor not running")

        return self.frame_queue.get(timeout=timeout)

    def process_frame(self, frame):
        """
        Process a captured frame and update metrics.

        Args:
            frame: The frame to process.

        Returns:
            Tuple of (elapsed_time, should_save, smoothed_fps, queue_depth, queue_capacity)
        """
        frame_interval = FRAME_INTERVAL_SECONDS
        current_time = time.time()
        elapsed_time = current_time - self.start_time
        should_save = elapsed_time > frame_interval

        if should_save:
            process_delta = max(current_time - self.last_processed_time, 1e-6)
            instantaneous_processing_fps = 1.0 / process_delta
            if self.processing_fps <= 0.0:
                self.processing_fps = instantaneous_processing_fps
            else:
                self.processing_fps = (
                    (1.0 - self.processing_fps_alpha) * self.processing_fps
                    + self.processing_fps_alpha * instantaneous_processing_fps
                )

            self.last_processed_time = current_time
            self.start_time = current_time

        display_fps = self.processing_fps
        if display_fps <= 0.0 and frame_interval > 0:
            display_fps = 1.0 / frame_interval

        update_runtime_metrics(
            display_fps,
            self.frame_queue.qsize(),
            self.frame_queue.maxsize,
        )

        return (
            current_time - self.initial_time,
            should_save,
            display_fps,
            self.frame_queue.qsize(),
            self.frame_queue.maxsize,
        )

    def handle_frame_display(self, frame):
        """Display the frame through the centralized display manager."""
        show_live_frame(frame)

    def check_quit_request(self):
        """Check if user requested to quit."""
        return should_quit_live_display()

    def shutdown(self):
        """Shutdown the frame extractor and release resources."""
        if self.capture_stop is not None:
            self.capture_stop.set()

        if self.capture_thread is not None:
            self.capture_thread.join(timeout=1.5)

        if self.camera is not None:
            self.camera.release()

        shutdown_background_workers()
        shutdown_live_display()
        self.is_running = False


# Global instance for singleton-like access
_extractor = None


def get_extractor():
    """Get or create the global FrameExtractor instance."""
    global _extractor
    if _extractor is None:
        _extractor = FrameExtractor()
    return _extractor


def initialize():
    """Initialize the frame extractor."""
    extractor = get_extractor()
    extractor.initialize_camera()
    extractor.start_capture_thread()


def process_and_display_frame(frame):
    """
    Process a frame for stress detection and display.

    Args:
        frame: The captured frame.

    Returns:
        Tuple of (elapsed_time, smoothed_fps) for the frame.
    """
    extractor = get_extractor()
    elapsed_time, should_save, fps, _, _ = extractor.process_frame(frame)

    if should_save:
        recieve_frame(frame, elapsed_time)

    extractor.handle_frame_display(frame)

    return (elapsed_time, fps)


def shutdown():
    """Shutdown the frame extractor."""
    global _extractor
    if _extractor is not None:
        _extractor.shutdown()
        _extractor = None
