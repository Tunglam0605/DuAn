from __future__ import annotations

if __name__ == "__main__":
    from pathlib import Path
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    print("Please run from project root: python run.py (or python -m app.main)")
    raise SystemExit(0)

import threading
import time

from app.core.logger import get_logger


class DoorLock:
    def __init__(self, settings):
        self.logger = get_logger(__name__)
        self.settings = settings
        self.enabled = bool(settings.doorlock_enabled)
        self.device = None
        if self.enabled:
            self._init_device()

    def _init_device(self) -> None:
        try:
            from gpiozero import OutputDevice

            self.device = OutputDevice(self.settings.relay_pin, active_high=True, initial_value=False)
            self.logger.info("Door lock relay initialized on GPIO %s", self.settings.relay_pin)
        except Exception as exc:
            self.logger.warning("GPIO relay unavailable: %s", exc)
            self.device = None
            self.enabled = False

    def unlock(self, seconds: float | None = None) -> bool:
        if not self.enabled or not self.device:
            return False
        seconds = seconds if seconds is not None else self.settings.door_unlock_seconds
        try:
            self.device.on()
            time.sleep(seconds)
            self.device.off()
            return True
        except Exception as exc:
            self.logger.warning("Failed to toggle relay: %s", exc)
            return False

    def unlock_async(self, seconds: float | None = None) -> None:
        thread = threading.Thread(target=self.unlock, args=(seconds,), daemon=True)
        thread.start()
