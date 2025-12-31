# Smart Doorbell — Hệ thống chuông cửa thông minh (Raspberry Pi 5)

Dự án chuông cửa thông minh tích hợp **nhận diện khuôn mặt**, **GUI điều khiển**, **API cho mobile app**, **Cloudflare Tunnel**, cùng phần cứng **servo/LED/LCD/I2C**. Mục tiêu: chạy ổn định, dễ triển khai, sẵn sàng thương mại hóa.

---

## Điểm nổi bật
- **GUI chuyên nghiệp**: Live view, nhận diện, điều khiển cửa, People Manager, About (hiển thị tunnel URL).
- **Nhận diện + liveness**: nhận diện người quen/khách lạ, ROI elip định hướng camera.
- **API chuẩn mobile**: `/health`, `/events`, `/unlock`, `/lock`, `/media/...`.
- **Event + ảnh**: tự lưu ảnh sự kiện + log JSONL rõ ràng.
- **Cloudflare Tunnel tự động**: một lệnh là có URL public cho app.
- **Mock mode**: chạy demo trên PC/webcam, giả lập GPIO/door.

---

## Quickstart — 1 lệnh là chạy

### Linux / Pi / macOS
```bash
./scripts/run.sh
```
Mock mode (không cần GPIO/servo, dùng webcam):
```bash
./scripts/run.sh --mock
```

### Windows (PowerShell)
```powershell
.\scripts\run.ps1
```
Mock mode:
```powershell
.\scripts\run.ps1 -Mock
```

---

## Git LFS (bắt buộc cho model + mp3)

Repo sử dụng Git LFS để lưu **model** và **mp3**:
```bash
git lfs install
git lfs pull
```

Nếu thiếu LFS, model/âm thanh sẽ không được tải đầy đủ.

---

## Các chế độ chạy

| Chế độ | Lệnh | Mô tả |
| --- | --- | --- |
| Full system | `./.venv/bin/python run_all.py` | GUI + API + Tunnel |
| GUI only | `./.venv/bin/python run_gui.py` | Chỉ GUI |
| Legacy | `./.venv/bin/python main.py` | Luồng cũ (terminal / phím tắt) |

---

## Cài đặt thủ công (tuỳ chọn)

### 1) Tạo venv
```bash
python -m venv .venv
source .venv/bin/activate
```

### 2) Cài dependencies
- **Chung:**
```bash
pip install -r requirements.txt
```
- **Pi (GPIO + PiCamera):**
```bash
pip install -r requirements-pi.txt
```
- **Desktop (mock / dev):**
```bash
pip install -r requirements-desktop.txt
```

### 3) Chuẩn bị model
Đặt file model vào `models/`:
- `MobileNet-v2_float.tflite`
- `modelrgb.onnx`

---

## Mock mode
- Dùng webcam OpenCV thay cho PiCamera.
- Door/LED/servo giả lập (không cần GPIO).
- Bật mock:
```bash
SMART_DOORBELL_MODE=mock ./.venv/bin/python run_all.py
```
Hoặc dùng `./scripts/run.sh --mock`.

---

## Chính sách nhận diện & event (hiện tại)
- **KNOWN**: tự mở cửa + tạo event (không tạo lặp lại cho cùng một người cho đến khi cửa đóng).
- **UNKNOWN**: không tự mở cửa; **chỉ tạo event khi bấm chuông**.
- **Bấm chuông**: luôn tạo event (KNOWN/UNKNOWN/RING tùy trạng thái face).
- **Nếu People DB trống**: GUI buộc chế độ **Require known** để tránh mở cửa nhầm.

---

## API (FastAPI)

### Base URL
- Local: `http://<API_HOST>:<API_PORT>`
- Public: `https://<your>.trycloudflare.com`

### GET `/health`
```json
{ "ok": true }
```

### GET `/events`
Trả về **danh sách 1 event mới nhất** (0 hoặc 1 phần tử).

```json
[
  {
    "eventId": "evt_abcdef01",
    "timestamp": "2025-12-31 06:10:34",
    "type": "KNOWN",
    "imageUrl": "https://<public>/media/evt_abcdef01_20251231_061034.jpg",
    "personName": "Nguyen Van A"
  }
]
```

### POST `/unlock`
```json
{ "eventId": "evt_abcdef01", "source": "app" }
```

### POST `/lock`
```json
{ "eventId": "evt_abcdef01", "source": "app" }
```

### GET `/media/{filename}`
Trả ảnh sự kiện trong thư mục `media/`.

---

## Cấu hình nhanh (quan trọng nhất)
Tất cả nằm trong `config.py`, có thể override bằng biến môi trường.

### API / Tunnel
- `API_HOST`, `API_PORT`
- `PUBLIC_BASE_URL`
- `DOORBELL_TUNNEL_ENABLE` (0/1)
- `DOORBELL_TUNNEL_CMD` (mặc định: `cloudflared tunnel --url {url}`)

### GUI / Access
- `DOORBELL_ABOUT_ID` / `DOORBELL_ABOUT_PASSWORD` (tab About + People)

### Event
- `DOORBELL_EVENT_CAPTURE_ENABLED`
- `EVENT_CAPTURE_INTERVAL_SEC`

### Phần cứng
- **Servo**: `SERVO_PIN`, `SERVO_OPEN_ANGLE`, `SERVO_CLOSE_ANGLE`...
- **LED**: `LED_PIN`, `LED_ACTIVE_HIGH`
- **Chuông**: `DOORBELL_RING_BUTTON_PIN`, `DOORBELL_RING_SOUND_MP3`
- **LCD I2C**: `DOORBELL_LCD_I2C_BUS`, `DOORBELL_LCD_I2C_ADDRESS`

### Nhận diện & ROI
- `RECOGNITION_THRESHOLD`
- `FACE_ROI_RELATIVE_W`, `FACE_ROI_RELATIVE_H`, `FACE_ROI_ROTATE_DEG`
- `FACE_ROI_MIN_COVERAGE`, `FACE_ROI_CENTER_TOLERANCE_X`

---

## Cấu trúc thư mục
```
smart_doorbell/
├── camera/                 # Camera manager
├── face/                   # Face detection/recognition + DB
├── gui/                    # PySide6 GUI (Live, People, About)
├── server/                 # FastAPI + event store + control
├── utils/                  # LCD I2C, helper utilities
├── scripts/                # 1-lệnh chạy (run.sh, run.ps1)
├── requirements.txt        # Common deps
├── requirements-pi.txt     # Pi deps
├── requirements-desktop.txt# Desktop deps
├── media/                  # Ảnh sự kiện
├── logs/                   # events.jsonl
├── sounds/                 # MP3 âm thanh
├── models/                 # Model nhận diện / liveness
├── run_all.py              # GUI + API + Tunnel
├── run_gui.py              # GUI only
└── main.py                 # Legacy mode
```

---

## Troubleshooting nhanh
- **GUI không lên**: kiểm tra `PySide6` và chạy trong venv.
- **API lỗi import**: kiểm tra `fastapi`, `uvicorn`, `typing_extensions`.
- **Không có tunnel URL**: cài `cloudflared` hoặc `DOORBELL_TUNNEL_ENABLE=0`.
- **Không thấy ảnh event**: kiểm tra `PUBLIC_BASE_URL` và thư mục `media/`.

---

## Lưu ý bảo mật
- **Không commit token/credentials** (Telegram, tunnel, v.v.).
- Dùng biến môi trường trong production.

---

## Tài liệu con
- `camera/README.md`
- `face/README.md`
- `gui/README.md`
- `server/README.md`
- `utils/README.md`

---

Nếu cần build demo hoặc checklist triển khai production, cứ nói mình.
