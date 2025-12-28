from __future__ import annotations

from PySide6 import QtCore, QtWidgets

from app.gui.qt_utils import bgr_to_qpixmap
from app.services.overlay import draw_overlay


class RecognitionWorker(QtCore.QObject):
    finished = QtCore.Signal(dict)

    def __init__(self, controller, frame):
        super().__init__()
        self.controller = controller
        self.frame = frame

    @QtCore.Slot()
    def run(self) -> None:
        result = self.controller.recognize_frame(self.frame, log_event=False, send_telegram=False, allow_unlock=False)
        self.finished.emit(result)


class TabLive(QtWidgets.QWidget):
    def __init__(self, controller, settings, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.settings = settings
        self.last_frame = None
        self.frame_count = 0
        self.worker_thread = None
        self.last_result = None

        self.video_label = QtWidgets.QLabel()
        self.video_label.setMinimumSize(640, 480)
        self.video_label.setScaledContents(True)

        self.status_labels = {
            "id": QtWidgets.QLabel("-"),
            "name": QtWidgets.QLabel("-"),
            "group": QtWidgets.QLabel("-"),
            "note": QtWidgets.QLabel("-"),
            "score": QtWidgets.QLabel("-"),
            "is_real": QtWidgets.QLabel("-"),
        }

        form_layout = QtWidgets.QFormLayout()
        form_layout.addRow("ID", self.status_labels["id"])
        form_layout.addRow("Name", self.status_labels["name"])
        form_layout.addRow("Group", self.status_labels["group"])
        form_layout.addRow("Note", self.status_labels["note"])
        form_layout.addRow("Score", self.status_labels["score"])
        form_layout.addRow("Is real", self.status_labels["is_real"])

        self.btn_capture = QtWidgets.QPushButton("Capture & Recognize")
        self.btn_add = QtWidgets.QPushButton("Add Person from Camera")
        self.btn_unlock = QtWidgets.QPushButton("Unlock Door")
        self.btn_unlock.setEnabled(False)

        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.addWidget(self.btn_capture)
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_unlock)

        side_layout = QtWidgets.QVBoxLayout()
        side_layout.addLayout(form_layout)
        side_layout.addLayout(btn_layout)
        side_layout.addStretch(1)

        main_layout = QtWidgets.QHBoxLayout(self)
        main_layout.addWidget(self.video_label, 2)
        main_layout.addLayout(side_layout, 1)

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self._update_frame)
        self.timer.start(33)

        self.btn_capture.clicked.connect(self._on_capture)
        self.btn_add.clicked.connect(self._on_add_person)
        self.btn_unlock.clicked.connect(self._on_manual_unlock)

    def _update_frame(self) -> None:
        frame = self.controller.capture_frame()
        if frame is None:
            return
        self.last_frame = frame
        display_frame = frame.copy()
        draw_overlay(display_frame, self.last_result)
        pixmap = bgr_to_qpixmap(display_frame)
        self.video_label.setPixmap(pixmap)

        self.frame_count += 1
        if (
            self.settings.recognition_every_n_frames > 0
            and self.frame_count % self.settings.recognition_every_n_frames == 0
        ):
            self._start_worker(self.last_frame)

    def _start_worker(self, frame) -> None:
        if self.worker_thread and self.worker_thread.isRunning():
            return
        worker = RecognitionWorker(self.controller, frame.copy())
        thread = QtCore.QThread(self)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(self._on_result)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        self.worker_thread = thread
        thread.start()

    def _on_result(self, result: dict) -> None:
        self.last_result = result
        self._update_status(result)

    def _update_status(self, result: dict) -> None:
        self.status_labels["id"].setText(str(result.get("person_id") or "-"))
        self.status_labels["name"].setText(str(result.get("person_name") or "-"))
        self.status_labels["group"].setText(str(result.get("group") or "-"))
        self.status_labels["note"].setText(str(result.get("note") or "-"))
        score = result.get("score")
        self.status_labels["score"].setText("-" if score is None else f"{score:.3f}")
        self.status_labels["is_real"].setText(str(result.get("is_real")))

        allow_manual = False
        if result:
            if not result.get("known"):
                allow_manual = True
            elif result.get("group") in self.settings.auto_unlock_groups:
                allow_manual = True
        self.btn_unlock.setEnabled(allow_manual)

    def _on_capture(self) -> None:
        if self.last_frame is None:
            return
        self._start_worker(self.last_frame)

    def _on_add_person(self) -> None:
        from app.gui.dialogs import AddEditPersonDialog

        embedding, face_crop = self.controller.capture_face_embedding()
        if embedding is None:
            QtWidgets.QMessageBox.warning(self, "No face", "No face detected from camera.")
            return
        dialog = AddEditPersonDialog(self.controller, embedding=embedding, face_crop=face_crop, parent=self)
        if dialog.exec() == QtWidgets.QDialog.Accepted:
            data = dialog.result_data
            if data:
                self.controller.face_db.add_person(
                    data["name"], data["group"], data["note"], data["embedding"]
                )

    def _on_manual_unlock(self) -> None:
        if self.last_result is None:
            return
        self.controller.manual_unlock(self.last_result)

    def update_from_event(self, result: dict) -> None:
        self.last_result = result
        self._update_status(result)
