from __future__ import annotations

import argparse

from app.core.logger import setup_logging
from app.core.settings import Settings
from app.controller import Controller


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Smart Doorbell Pro")
    parser.add_argument("--headless", action="store_true", help="Run without GUI")
    parser.add_argument("--no-telegram", action="store_true", help="Disable Telegram notifications")
    parser.add_argument("--unlock", action="store_true", help="Enable door lock relay")
    parser.add_argument("--log-level", default=None, help="Log level (INFO/DEBUG)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = Settings.from_env()

    if args.log_level:
        settings.log_level = args.log_level
    if args.no_telegram:
        settings.telegram_enabled = False
    if args.unlock:
        settings.doorlock_enabled = True

    setup_logging(settings.log_level)

    controller = Controller(settings)

    if args.headless:
        controller.run_headless()
    else:
        from app.gui.app_window import run_gui

        run_gui(controller, settings)


if __name__ == "__main__":
    main()