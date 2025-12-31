import json
import os
import threading
import uuid
from datetime import datetime

import cv2

from config import (
    PUBLIC_BASE_URL,
    EVENT_MEDIA_DIR,
    EVENT_MAX_ITEMS,
    EVENT_LOG_ENABLED,
    EVENT_LOG_PATH,
)


class EventStore:
    def __init__(self, media_dir, max_items=200, log_enabled=True, log_path=""):
        self.media_dir = media_dir
        self.max_items = max_items
        self.log_enabled = bool(log_enabled)
        self.log_path = log_path
        self._lock = threading.Lock()
        self._events = []
        self._last_image_url = ""
        self._ensure_media_dir()

    def _ensure_media_dir(self):
        os.makedirs(self.media_dir, exist_ok=True)

    def _ensure_log_dir(self):
        if not self.log_enabled or not self.log_path:
            return
        os.makedirs(os.path.dirname(self.log_path) or ".", exist_ok=True)

    def _append_log(self, event):
        if not self.log_enabled or not self.log_path:
            return
        self._ensure_log_dir()
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=True) + "\n")
        except Exception:
            return

    def add_event(self, event_type, image_bgr, person_name=None, source="gui", meta=None):
        self._ensure_media_dir()
        event_id = f"evt_{uuid.uuid4().hex[:8]}"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        filename = f"{event_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        path = os.path.join(self.media_dir, filename)
        try:
            cv2.imwrite(path, image_bgr)
        except Exception:
            return None

        image_url = f"{PUBLIC_BASE_URL}/media/{filename}"
        event = {
            "eventId": event_id,
            "timestamp": timestamp,
            "type": event_type,
            "imageUrl": image_url,
            "personName": person_name,
            "source": source,
            "meta": meta or {},
        }
        self._last_image_url = image_url
        self._append_log(event)

        with self._lock:
            self._events.insert(0, event)
            if self.max_items and len(self._events) > self.max_items:
                self._events = self._events[: self.max_items]
        return event

    def log_action(self, action, ok, message="", source="api", request_event_id=None):
        event_id = f"act_{uuid.uuid4().hex[:8]}"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        image_url = self._last_image_url or ""
        event = {
            "eventId": event_id,
            "timestamp": timestamp,
            "type": action,
            "imageUrl": image_url,
            "personName": None,
            "source": source,
            "meta": {
                "ok": bool(ok),
                "message": message,
                "requestEventId": request_event_id,
            },
        }
        self._append_log(event)
        return event

    def list_events(self):
        with self._lock:
            return list(self._events)


_event_store = EventStore(
    EVENT_MEDIA_DIR,
    EVENT_MAX_ITEMS,
    log_enabled=EVENT_LOG_ENABLED,
    log_path=EVENT_LOG_PATH,
)


def get_event_store():
    return _event_store
