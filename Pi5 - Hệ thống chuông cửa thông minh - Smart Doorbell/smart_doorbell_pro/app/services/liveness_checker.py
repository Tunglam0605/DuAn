from __future__ import annotations

if __name__ == "__main__":
    from pathlib import Path
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    print("Please run from project root: python run.py (or python -m app.main)")
    raise SystemExit(0)

from collections import deque
from typing import Optional, Tuple

import cv2
import numpy as np

from app.core.logger import get_logger
from app.models.registry import get_model


class LivenessChecker:
    def __init__(self, settings):
        self.logger = get_logger(__name__)
        self.settings = settings
        self.session = None
        self.input_name = None
        self.input_layout = "nhwc"
        self.input_size = (80, 80)
        self.prob_buffer = deque(maxlen=self.settings.liveness_multi_frame_count)
        self.last_center: Optional[Tuple[float, float]] = None
        self._load_model()

    def _load_model(self) -> None:
        try:
            import onnxruntime as ort
        except Exception as exc:
            self.logger.warning("ONNXRuntime not available: %s", exc)
            return

        try:
            _, model_path = get_model(self.settings.liveness_model_key, self.settings.models_dir)
            if not model_path.exists():
                self.logger.warning("Liveness model missing: %s", model_path)
                return
            self.session = ort.InferenceSession(str(model_path), providers=["CPUExecutionProvider"])
            input_info = self.session.get_inputs()[0]
            self.input_name = input_info.name
            shape = input_info.shape
            if len(shape) == 4:
                if shape[1] in (1, 3):
                    self.input_layout = "nchw"
                    h = shape[2] if isinstance(shape[2], int) else 80
                    w = shape[3] if isinstance(shape[3], int) else 80
                else:
                    self.input_layout = "nhwc"
                    h = shape[1] if isinstance(shape[1], int) else 80
                    w = shape[2] if isinstance(shape[2], int) else 80
                self.input_size = (int(w), int(h))
            self.logger.info("Loaded liveness model: %s", model_path)
        except Exception as exc:
            self.logger.warning("Failed to load liveness model: %s", exc)

    def reset(self) -> None:
        self.prob_buffer.clear()
        self.last_center = None

    def _blur_ok(self, face_bgr) -> bool:
        gray = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2GRAY)
        variance = cv2.Laplacian(gray, cv2.CV_64F).var()
        area = float(face_bgr.shape[0] * face_bgr.shape[1])
        threshold = max(
            self.settings.liveness_blur_min,
            self.settings.liveness_blur_base * (area / self.settings.liveness_blur_area_ref),
        )
        return variance >= threshold

    def _movement_ok(self, bbox) -> bool:
        x, y, w, h = bbox
        center = (x + w / 2.0, y + h / 2.0)
        if self.last_center is None:
            self.last_center = center
            return False
        dx = center[0] - self.last_center[0]
        dy = center[1] - self.last_center[1]
        self.last_center = center
        distance = (dx * dx + dy * dy) ** 0.5
        return distance >= (min(w, h) * self.settings.liveness_movement_ratio)

    def _predict_prob(self, face_rgb) -> float:
        if self.session is None:
            return 1.0
        face = cv2.resize(face_rgb, self.input_size)
        face = face.astype(np.float32) / 255.0
        if self.input_layout == "nchw":
            face = np.transpose(face, (2, 0, 1))
        face = np.expand_dims(face, axis=0)
        outputs = self.session.run(None, {self.input_name: face})
        output = outputs[0]
        flat = np.array(output).reshape(-1)
        if flat.size == 0:
            return 0.0
        if flat.size == 1:
            prob = float(flat[0])
        else:
            prob = float(flat[-1])
        return max(0.0, min(1.0, prob))

    def assess(self, frame_bgr, bbox) -> Tuple[bool, float, dict]:
        x, y, w, h = bbox
        face_bgr = frame_bgr[y : y + h, x : x + w]
        face_rgb = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2RGB)

        blur_ok = self._blur_ok(face_bgr)
        movement_ok = self._movement_ok(bbox)
        prob = self._predict_prob(face_rgb)
        self.prob_buffer.append(prob)
        avg_prob = float(np.mean(self.prob_buffer)) if self.prob_buffer else prob

        is_real = avg_prob >= 0.25 or (movement_ok and avg_prob >= 0.18)
        if not blur_ok:
            is_real = False

        details = {
            "blur_ok": blur_ok,
            "movement_ok": movement_ok,
            "prob": prob,
            "avg_prob": avg_prob,
        }
        return is_real, avg_prob, details
