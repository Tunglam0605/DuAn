from __future__ import annotations

from typing import Optional

from PySide6 import QtCore, QtWidgets

from app.gui.qt_utils import bgr_to_qpixmap


class AddEditPersonDialog(QtWidgets.QDialog):
    def __init__(self, controller, person: Optional[dict] = None, embedding=None, face_crop=None, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.person = person
        self.embedding = embedding
        self.face_crop = face_crop
        self.is_edit = person is not None
        self.result_data = None

        self.setWindowTitle("Edit person" if self.is_edit else "Add person")

        self.name_input = QtWidgets.QLineEdit()
        self.group_combo = QtWidgets.QComboBox()
        self.group_combo.addItems(["owner", "family", "friend"])
        self.note_input = QtWidgets.QTextEdit()
        self.embedding_label = QtWidgets.QLabel()
        self.preview_label = QtWidgets.QLabel()
        self.preview_label.setFixedSize(160, 160)
        self.preview_label.setScaledContents(True)

        self.btn_from_camera = QtWidgets.QPushButton("From Camera")
        self.btn_from_file = QtWidgets.QPushButton("From File")

        self.btn_from_camera.clicked.connect(self._on_from_camera)
        self.btn_from_file.clicked.connect(self._on_from_file)

        form_layout = QtWidgets.QFormLayout()
        form_layout.addRow("Name*", self.name_input)
        form_layout.addRow("Group", self.group_combo)
        form_layout.addRow("Note", self.note_input)

        embed_layout = QtWidgets.QHBoxLayout()
        embed_layout.addWidget(self.btn_from_camera)
        embed_layout.addWidget(self.btn_from_file)

        embed_block = QtWidgets.QVBoxLayout()
        embed_block.addLayout(embed_layout)
        embed_block.addWidget(self.embedding_label)

        top_layout = QtWidgets.QHBoxLayout()
        top_layout.addLayout(form_layout)
        top_layout.addWidget(self.preview_label)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(top_layout)
        layout.addLayout(embed_block)

        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        if self.is_edit:
            self.name_input.setText(person.get("name", ""))
            group = person.get("group", "friend")
            index = self.group_combo.findText(group)
            if index >= 0:
                self.group_combo.setCurrentIndex(index)
            self.note_input.setPlainText(person.get("note", ""))

        self._update_embedding_label()
        self._update_preview()

    def _update_embedding_label(self) -> None:
        if self.embedding is None:
            self.embedding_label.setText("Embedding: none")
        else:
            self.embedding_label.setText("Embedding: ready")

    def _update_preview(self) -> None:
        if self.face_crop is None:
            self.preview_label.clear()
            return
        pixmap = bgr_to_qpixmap(self.face_crop)
        self.preview_label.setPixmap(pixmap)

    def _on_from_camera(self) -> None:
        embedding = self.controller.get_last_embedding()
        face_crop = self.controller.get_last_face_crop()
        if embedding is None or face_crop is None:
            embedding, face_crop = self.controller.capture_face_embedding()
            if embedding is None:
                QtWidgets.QMessageBox.warning(self, "No face", "No face detected from camera.")
                return
        self.embedding = embedding
        self.face_crop = face_crop
        self._update_embedding_label()
        self._update_preview()

    def _on_from_file(self) -> None:
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select image")
        if not file_path:
            return
        embedding, face_crop = self.controller.embedding_from_file(file_path)
        if embedding is None:
            QtWidgets.QMessageBox.warning(self, "No face", "No face detected in image.")
            return
        self.embedding = embedding
        self.face_crop = face_crop
        self._update_embedding_label()
        self._update_preview()

    def _on_accept(self) -> None:
        name = self.name_input.text().strip()
        group = self.group_combo.currentText().strip()
        note = self.note_input.toPlainText().strip()
        if not name:
            QtWidgets.QMessageBox.warning(self, "Missing name", "Name is required.")
            return
        if not self.is_edit and self.embedding is None:
            QtWidgets.QMessageBox.warning(self, "Missing embedding", "Please select a face from camera or file.")
            return
        self.result_data = {
            "name": name,
            "group": group,
            "note": note,
            "embedding": self.embedding,
        }
        self.accept()


class DoorbellPopup(QtWidgets.QDialog):
    def __init__(self, controller, result: dict, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.result = result
        self.setWindowTitle("Doorbell")

        image_label = QtWidgets.QLabel()
        image_label.setFixedSize(320, 240)
        image_label.setScaledContents(True)
        if result.get("frame") is not None:
            pixmap = bgr_to_qpixmap(result["frame"])
            image_label.setPixmap(pixmap)

        info_lines = [
            f"ID: {result.get('person_id') or '-'}",
            f"Name: {result.get('person_name') or '-'}",
            f"Group: {result.get('group') or '-'}",
            f"Note: {result.get('note') or '-'}",
            f"Score: {result.get('score') if result.get('score') is not None else '-'}",
            f"Is real: {result.get('is_real')}",
        ]
        info_label = QtWidgets.QLabel("\n".join(info_lines))

        self.unlock_button = QtWidgets.QPushButton("Unlock Door")
        self.unlock_button.clicked.connect(self._on_unlock)
        self.unlock_button.setVisible(not result.get("known", False))

        close_button = QtWidgets.QPushButton("Close")
        close_button.clicked.connect(self.accept)

        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.addWidget(self.unlock_button)
        btn_layout.addWidget(close_button)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(image_label)
        layout.addWidget(info_label)
        layout.addLayout(btn_layout)

    def _on_unlock(self) -> None:
        self.controller.manual_unlock(self.result)
        self.accept()
