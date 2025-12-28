from __future__ import annotations

if __name__ == "__main__":
    from pathlib import Path
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    print("Please run from project root: python run.py (or python -m app.main)")
    raise SystemExit(0)

import threading
from typing import Optional

import cv2

from app.core.logger import get_logger


class Camera:
    def __init__(self, settings):
        self.logger = get_logger(__name__)
        self.settings = settings
        self.lock = threading.Lock()
        self.picam = None
        self.cap = None
        self.use_picamera2 = False

        self._init_camera()

    def _init_camera(self) -> None:
        try:
            from picamera2 import Picamera2

            self.picam = Picamera2()
            config = self.picam.create_preview_configuration(
                main={"format": "RGB888", "size": (self.settings.camera_width, self.settings.camera_height)}
            )
            self.picam.configure(config)
            self.picam.start()
            self.use_picamera2 = True
            self.logger.info("Camera initialized with Picamera2")
            return
        except Exception as exc:
            self.logger.info("Picamera2 not available (%s). Falling back to OpenCV.", exc)

        self.cap = cv2.VideoCapture(self.settings.camera_index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.settings.camera_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.settings.camera_height)
        if not self.cap.isOpened():
            self.logger.warning("OpenCV camera failed to open")
        else:
            self.logger.info("Camera initialized with OpenCV VideoCapture")

    def read(self) -> Optional[cv2.Mat]:
        with self.lock:
            if self.use_picamera2 and self.picam:
                frame = self.picam.capture_array()
                if frame is None:
                    return None
                return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            if self.cap:
                ok, frame = self.cap.read()
                if not ok:
                    return None
                return frame
        return None

    def release(self) -> None:
        with self.lock:
            if self.picam:
                try:
                    self.picam.stop()
                except Exception:
                    pass
                self.picam = None
            if self.cap:
                self.cap.release()
                self.cap = None
