from __future__ import annotations

if __name__ == "__main__":
    from pathlib import Path
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    print("Please run from project root: python run.py (or python -m app.main)")
    raise SystemExit(0)

import time

from app.core.logger import get_logger


class TriggerService:
    def __init__(self, settings):
        self.logger = get_logger(__name__)
        self.settings = settings
        self.available = False
        self.button = None
        self.motion_sensor = None
        self.last_motion_time = 0.0
        self._callback = None

        try:
            from gpiozero import Button, MotionSensor

            self.Button = Button
            self.MotionSensor = MotionSensor
            self.available = True
        except Exception as exc:
            self.logger.warning("gpiozero unavailable: %s", exc)

    def start(self, on_trigger) -> bool:
        if not self.available:
            return False
        self._callback = on_trigger
        self.motion_sensor = self.MotionSensor(self.settings.pir_pin)
        self.button = self.Button(self.settings.button_pin, bounce_time=self.settings.button_bounce_sec)
        self.motion_sensor.when_motion = self._on_motion
        self.button.when_pressed = self._on_button
        self.logger.info("Trigger service started (button=%s, pir=%s)", self.settings.button_pin, self.settings.pir_pin)
        return True

    def _on_motion(self) -> None:
        self.last_motion_time = time.time()

    def _on_button(self) -> None:
        now = time.time()
        if now - self.last_motion_time <= self.settings.pir_recent_window_sec:
            if self._callback:
                self._callback()
        else:
            self.logger.info("Button pressed but PIR not recent")

    def stop(self) -> None:
        if self.button:
            try:
                self.button.close()
            except Exception:
                pass
        if self.motion_sensor:
            try:
                self.motion_sensor.close()
            except Exception:
                pass
