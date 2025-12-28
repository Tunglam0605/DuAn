# Smart Doorbell Pro

Smart doorbell reference implementation for Raspberry Pi 5 with local GUI, face recognition, liveness checks, GPIO triggers, and Telegram alerts.

## Folder structure

```
smart_doorbell_pro/
  app/
    main.py
    controller.py
    core/
      logger.py
      env.py
      settings.py
    models/
      registry.py
    services/
      camera.py
      triggers.py
      face_db.py
      face_recognizer.py
      liveness_checker.py
      door_lock.py
      telegram_notifier.py
      overlay.py
      event_store.py
    gui/
      app_window.py
      tab_live.py
      tab_people.py
      dialogs.py
      qt_utils.py
    data/
      face_db.json
  assets/
    models/
  logs/
    events.jsonl
  scripts/
    self_check.py
  run.py
  requirements.txt
  .env.example
  README.md
```

## Models

Copy required models into `assets/models/` with exact filenames:

Required:
- `MobileNet-v2_float.tflite` (key: `embedding_mobilenetv2`)
- `modelrgb.onnx` (key: `liveness_modelrgb`)

Optional:
- `MobileFaceNet.tflite`
- `FaceAntiSpoofing.tflite`
- `genderage.onnx`
- `2d106det.onnx`
- `glintr100.onnx`

The registry lives in `app/models/registry.py` and all services resolve models by key.

## Environment

Copy `.env.example` to `.env` and fill in values:

```
copy .env.example .env
```

At minimum, set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` if you want Telegram alerts.

## Run

GUI mode (default):

```
python run.py
```

Module mode:

```
python -m app.main
```

Headless (GPIO loop only):

```
python run.py --headless
```

Note: Không chạy file module lẻ. Hãy chạy run.py hoặc python -m app.main.

CLI options:
- `--headless`: no GUI, only GPIO loop
- `--no-telegram`: disable Telegram notifications
- `--unlock`: enable relay unlock
- `--log-level INFO|DEBUG`

## Windows PowerShell setup

From project root:

```
py -3.9 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -r requirements.txt
python -m compileall -q .
python run.py
```

If `Activate.ps1` is blocked:

```
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

If `python`/`python3` opens Microsoft Store, disable App Execution Aliases for Python in Windows Settings.

## Self-check

```
python scripts/self_check.py
```

## Troubleshooting

- Camera: if Picamera2 is not available, the app falls back to OpenCV VideoCapture.
- GPIO permissions: ensure the user can access GPIO (try running with sudo or set up udev rules).
- Windows GPIO: gpiozero is disabled (mock mode) when GPIO is not available.
- Models missing: check `assets/models/` filenames match the registry keys.
- Telegram: confirm bot token and chat ID are correct; the bot must have access to the chat.
