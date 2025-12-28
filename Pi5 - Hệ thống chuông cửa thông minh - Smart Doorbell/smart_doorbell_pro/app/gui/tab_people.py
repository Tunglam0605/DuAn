from __future__ import annotations

from PySide6 import QtCore, QtWidgets

from app.gui.dialogs import AddEditPersonDialog


class TabPeople(QtWidgets.QWidget):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.face_db = controller.face_db

        self.search_input = QtWidgets.QLineEdit()
        self.search_input.setPlaceholderText("Search by name")
        self.group_filter = QtWidgets.QComboBox()
        self.group_filter.addItems(["all", "owner", "family", "friend"])

        self.table = QtWidgets.QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Group", "Note", "Created", "Updated"])
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)

        self.btn_add = QtWidgets.QPushButton("Add")
        self.btn_edit = QtWidgets.QPushButton("Edit")
        self.btn_delete = QtWidgets.QPushButton("Delete")
        self.btn_refresh = QtWidgets.QPushButton("Refresh")

        top_layout = QtWidgets.QHBoxLayout()
        top_layout.addWidget(self.search_input)
        top_layout.addWidget(self.group_filter)

        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addWidget(self.btn_refresh)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(top_layout)
        layout.addWidget(self.table)
        layout.addLayout(btn_layout)

        self.search_input.textChanged.connect(self.refresh_table)
        self.group_filter.currentIndexChanged.connect(self.refresh_table)
        self.btn_refresh.clicked.connect(self.refresh_table)
        self.btn_add.clicked.connect(self._on_add)
        self.btn_edit.clicked.connect(self._on_edit)
        self.btn_delete.clicked.connect(self._on_delete)

        self.refresh_table()

    def _filtered_people(self):
        people = self.face_db.list_people()
        keyword = self.search_input.text().strip().lower()
        group = self.group_filter.currentText()
        filtered = []
        for person in people:
            if keyword and keyword not in person.get("name", "").lower():
                continue
            if group != "all" and person.get("group") != group:
                continue
            filtered.append(person)
        return filtered

    def refresh_table(self) -> None:
        people = self._filtered_people()
        self.table.setRowCount(len(people))
        for row, person in enumerate(people):
            self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(str(person.get("id", ""))))
            self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(person.get("name", "")))
            self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(person.get("group", "")))
            self.table.setItem(row, 3, QtWidgets.QTableWidgetItem(person.get("note", "")))
            self.table.setItem(row, 4, QtWidgets.QTableWidgetItem(person.get("created_at", "")))
            self.table.setItem(row, 5, QtWidgets.QTableWidgetItem(person.get("updated_at", "")))

    def _selected_id(self):
        items = self.table.selectedItems()
        if not items:
            return None
        return items[0].text()

    def _on_add(self) -> None:
        dialog = AddEditPersonDialog(self.controller, parent=self)
        if dialog.exec() == QtWidgets.QDialog.Accepted:
            data = dialog.result_data
            if data:
                self.face_db.add_person(data["name"], data["group"], data["note"], data["embedding"])
            self.refresh_table()

    def _on_edit(self) -> None:
        person_id = self._selected_id()
        if not person_id:
            QtWidgets.QMessageBox.warning(self, "No selection", "Select a person to edit.")
            return
        person = self.face_db.get_person(person_id)
        if not person:
            return
        dialog = AddEditPersonDialog(self.controller, person=person, parent=self)
        if dialog.exec() == QtWidgets.QDialog.Accepted:
            data = dialog.result_data
            if data:
                self.face_db.update_person(
                    person_id,
                    name=data["name"],
                    group=data["group"],
                    note=data["note"],
                    embedding=data.get("embedding"),
                )
            self.refresh_table()

    def _on_delete(self) -> None:
        person_id = self._selected_id()
        if not person_id:
            QtWidgets.QMessageBox.warning(self, "No selection", "Select a person to delete.")
            return
        confirm = QtWidgets.QMessageBox.question(
            self,
            "Confirm delete",
            f"Delete person {person_id}?",
        )
        if confirm == QtWidgets.QMessageBox.Yes:
            self.face_db.delete_person(person_id)
            self.refresh_table()