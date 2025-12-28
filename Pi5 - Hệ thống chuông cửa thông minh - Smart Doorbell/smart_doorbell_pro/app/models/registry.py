from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


@dataclass(frozen=True)
class ModelSpec:
    key: str
    filename: str
    kind: str
    notes: str = ""


REGISTRY: Dict[str, ModelSpec] = {
    "embedding_mobilenetv2": ModelSpec(
        key="embedding_mobilenetv2",
        filename="MobileNet-v2_float.tflite",
        kind="tflite",
        notes="Default embedding model",
    ),
    "liveness_modelrgb": ModelSpec(
        key="liveness_modelrgb",
        filename="modelrgb.onnx",
        kind="onnx",
        notes="Default liveness model",
    ),
    "embedding_mobilefacenet": ModelSpec(
        key="embedding_mobilefacenet",
        filename="MobileFaceNet.tflite",
        kind="tflite",
        notes="Optional embedding model",
    ),
    "liveness_tflite_fas": ModelSpec(
        key="liveness_tflite_fas",
        filename="FaceAntiSpoofing.tflite",
        kind="tflite",
        notes="Optional liveness model",
    ),
    "gender_age": ModelSpec(
        key="gender_age",
        filename="genderage.onnx",
        kind="onnx",
        notes="Optional gender/age model",
    ),
    "landmark_2d106": ModelSpec(
        key="landmark_2d106",
        filename="2d106det.onnx",
        kind="onnx",
        notes="Optional landmark model",
    ),
    "insightface_glintr100": ModelSpec(
        key="insightface_glintr100",
        filename="glintr100.onnx",
        kind="onnx",
        notes="Optional ArcFace model",
    ),
}


def _default_models_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "assets" / "models"


def get_model(key: str, models_dir: Path | None = None) -> Tuple[ModelSpec, Path]:
    if key not in REGISTRY:
        raise KeyError(f"Unknown model key: {key}")
    spec = REGISTRY[key]
    base = models_dir or _default_models_dir()
    return spec, base / spec.filename


def sanity_check(required_keys: Iterable[str], models_dir: Path | None = None) -> List[str]:
    missing = []
    base = models_dir or _default_models_dir()
    for key in required_keys:
        spec = REGISTRY.get(key)
        if spec is None:
            missing.append(key)
            continue
        if not (base / spec.filename).exists():
            missing.append(key)
    return missing