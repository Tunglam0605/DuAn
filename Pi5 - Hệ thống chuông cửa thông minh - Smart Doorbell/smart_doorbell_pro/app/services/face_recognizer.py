from __future__ import annotations

if __name__ == "__main__":
    from pathlib import Path
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    print("Please run from project root: python run.py (or python -m app.main)")
    raise SystemExit(0)

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import cv2
import numpy as np
import mediapipe as mp

from app.core.logger import get_logger
from app.models.registry import get_model


@dataclass
class FaceResult:
    bbox: Tuple[int, int, int, int]
    score: float


class FaceRecognizer:
    def __init__(self, settings):
        self.logger = get_logger(__name__)
        self.settings = settings
        self.detector = mp.solutions.face_detection.FaceDetection(
            model_selection=0,
            min_detection_confidence=self.settings.face_detection_confidence,
        )
        self.interpreter = None
        self.input_index = None
        self.output_index = None
        self.input_shape = None
        self._load_embedding_model()

    def _load_embedding_model(self) -> None:
        try:
            from tflite_runtime.interpreter import Interpreter
        except Exception:
            try:
                from tensorflow.lite.python.interpreter import Interpreter
            except Exception as exc:
                self.logger.warning("TFLite runtime not available: %s", exc)
                return

        try:
            _, model_path = get_model(self.settings.embedding_model_key, self.settings.models_dir)
            if not model_path.exists():
                self.logger.warning("Embedding model missing: %s", model_path)
                return
            self.interpreter = Interpreter(model_path=str(model_path))
            self.interpreter.allocate_tensors()
            input_details = self.interpreter.get_input_details()[0]
            output_details = self.interpreter.get_output_details()[0]
            self.input_index = input_details["index"]
            self.output_index = output_details["index"]
            self.input_shape = input_details["shape"]
            self.logger.info("Loaded embedding model: %s", model_path)
        except Exception as exc:
            self.logger.warning("Failed to load embedding model: %s", exc)

    def detect_face(self, frame_bgr) -> Optional[FaceResult]:
        if frame_bgr is None:
            return None
        image_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        result = self.detector.process(image_rgb)
        if not result.detections:
            return None

        height, width, _ = frame_bgr.shape
        best = max(result.detections, key=lambda det: det.score[0])
        bbox = best.location_data.relative_bounding_box
        x = max(int(bbox.xmin * width), 0)
        y = max(int(bbox.ymin * height), 0)
        w = min(int(bbox.width * width), width - x)
        h = min(int(bbox.height * height), height - y)
        if w <= 0 or h <= 0:
            return None
        return FaceResult(bbox=(x, y, w, h), score=float(best.score[0]))

    def _prepare_input(self, face_rgb: np.ndarray) -> np.ndarray:
        face = cv2.resize(face_rgb, (224, 224))
        face = face.astype(np.float32)
        face = (face - 127.5) / 128.0
        input_data = np.expand_dims(face, axis=0)

        if self.input_shape is not None and len(self.input_shape) == 4:
            if self.input_shape[1] in (1, 3):
                input_data = np.transpose(input_data, (0, 3, 1, 2))
        return input_data

    def extract_embedding(self, face_rgb: np.ndarray) -> Optional[np.ndarray]:
        if self.interpreter is None:
            return None
        input_data = self._prepare_input(face_rgb)
        self.interpreter.set_tensor(self.input_index, input_data)
        self.interpreter.invoke()
        output = self.interpreter.get_tensor(self.output_index)
        embedding = output.reshape(-1).astype(np.float32)
        norm = np.linalg.norm(embedding) + 1e-9
        return embedding / norm

    def extract_embedding_from_frame(self, frame_bgr) -> Tuple[Optional[np.ndarray], Optional[FaceResult], Optional[np.ndarray]]:
        face_result = self.detect_face(frame_bgr)
        if not face_result:
            return None, None, None
        x, y, w, h = face_result.bbox
        face_bgr = frame_bgr[y : y + h, x : x + w]
        face_rgb = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2RGB)
        embedding = self.extract_embedding(face_rgb)
        return embedding, face_result, face_bgr

    def match(self, embedding: np.ndarray, people: list) -> Tuple[Optional[Dict], float]:
        best_person = None
        best_score = -1.0
        for person in people:
            stored = np.array(person.get("embedding", []), dtype=np.float32)
            if stored.size == 0:
                continue
            score = float(np.dot(embedding, stored) / (np.linalg.norm(embedding) * np.linalg.norm(stored) + 1e-9))
            if score > best_score:
                best_score = score
                best_person = person
        return best_person, best_score
