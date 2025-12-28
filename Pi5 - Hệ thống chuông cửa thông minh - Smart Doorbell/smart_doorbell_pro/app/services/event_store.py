from __future__ import annotations

if __name__ == "__main__":
    from pathlib import Path
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    print("Please run from project root: python run.py (or python -m app.main)")
    raise SystemExit(0)

import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


class EventStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.lock = threading.Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, event: Dict[str, Any]) -> None:
        line = json.dumps(event, ensure_ascii=False)
        with self.lock, self.path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")

    def log_event(self, **fields: Any) -> None:
        event = {"timestamp": datetime.now().isoformat()}
        event.update(fields)
        self.append(event)
