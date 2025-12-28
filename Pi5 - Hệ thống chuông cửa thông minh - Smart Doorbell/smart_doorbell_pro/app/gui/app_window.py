from __future__ import annotations

from PySide6 import QtCore, QtWidgets

from app.gui.dialogs import DoorbellPopup
from app.gui.tab_live import TabLive
from app.gui.tab_people import TabPeople


class EventBridge(QtCore.QObject):
    event = QtCore.Signal(dict)


class AppWindow(QtWidgets.QMainWindow):
    def __init__(self, controller, settings):
        super().__init__()
        self.controller = controller
        self.settings = settings

        self.setWindowTitle("Smart Doorbell Pro")

        self.tabs = QtWidgets.QTabWidget()
        self.tab_live = TabLive(controller, settings)
        self.tab_people = TabPeople(controller)
        self.tabs.addTab(self.tab_live, "Live")
        self.tabs.addTab(self.tab_people, "People")
        self.setCentralWidget(self.tabs)

        self.bridge = EventBridge()
        self.bridge.event.connect(self._on_event)
        self.controller.set_event_callback(self.bridge.event.emit)
        self.controller.start_hardware()

    def _on_event(self, result: dict) -> None:
        self.tab_live.update_from_event(result)
        popup = DoorbellPopup(self.controller, result, parent=self)
        popup.exec()


def run_gui(controller, settings) -> None:
    app = QtWidgets.QApplication([])
    window = AppWindow(controller, settings)
    window.resize(1024, 600)
    window.show()
    app.exec()