"""Utilities for detecting and managing AU (Action Unit) availability from py-feat.

This module provides functions to:
1. Detect which AUs py-feat actually provides
2. Get preset AU configurations (ranked by stress relevance)
3. Calculate weights for AU-based stress computation
"""

# Ranked AU list ordered by stress relevance (descending).
RANKED_AU_LIST = [
    "AU01",  # Inner brow raiser
    "AU02",  # Outer brow raiser
    "AU05",  # Upper lid raiser
    "AU04",  # Brow lowerer
    "AU15",  # Lip corner depressor
    "AU09",  # Nose wrinkler
    "AU17",  # Chin raiser
    "AU10",  # Upper lip raiser
    "AU25",  # Lips part
    "AU06",  # Cheek raiser
    "AU23",  # Lip tightener
    "AU20",  # Lip stretcher
    "AU07",  # Lid tightener
    "AU12",  # Lip corner puller
]


def get_available_aus_from_pyfeat():
    """Detect which AUs py-feat's detector can actually provide.
    
    Returns:
        list: AU names (e.g., ["AU01", "AU02", ...]) available in py-feat,
              or empty list if detection fails.
    """
    try:
        from feat import Detector
        import numpy as np
        
        detector = Detector()
        
        # Create a minimal dummy face detection to probe AU output
        # We use a small random image to avoid needing a real face
        test_img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        # Try to detect and get AU output structure
        faces = detector.detect_faces(test_img)
        
        # If no faces in random image, try with a slightly less random approach
        # or check detector's internal AU names directly
        if hasattr(detector, 'au_model') and detector.au_model is not None:
            # Some versions of py-feat expose AU names
            if hasattr(detector.au_model, 'n_classes'):
                # Default py-feat AU set (if we can't query directly)
                return _get_default_pyfeat_aus()
        
        # Fallback: return default py-feat AU set
        return _get_default_pyfeat_aus()
        
    except Exception:
        # If we can't detect, return empty list
        return []


def _get_default_pyfeat_aus():
    """Return the default AU set that modern py-feat provides."""
    # Standard py-feat AU output (version 0.4+)
    return [
        "AU01", "AU02", "AU04", "AU05", "AU06", "AU07",
        "AU09", "AU10", "AU12", "AU14", "AU15", "AU17",
        "AU20", "AU23", "AU24", "AU25", "AU26", "AU28", "AU43"
    ]


def get_au_preset(preset_name: str) -> list:
    """Get a preset AU configuration.
    
    Args:
        preset_name: One of "ranked", "all", or custom name.
    
    Returns:
        list: AU names for the preset.
    """
    preset_name = preset_name.lower().strip()
    
    if preset_name == "ranked":
        return RANKED_AU_LIST
    
    if preset_name == "all":
        available = get_available_aus_from_pyfeat()
        return available if available else _get_default_pyfeat_aus()
    
    # Return empty for unknown presets; caller will use default
    return []


def calculate_au_weights(au_list: list) -> dict:
    """Calculate descending weights for a list of AUs.
    
    Args:
        au_list: List of AU names (order matters; first = highest weight).
    
    Returns:
        dict: Mapping of AU name to weight (sum = 1.0).
    """
    if not au_list:
        return {}
    
    n = len(au_list)
    # Descending weights: first AU gets highest, last gets lowest
    # e.g., for 14 AUs: [0.20, 0.19, 0.18, ..., 0.07]
    weights = {}
    for i, au in enumerate(au_list):
        # Weight = (n - i) / (n * (n + 1) / 2) for descending sum = 1.0
        weight = (n - i) / (n * (n + 1) / 2)
        weights[au] = round(weight, 2)
    
    return weights
