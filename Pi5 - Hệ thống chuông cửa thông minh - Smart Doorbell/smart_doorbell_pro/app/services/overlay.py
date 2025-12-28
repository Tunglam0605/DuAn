from __future__ import annotations

if __name__ == "__main__":
    from pathlib import Path
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    print("Please run from project root: python run.py (or python -m app.main)")
    raise SystemExit(0)

import cv2


def draw_overlay(frame_bgr, result: dict | None) -> None:
    if frame_bgr is None or not result:
        return
    bbox = result.get("bbox")
    if bbox:
        x, y, w, h = bbox
        cv2.rectangle(frame_bgr, (x, y), (x + w, y + h), (0, 200, 0), 2)
    label_parts = []
    if result.get("person_name"):
        label_parts.append(result["person_name"])
    if result.get("group"):
        label_parts.append(f"{result['group']}")
    score = result.get("score")
    if score is not None:
        label_parts.append(f"{score:.2f}")
    if label_parts and bbox:
        text = " | ".join(label_parts)
        cv2.putText(frame_bgr, text, (bbox[0], max(0, bbox[1] - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 0), 1)
