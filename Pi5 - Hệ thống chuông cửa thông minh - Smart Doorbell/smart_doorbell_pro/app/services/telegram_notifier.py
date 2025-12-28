from __future__ import annotations

if __name__ == "__main__":
    from pathlib import Path
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    print("Please run from project root: python run.py (or python -m app.main)")
    raise SystemExit(0)

from typing import Optional

import cv2
import requests

from app.core.logger import get_logger


class TelegramNotifier:
    def __init__(self, settings, enabled: Optional[bool] = None):
        self.logger = get_logger(__name__)
        self.token = settings.telegram_bot_token
        self.chat_id = settings.telegram_chat_id
        self.enabled = settings.telegram_enabled if enabled is None else enabled
        if not self.token or not self.chat_id:
            self.enabled = False

    def _send_photo(self, image_bgr, caption: str) -> bool:
        if not self.enabled:
            return False
        ok, buffer = cv2.imencode(".jpg", image_bgr)
        if not ok:
            return False
        url = f"https://api.telegram.org/bot{self.token}/sendPhoto"
        files = {"photo": ("snapshot.jpg", buffer.tobytes())}
        data = {"chat_id": self.chat_id, "caption": caption}
        try:
            response = requests.post(url, data=data, files=files, timeout=10)
            if response.status_code != 200:
                self.logger.warning("Telegram send failed: %s", response.text)
                return False
            return True
        except Exception as exc:
            self.logger.warning("Telegram send error: %s", exc)
            return False

    def send_known(self, image_bgr, name: str, group: str, score: float) -> bool:
        caption = f"? Ngu?i quen: {name} | group={group} | score={score:.3f}"
        return self._send_photo(image_bgr, caption)

    def send_unknown(self, image_bgr, score: float) -> bool:
        caption = f"?? Ngu?i l? | score={score:.3f}"
        return self._send_photo(image_bgr, caption)

    def send_spoof(self, image_bgr) -> bool:
        caption = "?? PhÃ¡t hi?n khuÃ´n m?t gi? (spoof)"
        return self._send_photo(image_bgr, caption)
