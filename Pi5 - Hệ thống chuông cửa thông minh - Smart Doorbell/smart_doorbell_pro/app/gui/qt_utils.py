from __future__ import annotations

import cv2
from PySide6 import QtGui


def bgr_to_qpixmap(frame_bgr) -> QtGui.QPixmap:
    if frame_bgr is None:
        return QtGui.QPixmap()
    rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    height, width, channels = rgb.shape
    bytes_per_line = channels * width
    image = QtGui.QImage(rgb.data, width, height, bytes_per_line, QtGui.QImage.Format_RGB888)
    return QtGui.QPixmap.fromImage(image)