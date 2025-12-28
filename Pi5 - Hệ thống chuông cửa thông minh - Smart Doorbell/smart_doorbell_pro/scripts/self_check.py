from __future__ import annotations

import importlib
import sys
from pathlib import Path


def _try_import(module_name: str):
    try:
        importlib.import_module(module_name)
        return True, None
    except Exception as exc:
        return False, exc


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    print("Smart Doorbell Pro self-check")

    modules = [
        "app",
        "app.main",
        "app.controller",
        "app.core.env",
        "app.core.logger",
        "app.core.settings",
        "app.models.registry",
        "app.services.camera",
        "app.services.triggers",
        "app.services.face_db",
        "app.services.face_recognizer",
        "app.services.liveness_checker",
        "app.services.door_lock",
        "app.services.telegram_notifier",
        "app.services.overlay",
        "app.services.event_store",
        "app.gui.app_window",
        "app.gui.tab_live",
        "app.gui.tab_people",
        "app.gui.dialogs",
        "app.gui.qt_utils",
    ]

    failures = []
    for module_name in modules:
        ok, exc = _try_import(module_name)
        if ok:
            print(f"[OK] {module_name}")
        else:
            print(f"[ERROR] {module_name}: {exc}")
            failures.append((module_name, exc))

    try:
        from app.core.settings import Settings
        from app.models.registry import sanity_check

        settings = Settings.from_env()
        missing = sanity_check(
            ["embedding_mobilenetv2", "liveness_modelrgb"],
            settings.models_dir,
        )
        if missing:
            print("[WARN] Missing models: " + ", ".join(missing))
        else:
            print("[OK] Model registry sanity check")
    except Exception as exc:
        print(f"[ERROR] Model registry check failed: {exc}")
        failures.append(("model_registry", exc))

    print("Run from project root: python run.py (or python -m app.main)")

    if failures:
        print(f"Self-check failed: {len(failures)} issue(s).")
        return 1

    print("Self-check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
