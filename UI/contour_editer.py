import sys
import cv2
import numpy as np
from PySide6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSlider, QFrame, QSpinBox
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt

from contour_algorithm import ContourProcessor  # Import thuật toán

class ContourEditor(QWidget):
    def __init__(self, image_path):
        super().__init__()
        self.setWindowTitle("Contour Editor")
        self.resize(1000, 600)
        self.setMinimumSize(800, 400)

        self.processor = ContourProcessor(image_path)
        self.template_color = self.processor.template_color
        self.contours_template = self.processor.contours_template

        self.selected_contour = None
        self.contour_inner = None
        self.selected_point_idx = None
        self.contour_selected = False
        self.scale_factor = 0.8  
        self.final_offset = []

        self.label = QLabel(self)
        self.label.setScaledContents(True)

        self.control_panel = QFrame(self)
        self.control_panel.setFrameShape(QFrame.StyledPanel)
        self.control_panel.setMinimumWidth(250)

        self.btn_reset = QPushButton("Reset Contour")
        self.btn_reset.clicked.connect(self.reset_selection)

        self.btn_save = QPushButton("Save Points")
        self.btn_save.clicked.connect(self.save_points)

        self.btn_clear = QPushButton("Clear Saved")
        self.btn_clear.clicked.connect(self.clear_final_offset)

        self.slider_scale = QSlider(Qt.Horizontal)
        self.slider_scale.setMinimum(-150)
        self.slider_scale.setMaximum(150)
        self.slider_scale.setValue(0)
        self.slider_scale.setTickInterval(10)
        self.slider_scale.setTickPosition(QSlider.TicksBelow)
        self.slider_scale.valueChanged.connect(self.update_scale)

        self.n_input = QSpinBox()
        self.n_input.setMinimum(0)
        self.m_input = QSpinBox()
        self.m_input.setMinimum(0)

        control_layout = QVBoxLayout()
        control_layout.addWidget(self.btn_reset)
        control_layout.addWidget(self.slider_scale)
        control_layout.addWidget(self.n_input)
        control_layout.addWidget(self.m_input)
        control_layout.addWidget(self.btn_save)
        control_layout.addWidget(self.btn_clear)
        control_layout.addStretch()
        self.control_panel.setLayout(control_layout)

        main_layout = QHBoxLayout()
        main_layout.addWidget(self.label, 2)
        main_layout.addWidget(self.control_panel, 1)

        self.setLayout(main_layout)
        self.update_display()

    def update_display(self):
        display = self.template_color.copy()
        cv2.drawContours(display, self.contours_template, -1, (255, 255, 255), 1)

        if self.contour_inner is not None:
            cv2.drawContours(display, [self.contour_inner[:, :, 0:2]], -1, (0, 0, 255), 2)
            for i, point in enumerate(self.contour_inner[:, :, 0:2]):
                x, y = point[0]
                cv2.circle(display, (x, y), 5, (255, 0, 0), -1)
                cv2.putText(display, str(i), (x + 5, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

        if self.final_offset:
            for i, point in enumerate(self.final_offset):
                x, y = point
                cv2.circle(display, (x, y), 3, (0, 255, 0), -1)
                cv2.putText(display, str(i), (x + 5, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)
            if len(self.final_offset) > 1:
                cv2.polylines(display, [np.array(self.final_offset)], isClosed=False, color=(0, 255, 0), thickness=2)

        height, width, channel = display.shape
        bytes_per_line = 3 * width
        q_img = QImage(display.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
        pixmap = QPixmap.fromImage(q_img)
        self.label.setPixmap(pixmap)

    def reset_selection(self):
        self.selected_contour = None
        self.contour_inner = None
        self.contour_selected = False
        self.update_display()

    def update_scale(self, value):
        self.scale_factor = value 
        if self.selected_contour is not None:
            self.contour_inner = self.processor.contour_offset(self.selected_contour, -self.scale_factor)
            self.contour_inner = cv2.approxPolyDP(self.contour_inner, epsilon=1, closed=True)
            self.contour_inner = np.concatenate((self.contour_inner, np.zeros((self.contour_inner.shape[0], 1, 1), dtype=self.contour_inner.dtype)), axis=2)
        self.update_display()

    def save_points(self):
        if self.contour_inner is not None:
            n, m = self.n_input.value(), self.m_input.value()
            if 0 <= n < len(self.contour_inner) and 0 <= m < len(self.contour_inner):
                selected_points = self.contour_inner[n:m+1, 0, :2].tolist()
                self.final_offset.extend(selected_points)
                self.update_display()

    def clear_final_offset(self):
        self.final_offset = []
        self.update_display()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            label_width, label_height = self.label.width(), self.label.height()
            img_height, img_width = self.template_color.shape[:2]

            x = int(event.position().x() * (img_width / label_width))
            y = int(event.position().y() * (img_height / label_height))

            if not self.contour_selected:
                for cnt in self.contours_template:
                    if cv2.pointPolygonTest(cnt, (x, y), False) >= 0:
                        self.selected_contour = cnt
                        self.contour_inner = self.processor.contour_offset(self.selected_contour, -self.scale_factor)
                        self.contour_inner = cv2.approxPolyDP(self.contour_inner, epsilon=1, closed=True)
                        self.contour_inner = np.concatenate((self.contour_inner, np.zeros((self.contour_inner.shape[0], 1, 1), dtype=self.contour_inner.dtype)), axis=2)
                        self.contour_selected = True
                        break
            self.update_display()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = ContourEditor("/home/vinhdq/vision guide robot/image/captured_image.png")
    editor.show()
    sys.exit(app.exec())
