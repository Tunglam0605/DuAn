from __future__ import annotations

if __name__ == "__main__":
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    print("Please run from project root: python run.py (or python -m app.main)")
    raise SystemExit(0)

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple

import cv2
import numpy as np

try:
    import mediapipe as mp
except Exception:
    mp = None

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
        self.force_opencv = os.environ.get("FACE_DETECTOR", "").strip().lower() == "opencv"
        if self.force_opencv:
            self.logger.info("Face detector backend forced to OpenCV (FACE_DETECTOR=opencv)")
        self.detector = None
        if mp is not None and not self.force_opencv:
            try:
                self.detector = mp.solutions.face_detection.FaceDetection(
                    model_selection=0,
                    min_detection_confidence=self.settings.face_detection_confidence,
                )
            except Exception as exc:
                self.logger.warning("Mediapipe face detector unavailable: %s", exc)
        else:
            self.logger.warning("Mediapipe not available; using OpenCV detector")
        self.opencv_detector = None
        self.interpreter = None
        self.input_index = None
        self.output_index = None
        self.input_shape = None
        self.opencv_embedding_size = (64, 64)
        self._init_opencv_detector()
        self._load_embedding_model()
        if self.interpreter is None:
            self.logger.warning("Embedding model missing; using OpenCV fallback embedding")

    def _init_opencv_detector(self) -> None:
        try:
            cascade_base = Path(cv2.data.haarcascades)
        except Exception as exc:
            self.logger.warning("OpenCV haarcascade path unavailable: %s", exc)
            return
        cascade_path = cascade_base / "haarcascade_frontalface_default.xml"
        if not cascade_path.exists():
            self.logger.warning("OpenCV haarcascade not found: %s", cascade_path)
            return
        detector = cv2.CascadeClassifier(str(cascade_path))
        if detector.empty():
            self.logger.warning("Failed to load OpenCV haarcascade: %s", cascade_path)
            return
        self.opencv_detector = detector

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
        if self.detector is not None:
            try:
                image_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                result = self.detector.process(image_rgb)
                if result.detections:
                    height, width, _ = frame_bgr.shape
                    best = max(result.detections, key=lambda det: det.score[0])
                    bbox = best.location_data.relative_bounding_box
                    x = max(int(bbox.xmin * width), 0)
                    y = max(int(bbox.ymin * height), 0)
                    w = min(int(bbox.width * width), width - x)
                    h = min(int(bbox.height * height), height - y)
                    if w > 0 and h > 0:
                        return FaceResult(bbox=(x, y, w, h), score=float(best.score[0]))
            except Exception as exc:
                self.logger.warning("Mediapipe detection failed: %s", exc)
        return self._detect_face_opencv(frame_bgr)

    def _detect_face_opencv(self, frame_bgr) -> Optional[FaceResult]:
        if frame_bgr is None or self.opencv_detector is None:
            return None
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)
        faces = self.opencv_detector.detectMultiScale(
            gray,
            scaleFactor=1.05,
            minNeighbors=3,
            minSize=(30, 30),
        )
        if faces is None or len(faces) == 0:
            return None
        x, y, w, h = max(faces, key=lambda rect: rect[2] * rect[3])
        if w <= 0 or h <= 0:
            return None
        return FaceResult(bbox=(int(x), int(y), int(w), int(h)), score=1.0)

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
            return self._extract_embedding_opencv(face_rgb)
        input_data = self._prepare_input(face_rgb)
        self.interpreter.set_tensor(self.input_index, input_data)
        self.interpreter.invoke()
        output = self.interpreter.get_tensor(self.output_index)
        embedding = output.reshape(-1).astype(np.float32)
        norm = np.linalg.norm(embedding) + 1e-9
        return embedding / norm

    def _extract_embedding_opencv(self, face_rgb: np.ndarray) -> Optional[np.ndarray]:
        if face_rgb is None:
            return None
        try:
            gray = cv2.cvtColor(face_rgb, cv2.COLOR_RGB2GRAY)
            gray = cv2.resize(gray, self.opencv_embedding_size, interpolation=cv2.INTER_AREA)
            gray = cv2.equalizeHist(gray)
            embedding = gray.astype(np.float32).reshape(-1)
            norm = np.linalg.norm(embedding) + 1e-9
            return embedding / norm
        except Exception as exc:
            self.logger.warning("Failed to compute OpenCV embedding: %s", exc)
            return None

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
            if stored.size == 0 or stored.size != embedding.size:
                continue
            score = float(np.dot(embedding, stored) / (np.linalg.norm(embedding) * np.linalg.norm(stored) + 1e-9))
            if score > best_score:
                best_score = score
                best_person = person
        return best_person, best_score
