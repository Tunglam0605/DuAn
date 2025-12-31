# main.py

import cv2
from gpiozero import Button

from camera.camera_manager import CameraManager
from face.face_recognition import FaceRecognition
from face.anti_spoof import LivenessChecker
from utils.utils import draw_face_label, normalize_face_crop
from config import *


def main():
    # =============================
    # INIT
    # =============================
    cam = CameraManager()
    face = FaceRecognition()
    anti_spoof = LivenessChecker(LIVENESS_MODEL_PATH)

    button = Button(BUTTON_PIN)

    frame_count = 0

    last_real_face = None
    last_embedding = None
    last_bbox = None

    # =============================
    # DOORBELL CALLBACK
    # =============================
    def on_button():
        nonlocal last_real_face, last_embedding, last_bbox

        frame = cam.get_frame()
        results = face.detect_faces(frame)

        if not results.detections:
            print("[Doorbell] Không phát hiện khuôn mặt")
            return

        best = max(
            results.detections,
            key=lambda d: d.location_data.relative_bounding_box.width *
                          d.location_data.relative_bounding_box.height
        )

        face_crop, emb, bbox = face.update_last_face(frame, best)

        # ---------- ANTI SPOOF ----------
        face_crop = normalize_face_crop(face_crop)
        if not anti_spoof.is_real(face_crop, bbox):
            print("[Cảnh báo] Phát hiện khuôn mặt giả")
            return

        id, name, score = face.recognize_embedding(emb)

        print(f"[Doorbell] Nhận diện: {id or -1} | {name or 'Unknown'} | Score={score:.2f}")

    button.when_pressed = on_button

    # =============================
    # MAIN LOOP
    # =============================
    while True:
        frame = cam.get_frame()

        # ---------- FACE DETECTION (SKIP FRAME) ----------
        if frame_count % N_DETECTION_FRAMES == 0:
            results = face.detect_faces(frame)

            if results.detections:
                best = max(
                    results.detections,
                    key=lambda d: d.location_data.relative_bounding_box.width *
                                  d.location_data.relative_bounding_box.height
                )

                face_crop, emb, bbox = face.update_last_face(frame, best)

                # ---------- ANTI SPOOF ----------
                # face_crop = normalize_face_crop(face_crop)
                # if anti_spoof.is_real(face_crop, bbox):
                last_real_face = face_crop
                last_embedding = emb
                last_bbox = bbox
                # else:
                #     last_real_face = None
                #     last_embedding = None
                #     last_bbox = None

        # ---------- DISPLAY ----------
        display = cv2.flip(frame, 1)

        if last_bbox is not None and last_embedding is not None:
            id, name, score = face.recognize_embedding(last_embedding)
            if results.detections:
                draw_face_label(display, last_bbox, id, name, score)

        display = cv2.cvtColor(display, cv2.COLOR_BGR2RGB)
        cv2.imshow("Preview", display)

        # =============================
        # KEYBOARD CONTROL
        # =============================
        key = cv2.waitKey(1) & 0xFF

        # Thoát
        if key == ord('q'):
            print("[Hệ thống] Thoát chương trình")
            break

        # Thêm người mới
        elif key == ord('e'):
            if last_real_face is None or last_embedding is None:
                print("[Enroll] Không có khuôn mặt thật để thêm")
                continue

            name = input("[Enroll] Nhập tên người cần thêm: ").strip()
            if not name:
                print("[Enroll] Tên không hợp lệ")
                continue

            pid, name, state = face.add_new_person(name, last_embedding, id)
            message = f"Đã thêm" if state == "new" else f"Đã cập nhật"
            print(f"[Enroll] " + message + ": {name} (id={pid})")

        frame_count += 1

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
