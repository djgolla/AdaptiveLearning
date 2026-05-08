"""Frontend API for stress detection pipeline.

This module provides an interface for the stress detection system.

"""

import queue
import frame_extractor as extractor


class StressDetectionPipeline:
    """High-level stress detection pipeline manager."""

    def __init__(self):
        self.frame_extractor = extractor.get_extractor()
        self.current_status = {
            "elapsed_time": 0.0,
            "smoothed_fps": 0.0,
            "queue_depth": 0,
            "queue_capacity": 0,
            "emotions": {},
            "stress_raw": 0.0,
            "stress_smoothed": 0.0,
            "frame_count": 0,
        }

    def start(self):
        """
        Initialize and start the stress detection pipeline.

        Raises:
            RuntimeError: If camera cannot be opened or initialization fails.
        """
        extractor.initialize()

    def process_next_step(self):
        """
        Process the next frame from the camera.

        This handles all frame capturing, processing, stress calculation, and display
        internally. Main just needs to call this in a loop.

        Returns:
            Dictionary containing all current metrics:
                - elapsed_time: Time elapsed since capture started
                - smoothed_fps: Current smoothed FPS
                - queue_depth: Current number of frames in queue
                - queue_capacity: Maximum queue capacity
                - emotions: Dictionary of emotion labels to confidence values
                - stress_raw: Raw stress value
                - stress_smoothed: Smoothed stress value
                - frame_count: Total frames processed

        Raises:
            queue.Empty: If timeout waiting for frame (consider it a minor issue, not fatal)
        """
        try:
            # Get the next frame from the camera
            frame = self.frame_extractor.get_next_frame(timeout=1.0)

            # Process the frame to get timing and metrics
            (
                elapsed_time,
                should_save,
                smoothed_fps,
                queue_depth,
                queue_capacity,
            ) = self.frame_extractor.process_frame(frame)

            # Handle frame display and stress calculation
            self.frame_extractor.handle_frame_display(frame)

            if should_save:
                from frame_handler import recieve_frame

                recieve_frame(frame, elapsed_time)

            # Get current stress and emotion data from the display manager
            from display_manager import live_display

            self.current_status.update(
                {
                    "elapsed_time": elapsed_time,
                    "smoothed_fps": smoothed_fps,
                    "queue_depth": queue_depth,
                    "queue_capacity": queue_capacity,
                    "emotions": (
                        live_display.latest_emotion_dict
                        if hasattr(live_display, "latest_emotion_dict")
                        else {}
                    ),
                    "stress_raw": (
                        live_display.latest_stress_raw
                        if hasattr(live_display, "latest_stress_raw")
                        else 0.0
                    ),
                    "stress_smoothed": (
                        live_display.latest_stress_smoothed
                        if hasattr(live_display, "latest_stress_smoothed")
                        else 0.0
                    ),
                }
            )

            self.current_status["frame_count"] += 1

        except queue.Empty:
            # Timeout waiting for frame - log but don't fail
            pass

        return self.current_status

    def should_quit(self):
        """
        Check if the user has requested to quit the pipeline.

        Returns:
            True if quit was requested, False otherwise.
        """
        return self.frame_extractor.check_quit_request()

    def stop(self):
        """
        Shutdown the stress detection pipeline and release resources.

        Closes all windows, stops threads, and releases the camera.
        """
        extractor.shutdown()

    def get_status(self):
        """
        Get the current pipeline status and metrics.

        Returns:
            Dictionary containing all current metrics.
        """
        return self.current_status.copy()


# Global pipeline instance
_pipeline = None


def get_pipeline():
    """Get or create the global pipeline instance."""
    global _pipeline
    if _pipeline is None:
        _pipeline = StressDetectionPipeline()
    return _pipeline


def start_stress_detection():
    """
    Initialize and start the stress detection pipeline.

    Raises:
        RuntimeError: If camera cannot be opened or initialization fails.
    """
    pipeline = get_pipeline()
    pipeline.start()


def process_next_step():
    """
    Process the next frame in the stress detection pipeline.

    This function handles everything: frame capture, processing, stress calculation,
    emotion detection, and display. Main just calls this in a loop.

    Returns:
        Dictionary with current metrics including emotions and stress values.
    """
    pipeline = get_pipeline()
    return pipeline.process_next_step()


def should_quit():
    """
    Check if the user has requested to quit the pipeline.

    Returns:
        True if quit was requested, False otherwise.
    """
    pipeline = get_pipeline()
    return pipeline.should_quit()


def stop_stress_detection():
    """
    Shutdown the stress detection pipeline and release resources.

    Closes all windows, stops threads, and releases the camera.
    """
    global _pipeline
    if _pipeline is not None:
        _pipeline.stop()
        _pipeline = None


def get_current_status():
    """
    Get the current pipeline status and all metrics.

    Returns:
        Dictionary containing:
            - elapsed_time: Time elapsed since capture started
            - smoothed_fps: Current smoothed FPS
            - queue_depth: Current number of frames in queue
            - queue_capacity: Maximum queue capacity
            - emotions: Dictionary of emotion labels to values
            - stress_raw: Raw stress value
            - stress_smoothed: Smoothed stress value
            - frame_count: Total frames processed
    """
    pipeline = get_pipeline()
    return pipeline.get_status()
