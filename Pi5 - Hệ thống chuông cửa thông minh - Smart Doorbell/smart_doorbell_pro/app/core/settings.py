from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from app.core.env import as_bool, get_env, load_env_file


def _split_csv(value: str | None, default: List[str]) -> List[str]:
    if not value:
        return list(default)
    return [v.strip() for v in value.split(",") if v.strip()]


@dataclass
class Settings:
    project_root: Path
    data_dir: Path
    models_dir: Path
    logs_dir: Path
    face_db_path: Path
    events_log_path: Path

    camera_index: int = 0
    camera_width: int = 640
    camera_height: int = 480
    face_detection_confidence: float = 0.6

    recognition_threshold: float = 0.45
    recognition_every_n_frames: int = 5

    embedding_model_key: str = "embedding_mobilenetv2"
    liveness_model_key: str = "liveness_modelrgb"

    auto_unlock_groups: List[str] = field(default_factory=lambda: ["owner", "family"])
    door_unlock_seconds: float = 5.0
    doorlock_enabled: bool = False

    pir_recent_window_sec: float = 6.0
    button_bounce_sec: float = 0.2
    button_pin: int = 17
    pir_pin: int = 27
    relay_pin: int = 22

    liveness_multi_frame_count: int = 5
    liveness_blur_base: float = 100.0
    liveness_blur_min: float = 50.0
    liveness_blur_area_ref: float = 6400.0
    liveness_movement_ratio: float = 0.15

    telegram_enabled: bool = True
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    log_level: str = "INFO"

    def ensure_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_env(cls) -> "Settings":
        root = Path(__file__).resolve().parents[2]
        load_env_file(root / ".env", override=False)

        data_dir = root / "app" / "data"
        models_dir = root / "assets" / "models"
        logs_dir = root / "logs"
        face_db_path = data_dir / "face_db.json"
        events_log_path = logs_dir / "events.jsonl"

        settings = cls(
            project_root=root,
            data_dir=data_dir,
            models_dir=models_dir,
            logs_dir=logs_dir,
            face_db_path=face_db_path,
            events_log_path=events_log_path,
            camera_index=int(get_env("CAMERA_INDEX", 0)),
            camera_width=int(get_env("CAMERA_WIDTH", 640)),
            camera_height=int(get_env("CAMERA_HEIGHT", 480)),
            face_detection_confidence=float(get_env("FACE_DETECTION_CONFIDENCE", 0.6)),
            recognition_threshold=float(get_env("RECOGNITION_THRESHOLD", 0.45)),
            recognition_every_n_frames=int(get_env("RECOGNITION_EVERY_N_FRAMES", 5)),
            embedding_model_key=str(get_env("EMBEDDING_MODEL_KEY", "embedding_mobilenetv2")),
            liveness_model_key=str(get_env("LIVENESS_MODEL_KEY", "liveness_modelrgb")),
            auto_unlock_groups=_split_csv(
                get_env("AUTO_UNLOCK_GROUPS", "owner,family"), ["owner", "family"]
            ),
            door_unlock_seconds=float(get_env("DOOR_UNLOCK_SECONDS", 5)),
            doorlock_enabled=as_bool(get_env("DOORLOCK_ENABLED", "false")),
            pir_recent_window_sec=float(get_env("PIR_RECENT_WINDOW_SEC", 6)),
            button_bounce_sec=float(get_env("BUTTON_BOUNCE_SEC", 0.2)),
            button_pin=int(get_env("BUTTON_PIN", 17)),
            pir_pin=int(get_env("PIR_PIN", 27)),
            relay_pin=int(get_env("RELAY_PIN", 22)),
            liveness_multi_frame_count=int(get_env("LIVENESS_MULTI_FRAME_COUNT", 5)),
            liveness_blur_base=float(get_env("LIVENESS_BLUR_BASE", 100.0)),
            liveness_blur_min=float(get_env("LIVENESS_BLUR_MIN", 50.0)),
            liveness_blur_area_ref=float(get_env("LIVENESS_BLUR_AREA_REF", 6400.0)),
            liveness_movement_ratio=float(get_env("LIVENESS_MOVEMENT_RATIO", 0.15)),
            telegram_enabled=as_bool(get_env("TELEGRAM_ENABLED", "true")),
            telegram_bot_token=str(get_env("TELEGRAM_BOT_TOKEN", "")),
            telegram_chat_id=str(get_env("TELEGRAM_CHAT_ID", "")),
            log_level=str(get_env("LOG_LEVEL", "INFO")),
        )
        settings.ensure_dirs()
        return settings