from PySide6 import QtWidgets


class PersonDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Person")

        self.name_input = QtWidgets.QLineEdit()

        self.source_live_radio = QtWidgets.QRadioButton("Use latest face from Live tab")
        self.source_file_radio = QtWidgets.QRadioButton("Use image file")
        self.source_group = QtWidgets.QButtonGroup(self)
        self.source_group.addButton(self.source_live_radio)
        self.source_group.addButton(self.source_file_radio)
        self.source_live_radio.setChecked(True)

        self.file_path_input = QtWidgets.QLineEdit()
        self.file_path_input.setReadOnly(True)
        self.file_browse_btn = QtWidgets.QPushButton("Browse...")
        self.file_browse_btn.clicked.connect(self._browse_file)

        self.source_live_radio.toggled.connect(self._sync_source_state)
        self.source_file_radio.toggled.connect(self._sync_source_state)

        form = QtWidgets.QFormLayout()
        form.addRow("Name*", self.name_input)

        source_box = QtWidgets.QVBoxLayout()
        source_box.addWidget(self.source_live_radio)
        source_box.addWidget(self.source_file_radio)

        file_row = QtWidgets.QHBoxLayout()
        file_row.addWidget(self.file_path_input)
        file_row.addWidget(self.file_browse_btn)

        source_widget = QtWidgets.QWidget()
        source_layout = QtWidgets.QVBoxLayout(source_widget)
        source_layout.setContentsMargins(0, 0, 0, 0)
        source_layout.addLayout(source_box)
        source_layout.addLayout(file_row)

        form.addRow("Source", source_widget)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

        self._sync_source_state()

    def _sync_source_state(self):
        use_file = self.source_file_radio.isChecked()
        self.file_path_input.setEnabled(use_file)
        self.file_browse_btn.setEnabled(use_file)

    def _browse_file(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Select image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp);;All files (*.*)",
        )
        if path:
            self.file_path_input.setText(path)
            self.source_file_radio.setChecked(True)

    def set_source_mode(self, mode):
        if mode == "file":
            self.source_file_radio.setChecked(True)
        else:
            self.source_live_radio.setChecked(True)

    def get_data(self):
        source = "file" if self.source_file_radio.isChecked() else "live"
        return {
            "name": self.name_input.text().strip(),
            "source": source,
            "file_path": self.file_path_input.text().strip(),
        }


class EditPersonDialog(QtWidgets.QDialog):
    def __init__(self, current_name="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Person")

        self.name_input = QtWidgets.QLineEdit()
        self.name_input.setText(current_name or "")

        self.update_face_checkbox = QtWidgets.QCheckBox("Update face embedding")

        self.source_live_radio = QtWidgets.QRadioButton("Use latest face from Live tab")
        self.source_file_radio = QtWidgets.QRadioButton("Use image file")
        self.source_group = QtWidgets.QButtonGroup(self)
        self.source_group.addButton(self.source_live_radio)
        self.source_group.addButton(self.source_file_radio)
        self.source_live_radio.setChecked(True)

        self.file_path_input = QtWidgets.QLineEdit()
        self.file_path_input.setReadOnly(True)
        self.file_browse_btn = QtWidgets.QPushButton("Browse...")
        self.file_browse_btn.clicked.connect(self._browse_file)

        self.update_face_checkbox.toggled.connect(self._sync_source_state)
        self.source_live_radio.toggled.connect(self._sync_source_state)
        self.source_file_radio.toggled.connect(self._sync_source_state)

        form = QtWidgets.QFormLayout()
        form.addRow("Name*", self.name_input)

        source_box = QtWidgets.QVBoxLayout()
        source_box.addWidget(self.update_face_checkbox)
        source_box.addWidget(self.source_live_radio)
        source_box.addWidget(self.source_file_radio)

        file_row = QtWidgets.QHBoxLayout()
        file_row.addWidget(self.file_path_input)
        file_row.addWidget(self.file_browse_btn)

        source_widget = QtWidgets.QWidget()
        source_layout = QtWidgets.QVBoxLayout(source_widget)
        source_layout.setContentsMargins(0, 0, 0, 0)
        source_layout.addLayout(source_box)
        source_layout.addLayout(file_row)

        form.addRow("Face", source_widget)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

        self._sync_source_state()

    def _sync_source_state(self):
        enabled = self.update_face_checkbox.isChecked()
        self.source_live_radio.setEnabled(enabled)
        self.source_file_radio.setEnabled(enabled)
        use_file = enabled and self.source_file_radio.isChecked()
        self.file_path_input.setEnabled(use_file)
        self.file_browse_btn.setEnabled(use_file)

    def _browse_file(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Select image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp);;All files (*.*)",
        )
        if path:
            self.file_path_input.setText(path)
            self.source_file_radio.setChecked(True)

    def get_data(self):
        source = "file" if self.source_file_radio.isChecked() else "live"
        return {
            "name": self.name_input.text().strip(),
            "update_embedding": self.update_face_checkbox.isChecked(),
            "source": source,
            "file_path": self.file_path_input.text().strip(),
        }
