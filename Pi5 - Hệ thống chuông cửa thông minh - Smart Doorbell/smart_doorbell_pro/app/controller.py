from __future__ import annotations

import threading
import time
from typing import Callable, Dict, Optional, Tuple

import cv2

from app.core.logger import get_logger
from app.services.camera import Camera
from app.services.door_lock import DoorLock
from app.services.event_store import EventStore
from app.services.face_db import FaceDB
from app.services.face_recognizer import FaceRecognizer
from app.services.liveness_checker import LivenessChecker
from app.services.telegram_notifier import TelegramNotifier
from app.services.triggers import TriggerService


class Controller:
    def __init__(self, settings):
        self.logger = get_logger(__name__)
        self.settings = settings
        self.face_db = FaceDB(settings.face_db_path)
        self.camera = Camera(settings)
        self.recognizer = FaceRecognizer(settings)
        self.liveness = LivenessChecker(settings)
        self.door_lock = DoorLock(settings)
        self.telegram = TelegramNotifier(settings)
        self.event_store = EventStore(settings.events_log_path)
        self.triggers = TriggerService(settings)
        self.event_callback: Optional[Callable[[Dict], None]] = None
        self._last_result: Optional[Dict] = None
        self._last_face_crop = None
        self._last_embedding = None
        self._lock = threading.Lock()

    def set_event_callback(self, callback: Callable[[Dict], None]) -> None:
        self.event_callback = callback

    def _emit_event(self, result: Dict) -> None:
        if self.event_callback:
            self.event_callback(result)

    def start_hardware(self) -> None:
        started = self.triggers.start(self._handle_trigger_async)
        if not started:
            self.logger.info("Hardware triggers disabled")

    def _handle_trigger_async(self) -> None:
        thread = threading.Thread(target=self.handle_trigger, daemon=True)
        thread.start()

    def handle_trigger(self) -> Dict:
        frame = self.capture_frame()
        result = self.recognize_frame(
            frame,
            log_event=True,
            event_type="button",
            send_telegram=True,
            allow_unlock=True,
        )
        self._emit_event(result)
        return result

    def capture_frame(self):
        return self.camera.read()

    def recognize_frame(
        self,
        frame,
        log_event: bool = False,
        event_type: str = "button",
        send_telegram: bool = False,
        allow_unlock: bool = False,
    ) -> Dict:
        result: Dict[str, Optional[object]] = {
            "known": False,
            "person_id": None,
            "person_name": None,
            "group": None,
            "note": None,
            "score": None,
            "is_real": False,
            "event_type": event_type,
            "bbox": None,
            "frame": frame,
        }

        if frame is None:
            result["event_type"] = "no_face"
            if log_event:
                self.event_store.log_event(**self._event_fields(result))
            self._update_last(result, None, None)
            return result

        embedding, face_result, face_crop = self.recognizer.extract_embedding_from_frame(frame)
        if face_result is None or embedding is None:
            result["event_type"] = "no_face"
            if log_event:
                self.event_store.log_event(**self._event_fields(result))
            self._update_last(result, None, None)
            return result

        result["bbox"] = face_result.bbox
        people = self.face_db.list_people()
        person, score = self.recognizer.match(embedding, people)
        if person is not None:
            result.update(
                {
                    "person_id": person.get("id"),
                    "person_name": person.get("name"),
                    "group": person.get("group"),
                    "note": person.get("note"),
                }
            )
        result["score"] = score if score >= 0 else 0.0

        is_real, avg_prob, _ = self.liveness.assess(frame, face_result.bbox)
        result["is_real"] = is_real

        known = bool(person) and score >= self.settings.recognition_threshold and is_real
        result["known"] = known

        if not is_real:
            result["event_type"] = "spoof"

        if allow_unlock and known:
            if result.get("group") in self.settings.auto_unlock_groups:
                self.door_lock.unlock_async(self.settings.door_unlock_seconds)

        if send_telegram:
            if not is_real:
                self.telegram.send_spoof(frame)
            elif known:
                self.telegram.send_known(frame, result["person_name"], result["group"], score)
            else:
                self.telegram.send_unknown(frame, score)

        if log_event:
            self.event_store.log_event(**self._event_fields(result))

        self._update_last(result, face_crop, embedding)
        return result

    def _event_fields(self, result: Dict) -> Dict:
        return {
            "known": bool(result.get("known")),
            "person_id": result.get("person_id"),
            "person_name": result.get("person_name"),
            "group": result.get("group"),
            "note": result.get("note"),
            "score": result.get("score"),
            "is_real": bool(result.get("is_real")),
            "event_type": result.get("event_type"),
        }

    def _update_last(self, result: Dict, face_crop, embedding) -> None:
        with self._lock:
            self._last_result = dict(result)
            if face_crop is not None:
                self._last_face_crop = face_crop
            if embedding is not None:
                self._last_embedding = embedding

    def get_last_result(self) -> Optional[Dict]:
        with self._lock:
            return dict(self._last_result) if self._last_result else None

    def get_last_face_crop(self):
        with self._lock:
            return None if self._last_face_crop is None else self._last_face_crop.copy()

    def get_last_embedding(self):
        with self._lock:
            return None if self._last_embedding is None else self._last_embedding.copy()

    def capture_face_embedding(self) -> Tuple[Optional[object], Optional[object]]:
        frame = self.capture_frame()
        if frame is None:
            return None, None
        embedding, face_result, face_crop = self.recognizer.extract_embedding_from_frame(frame)
        if embedding is None:
            return None, None
        self._update_last({"event_type": "capture"}, face_crop, embedding)
        return embedding, face_crop

    def embedding_from_file(self, file_path: str) -> Tuple[Optional[object], Optional[object]]:
        frame = cv2.imread(file_path)
        if frame is None:
            return None, None
        embedding, face_result, face_crop = self.recognizer.extract_embedding_from_frame(frame)
        if embedding is None:
            return None, None
        return embedding, face_crop

    def manual_unlock(self, context: Optional[Dict] = None) -> None:
        self.door_lock.unlock_async(self.settings.door_unlock_seconds)
        if context is None:
            context = self.get_last_result() or {}
        event = {
            "known": context.get("known", False),
            "person_id": context.get("person_id"),
            "person_name": context.get("person_name"),
            "group": context.get("group"),
            "note": context.get("note"),
            "score": context.get("score"),
            "is_real": context.get("is_real", True),
            "event_type": "manual_unlock",
        }
        self.event_store.log_event(**event)

    def run_headless(self) -> None:
        self.start_hardware()
        self.logger.info("Headless mode running. Press Ctrl+C to exit.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Exiting headless mode")
