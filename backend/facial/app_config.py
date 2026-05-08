"""Centralized runtime configuration for the live stress pipeline."""

# Capture settings
CAMERA_INDEX = 0
FRAME_INTERVAL_SECONDS = 1.00

# Output/session settings
FRAMES_DIR = "./frames"
SAVE_STRESS_CSV = False
STRESS_CSV_FILENAME = "stress_history.csv"
SAVE_CAPTURE_IMAGES = False
ENABLE_ASYNC_IMAGE_SAVE = True

# Stress model settings)
# Defaults: 12, 0.35, 0.45, 0.35, 0.20
STRESS_WINDOW_SIZE = 12  # Number of recent frames to consider for stress calculation, should be large enough to capture trends but small enough for responsiveness. At 0.2s/frame, 12 frames = 2.4 seconds of history.
STRESS_EMA_ALPHA = 0.35  # smoothing factor for exponential moving average of stress scores, between 0 and 1. Higher values give more weight to recent scores.
STRESS_GEOMETRY_WEIGHT = 0.45  # Geometric features (very basic in current model)
STRESS_EMOTION_WEIGHT = 0.35  # Emotional probabilities from py-feat emotions model
STRESS_AU_WEIGHT = 0.20  # Action units from facial expressions

# Action Unit (AU) configuration
# AU_PRESET: "ranked" (14 stress-relevant AUs ordered by relevance)
#            "all" (use all available AUs from py-feat (Do not use all AUs for stress calculation, just for debugging))
#            "custom" (use AU_CUSTOM_LIST below)
AU_PRESET = "ranked"

# AU_CUSTOM_LIST: Only used if AU_PRESET="custom". List of AU names to include.
# Example: ["AU01", "AU02", "AU04", "AU05", "AU15", "AU09"]
# If empty and AU_PRESET="custom", falls back to "all".
AU_CUSTOM_LIST = []

# AU_CUSTOM_WEIGHTS: Optional override weights for AUs (only used if AU_PRESET="custom").
# Maps AU name -> weight. If not provided, weights are auto-calculated from order.
# Example: {"AU01": 0.25, "AU02": 0.20, ...}
AU_CUSTOM_WEIGHTS = {}

# Display toggles
SHOW_WEBCAM = True
SHOW_STRESS_OVERLAY_TEXT = True
SHOW_FACE_BOUNDING_BOX = True
SHOW_FACE_LANDMARKS = True
SHOW_EMOTION_GRAPH = True
SHOW_STRESS_GRAPH = True
SHOW_STATUS_WINDOW = True
SHOW_PERFORMANCE_OVERLAY = True
SHOW_PERFORMANCE_STATUS = True

# Display styling
WEBCAM_WINDOW_TITLE = "Camera Feed"
STATUS_WINDOW_TITLE = "Pipeline Status"
STRESS_HISTORY_LIMIT = 120
BOUNDING_BOX_COLOR_BGR = (0, 255, 255)
BOUNDING_BOX_THICKNESS = 2
SHOW_BOUNDING_BOX_CONFIDENCE = True
LANDMARK_COLOR_BGR = (0, 165, 255)
LANDMARK_RADIUS = 1
LANDMARK_THICKNESS = -1
