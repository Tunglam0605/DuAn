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
from typing import Dict, List, Optional

import numpy as np


def _iso_now() -> str:
    return datetime.now().isoformat()


def _normalize(vec: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(vec) + 1e-9
    return vec / norm


def _coerce_embedding(value) -> np.ndarray:
    if isinstance(value, np.ndarray):
        return value.astype(np.float32)
    return np.array(value, dtype=np.float32)


class FaceDB:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.lock = threading.Lock()
        self.people: List[Dict] = []
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text("[]", encoding="utf-8")
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = []

        migrated = False
        now = _iso_now()
        for person in data:
            if "group" not in person:
                person["group"] = "friend"
                migrated = True
            if "note" not in person:
                person["note"] = ""
                migrated = True
            if "created_at" not in person:
                person["created_at"] = now
                migrated = True
            if "updated_at" not in person:
                person["updated_at"] = person.get("created_at", now)
                migrated = True
        self.people = data
        if migrated:
            self._save()

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(self.people, f, ensure_ascii=False, indent=2)

    def _next_id(self) -> str:
        max_id = 0
        for person in self.people:
            pid = str(person.get("id", ""))
            if pid.isdigit():
                max_id = max(max_id, int(pid))
        return f"{max_id + 1:03d}"

    def list_people(self) -> List[Dict]:
        with self.lock:
            return [dict(person) for person in self.people]

    def get_person(self, person_id: str) -> Optional[Dict]:
        with self.lock:
            for person in self.people:
                if person.get("id") == person_id:
                    return dict(person)
        return None

    def add_person(self, name: str, group: str, note: str, embedding) -> str:
        with self.lock:
            person_id = self._next_id()
            emb = _normalize(_coerce_embedding(embedding))
            now = _iso_now()
            record = {
                "id": person_id,
                "name": name,
                "group": group,
                "note": note,
                "created_at": now,
                "updated_at": now,
                "embedding": emb.astype(float).tolist(),
            }
            self.people.append(record)
            self._save()
        return person_id

    def update_person(
        self,
        person_id: str,
        name: Optional[str] = None,
        group: Optional[str] = None,
        note: Optional[str] = None,
        embedding=None,
    ) -> bool:
        with self.lock:
            for person in self.people:
                if person.get("id") != person_id:
                    continue
                if name is not None:
                    person["name"] = name
                if group is not None:
                    person["group"] = group
                if note is not None:
                    person["note"] = note
                if embedding is not None:
                    new_emb = _normalize(_coerce_embedding(embedding))
                    old_emb = _coerce_embedding(person.get("embedding", []))
                    if old_emb.size == 0:
                        merged = new_emb
                    elif old_emb.size != new_emb.size:
                        merged = new_emb
                    else:
                        merged = _normalize((old_emb + new_emb) / 2.0)
                    person["embedding"] = merged.astype(float).tolist()
                person["updated_at"] = _iso_now()
                self._save()
                return True
        return False

    def delete_person(self, person_id: str) -> bool:
        with self.lock:
            for idx, person in enumerate(self.people):
                if person.get("id") == person_id:
                    self.people.pop(idx)
                    self._save()
                    return True
        return False
