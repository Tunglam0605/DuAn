# face/

Thư mục xử lý nhận diện khuôn mặt, liveness và quản lý dữ liệu người quen.

## anti_spoof.py
- Hàm `compute_laplacian_blur(gray)` kiểm tra độ sắc nét để phát hiện ảnh in/screen.
- Class `LivenessChecker`:
  - `preprocess()` chuẩn hóa ảnh cho `modelrgb.onnx` (RGB, [0..1], shape 1x3x112x112).
  - `predict_real_prob()` chạy ONNX và trả về xác suất thật.
  - `detect_face_movement()` đo chuyển động vi mô của bbox.
  - `is_real(face_img, bbox)` kết hợp blur + xác suất + chuyển động để quyết định thật/giả.
- Phụ thuộc `onnxruntime`, `opencv`, `numpy` và các tham số trong `config.py`:
  `LIVENESS_LAPLACIAN_THRESH`, `MIN_FACE_MOVEMENT_RATIO`, `MULTI_FRAME_COUNT`.

## face_recognition.py
- Class `FaceRecognition`:
  - Dùng MediaPipe FaceDetection để phát hiện khuôn mặt.
  - Dùng TFLite (`MobileNet-v2_float.tflite`) để trích xuất embedding.
  - `detect_faces(frame)` có lọc ROI (elip xoay) + coverage + center tolerance.
  - `update_last_face()` lưu `last_face`, `last_embedding`, `last_bbox`.
  - `recognize_embedding()` so khớp cosine với DB, dùng `RECOGNITION_THRESHOLD`.
  - `add_new_person()` thêm/cập nhật người vào DB.
  - `reload_db()` nạp lại DB từ file.
- Phụ thuộc `mediapipe`, `tflite_runtime`, `scipy`, `opencv` và các tham số trong `config.py`:
  `MODEL_PATH`, `IMG_SIZE`, `RECOGNITION_THRESHOLD`, `FACE_DETECTION_CONFIDENCE`, `FACE_ROI_*`.

## face_db.py
- Class `FaceDB` lưu JSON theo schema cơ bản: `[{"id","name","embedding"}]`.
- Các hàm chính:
  - `load()` / `save()` quản lý file.
  - `add_person()` tạo id tăng dần và lưu embedding.
  - `update_person()` đổi tên/cập nhật embedding.
  - `delete_person()` xóa theo id.
  - `list_people()` trả về danh sách.
  - `get_all_embeddings()` trả dict `id -> (name, embedding)`.
- Dùng khóa `threading.RLock` để tránh race khi truy cập file.
- Dùng `DB_PATH` trong `config.py`.

## known_faces/face_db.json
- File dữ liệu người quen (JSON). Có thể chỉnh bằng GUI People Manager.

## __init__.py
- File đánh dấu package `face`.
