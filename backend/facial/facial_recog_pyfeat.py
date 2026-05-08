import cv2
import numpy as np
from feat import Detector
from feat.utils import FEAT_EMOTION_MAPPER

detector = Detector()


def _has_faces(detected_faces):
    """Return True when py-feat face detections contain at least one face."""
    if detected_faces is None:
        return False
    try:
        return len(detected_faces) > 0
    except TypeError:
        arr = np.asarray(detected_faces)
        return arr.size > 0


def get_emotion_label(emotion_result):
    """
    Maps the emotion values in emotion_result to their corresponding emotion labels.
    """
    if emotion_result is None:
        return None

    arr = np.asarray(emotion_result)
    if arr.size == 0:
        return None

    # Handle common py-feat layouts robustly, including singleton/batch dims.
    if arr.ndim >= 3:
        flat = arr.reshape(-1, arr.shape[-1])
        if flat.shape[0] == 0:
            return None
        emotion_values = flat[0].tolist()
    elif arr.ndim == 2:
        if arr.shape[0] == 0:
            return None
        emotion_values = arr[0].tolist()
    elif arr.ndim == 1:
        emotion_values = arr.tolist()
    else:
        return None

    if len(emotion_values) == 0:
        return None

    emotion_labels = [FEAT_EMOTION_MAPPER[i] for i in range(len(emotion_values))]
    return dict(zip(emotion_labels, emotion_values))


def convert_to_rgb_from_frame(frame):
    """
    Converts the given frame from BGR to RGB color space.
    """
    return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)


def convert_to_rgb_from_file(file_path):
    """
    Reads the image from the given file path and converts it from BGR to RGB color space.
    """
    img = cv2.imread(file_path)
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def df_from_frame(frame):
    """
    Detects faces in the given frame using py-feat.
    Returns the detection results.
    """

    # From frame directly
    img_rgb = convert_to_rgb_from_frame(frame)
    detected_faces = detector.detect_faces(img_rgb)
    if not _has_faces(detected_faces):
        return (None, detected_faces, None, None)

    detected_landmarks = detector.detect_landmarks(img_rgb, detected_faces)
    if detected_landmarks is None or len(detected_landmarks) == 0:
        return (None, detected_faces, None, None)

    emotion_result = detector.detect_emotions(
        img_rgb, detected_faces, detected_landmarks
    )
    try:
        au_result = detector.detect_aus(img_rgb, detected_faces, detected_landmarks)
    except Exception:
        # Keep pipeline running even if AU model is unavailable.
        au_result = None

    if emotion_result is None:
        return (None, detected_faces, detected_landmarks, au_result)

    return (emotion_result, detected_faces, detected_landmarks, au_result)


def df_from_file(file_path):
    """
    Detects faces in the image at the given file path using py-feat.
    Returns the detection results.
    """
    img_rgb = convert_to_rgb_from_file(file_path)
    detected_faces = detector.detect_faces(img_rgb)
    if not _has_faces(detected_faces):
        return (None, detected_faces, None, None)

    detected_landmarks = detector.detect_landmarks(img_rgb, detected_faces)
    if detected_landmarks is None or len(detected_landmarks) == 0:
        return (None, detected_faces, None, None)

    emotion_result = detector.detect_emotions(
        img_rgb, detected_faces, detected_landmarks
    )
    try:
        au_result = detector.detect_aus(img_rgb, detected_faces, detected_landmarks)
    except Exception:
        au_result = None

    if emotion_result is None:
        return (None, detected_faces, detected_landmarks, au_result)

    return (emotion_result, detected_faces, detected_landmarks, au_result)
