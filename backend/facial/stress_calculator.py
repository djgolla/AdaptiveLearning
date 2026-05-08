"""Utilities for estimating stress from py-feat outputs across multiple frames.

This calculator combines:
1) 68-point landmark geometry (eye openness, eyebrow distance, mouth tension)
2) py-feat AU outputs
3) py-feat emotion probabilities

It then aggregates frame-level stress over a rolling window and an EMA smoother
to reduce noise from single-frame outliers.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional

import numpy as np

import au_utils


# Default AU order for backward compatibility and initial extraction.
# Actual AUs used come from app_config settings and au_utils presets.
DEFAULT_AU_ORDER = au_utils._get_default_pyfeat_aus()


@dataclass
class FrameStressResult:
	"""Container for a single processed frame stress result."""

	raw_stress_0_100: float
	smoothed_stress_0_100: float
	geometric_stress_0_1: float
	au_stress_0_1: Optional[float]
	emotion_stress_0_1: Optional[float]
	eye_openness: float
	eyebrow_distance: float
	mouth_tension: float
	frames_in_window: int


def _clip01(value: float) -> float:
	return float(np.clip(value, 0.0, 1.0))


def _safe_distance(a: np.ndarray, b: np.ndarray) -> float:
	return float(np.linalg.norm(a - b))


def _face_scale(landmarks: np.ndarray) -> float:
	"""Estimate a robust face scale for normalization.

	Uses average of jaw width and face height to normalize geometric measures.
	"""
	jaw_width = _safe_distance(landmarks[0], landmarks[16])
	face_height = _safe_distance(landmarks[8], landmarks[27])
	return max((jaw_width + face_height) / 2.0, 1e-6)


def _eye_ear(eye_points: np.ndarray) -> float:
	"""Compute Eye Aspect Ratio (EAR) for one eye.

	EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)
	"""
	vertical_1 = _safe_distance(eye_points[1], eye_points[5])
	vertical_2 = _safe_distance(eye_points[2], eye_points[4])
	horizontal = max(_safe_distance(eye_points[0], eye_points[3]), 1e-6)
	return (vertical_1 + vertical_2) / (2.0 * horizontal)


def _normalize_metric(value: float, low: float, high: float, invert: bool = False) -> float:
	"""Map a metric to [0, 1] using low/high anchors."""
	normalized = (value - low) / max(high - low, 1e-6)
	normalized = _clip01(normalized)
	if invert:
		normalized = 1.0 - normalized
	return normalized


def extract_landmarks_array(
	detected_landmarks: Any,
	face_index: int = 0,
) -> np.ndarray:
	"""Extract a single (68, 2) landmark array from py-feat landmark outputs.

	Supported inputs include numpy arrays/lists in shapes such as:
	- (68, 2)
	- (N, 68, 2)

	Raises ValueError if input cannot be parsed.
	"""
	if detected_landmarks is None:
		raise ValueError("Landmarks are None.")

	arr = np.asarray(detected_landmarks)
	if arr.size == 0:
		raise ValueError("Landmarks are empty.")

	# py-feat may return extra batch/face singleton dimensions, e.g. (1, 1, 68, 2).
	# If trailing dimensions are (68, 2), flatten all leading dimensions into face axis.
	if arr.shape[-2:] == (68, 2):
		faces = arr.reshape(-1, 68, 2)
		if face_index >= faces.shape[0]:
			raise ValueError(f"face_index {face_index} out of range for {faces.shape[0]} faces")
		return faces[face_index].astype(float)

	if arr.ndim == 2 and arr.shape == (68, 2):
		return arr.astype(float)

	if arr.ndim == 3 and arr.shape[1:] == (68, 2):
		if face_index >= arr.shape[0]:
			raise ValueError(f"face_index {face_index} out of range for {arr.shape[0]} faces")
		return arr[face_index].astype(float)

	raise ValueError(
		"Unable to parse landmarks. Expected shape (68,2) or (N,68,2), "
		f"got {arr.shape}."
	)


def extract_emotion_dict(
	emotion_output: Optional[Any],
	face_index: int = 0,
) -> Optional[Dict[str, float]]:
	"""Parse py-feat emotion output into a normalized emotion-probability dict."""
	if emotion_output is None:
		return None

	if isinstance(emotion_output, dict):
		return {str(k).lower(): float(v) for k, v in emotion_output.items()}

	arr = np.asarray(emotion_output)

	# Common py-feat shape for one face in your code path is often (1,1,7)
	if arr.ndim == 3:
		if face_index >= arr.shape[0]:
			return None
		probs = arr[face_index][0]
	elif arr.ndim == 2:
		if face_index >= arr.shape[0]:
			return None
		probs = arr[face_index]
	elif arr.ndim == 1:
		probs = arr
	else:
		return None

	if probs.size < 7:
		return None

	labels = ["anger", "disgust", "fear", "happiness", "sadness", "surprise", "neutral"]
	return {labels[i]: float(probs[i]) for i in range(7)}


def extract_au_dict(
	au_output: Optional[Any],
	face_index: int = 0,
	au_order: Iterable[str] = DEFAULT_AU_ORDER,
) -> Optional[Dict[str, float]]:
	"""Parse AU outputs into a dictionary keyed by AU name (e.g., AU04)."""
	if au_output is None:
		return None

	if isinstance(au_output, dict):
		return {str(k).upper(): float(v) for k, v in au_output.items()}

	arr = np.asarray(au_output)
	if arr.ndim == 2:
		if face_index >= arr.shape[0]:
			return None
		values = arr[face_index]
	elif arr.ndim == 1:
		values = arr
	else:
		return None

	names = list(au_order)
	if values.size < len(names):
		names = names[: values.size]

	return {names[i].upper(): float(values[i]) for i in range(len(names))}


class StressCalculator:
	"""Compute stress from py-feat outputs using frame window aggregation.

	The calculator returns both:
	- raw frame stress (0..100)
	- smoothed stress using rolling window + EMA (0..100)
	
	AU configuration is resolved from app_config presets and custom settings.
	"""

	def __init__(
		self,
		window_size: int = 15,
		ema_alpha: float = 0.35,
		geometry_weight: float = 0.45,
		emotion_weight: float = 0.35,
		au_weight: float = 0.20,
		au_list: Optional[list] = None,
		au_weights: Optional[Dict[str, float]] = None,
	) -> None:
		self.window_size = max(window_size, 2)
		self.ema_alpha = _clip01(ema_alpha)
		self.geometry_weight = max(geometry_weight, 0.0)
		self.emotion_weight = max(emotion_weight, 0.0)
		self.au_weight = max(au_weight, 0.0)

		# Resolve AU configuration
		if au_list is None:
			au_list = self._resolve_au_list_from_config()
		
		self.au_list = au_list or []
		
		# Use provided weights or auto-calculate from AU list order
		if au_weights is None:
			self.au_weights = au_utils.calculate_au_weights(self.au_list)
		else:
			self.au_weights = au_weights or {}

		self._window_scores: deque[float] = deque(maxlen=self.window_size)
		self._ema_score: Optional[float] = None

	@staticmethod
	def _resolve_au_list_from_config() -> list:
		"""Resolve AU list from app_config settings."""
		try:
			import app_config
			
			preset = getattr(app_config, "AU_PRESET", "ranked").lower().strip()
			custom_list = getattr(app_config, "AU_CUSTOM_LIST", [])
			
			if preset == "custom":
				if custom_list:
					return list(custom_list)
				else:
					# Fallback to all if custom is empty
					return au_utils.get_au_preset("all")
			else:
				# Use preset (ranked or all)
				result = au_utils.get_au_preset(preset)
				return result if result else au_utils._get_default_pyfeat_aus()
		except Exception:
			# Fallback to default
			return au_utils._get_default_pyfeat_aus()

	def reset(self) -> None:
		"""Clear state for a fresh sequence."""
		self._window_scores.clear()
		self._ema_score = None

	def process_frame(
		self,
		detected_landmarks: Any,
		*,
		au_output: Optional[Any] = None,
		emotion_output: Optional[Any] = None,
		face_index: int = 0,
	) -> FrameStressResult:
		"""Process one frame and update rolling stress state.

		Parameters are raw py-feat outputs (or compatible dict/arrays).
		"""
		landmarks = extract_landmarks_array(detected_landmarks, face_index=face_index)
		geometric_metrics = self._compute_geometric_metrics(landmarks)
		geometric_stress = self._compute_geometric_stress(geometric_metrics)

		emotions = extract_emotion_dict(emotion_output, face_index=face_index)
		emotion_stress = self._compute_emotion_stress(emotions) if emotions is not None else None

		aus = extract_au_dict(au_output, face_index=face_index)
		au_stress = self._compute_au_stress(aus) if aus is not None else None

		raw_score_01 = self._fuse_components(
			geometric_stress=geometric_stress,
			emotion_stress=emotion_stress,
			au_stress=au_stress,
		)

		self._window_scores.append(raw_score_01)

		if self._ema_score is None:
			self._ema_score = raw_score_01
		else:
			self._ema_score = self.ema_alpha * raw_score_01 + (1.0 - self.ema_alpha) * self._ema_score

		rolling_mean = float(np.mean(self._window_scores))
		smoothed_01 = (rolling_mean + self._ema_score) / 2.0

		return FrameStressResult(
			raw_stress_0_100=raw_score_01 * 100.0,
			smoothed_stress_0_100=smoothed_01 * 100.0,
			geometric_stress_0_1=geometric_stress,
			au_stress_0_1=au_stress,
			emotion_stress_0_1=emotion_stress,
			eye_openness=geometric_metrics["eye_openness"],
			eyebrow_distance=geometric_metrics["eyebrow_distance"],
			mouth_tension=geometric_metrics["mouth_tension"],
			frames_in_window=len(self._window_scores),
		)

	def get_window_summary(self) -> Dict[str, float]:
		"""Return summary statistics for the current rolling window."""
		if not self._window_scores:
			return {"window_mean_0_100": 0.0, "window_std_0_100": 0.0, "num_frames": 0}

		arr = np.asarray(self._window_scores, dtype=float)
		return {
			"window_mean_0_100": float(np.mean(arr) * 100.0),
			"window_std_0_100": float(np.std(arr) * 100.0),
			"num_frames": float(arr.size),
		}

	def _compute_geometric_metrics(self, lm: np.ndarray) -> Dict[str, float]:
		"""Compute normalized geometry features from 68-point landmarks."""
		scale = _face_scale(lm)

		left_eye = lm[[36, 37, 38, 39, 40, 41]]
		right_eye = lm[[42, 43, 44, 45, 46, 47]]
		eye_openness = (_eye_ear(left_eye) + _eye_ear(right_eye)) / 2.0

		left_brow_center = np.mean(lm[17:22], axis=0)
		right_brow_center = np.mean(lm[22:27], axis=0)
		left_eye_center = np.mean(left_eye, axis=0)
		right_eye_center = np.mean(right_eye, axis=0)
		brow_eye_left = _safe_distance(left_brow_center, left_eye_center) / scale
		brow_eye_right = _safe_distance(right_brow_center, right_eye_center) / scale
		eyebrow_distance = (brow_eye_left + brow_eye_right) / 2.0

		mouth_width = _safe_distance(lm[48], lm[54]) / scale
		mouth_open = _safe_distance(lm[62], lm[66]) / scale
		upper_lower_lip_dist = _safe_distance(lm[51], lm[57]) / scale

		# Wider + compressed lips is treated as higher tension.
		mouth_tension = mouth_width / max(upper_lower_lip_dist + mouth_open, 1e-6)

		return {
			"eye_openness": float(eye_openness),
			"eyebrow_distance": float(eyebrow_distance),
			"mouth_tension": float(mouth_tension),
		}

	def _compute_geometric_stress(self, features: Dict[str, float]) -> float:
		"""Convert geometric features to stress proxy in [0,1]."""
		eye_stress = _normalize_metric(features["eye_openness"], low=0.16, high=0.34, invert=True)
		brow_stress = _normalize_metric(features["eyebrow_distance"], low=0.06, high=0.18, invert=True)
		mouth_stress = _normalize_metric(features["mouth_tension"], low=1.2, high=3.6, invert=False)

		# Slightly favor eye and brow changes for stress estimation.
		return _clip01(0.4 * eye_stress + 0.35 * brow_stress + 0.25 * mouth_stress)

	def _compute_emotion_stress(self, emotions: Dict[str, float]) -> float:
		"""Emotion-based stress from py-feat probability outputs."""
		anger = emotions.get("anger", 0.0)
		disgust = emotions.get("disgust", 0.0)
		fear = emotions.get("fear", 0.0)
		happiness = emotions.get("happiness", 0.0)
		sadness = emotions.get("sadness", 0.0)
		surprise = emotions.get("surprise", 0.0)
		neutral = emotions.get("neutral", 0.0)

		score = (
			0.95 * fear
			+ 0.85 * anger
			+ 0.60 * sadness
			+ 0.45 * disgust
			+ 0.20 * surprise
			- 0.55 * happiness
			- 0.15 * neutral
		)
		return _clip01(score)

	def _compute_au_stress(self, aus: Dict[str, float]) -> float:
		"""AU-based stress using configured AU list and weights.

		Uses AUs configured in app_config (via AU_PRESET or AU_CUSTOM_LIST).
		Weights are either provided or auto-calculated from AU list order.
		"""
		if not self.au_list or not self.au_weights:
			return 0.0
		
		score = 0.0
		for au in self.au_list:
			weight = self.au_weights.get(au, 0.0)
			value = aus.get(au, 0.0)
			score += weight * value
		
		return _clip01(score)

	def _fuse_components(
		self,
		*,
		geometric_stress: float,
		emotion_stress: Optional[float],
		au_stress: Optional[float],
	) -> float:
		"""Fuse available components while re-normalizing missing inputs."""
		weighted_sum = self.geometry_weight * geometric_stress
		weight_total = self.geometry_weight

		if emotion_stress is not None:
			weighted_sum += self.emotion_weight * emotion_stress
			weight_total += self.emotion_weight

		if au_stress is not None:
			weighted_sum += self.au_weight * au_stress
			weight_total += self.au_weight

		if weight_total <= 1e-9:
			return _clip01(geometric_stress)

		return _clip01(weighted_sum / weight_total)

