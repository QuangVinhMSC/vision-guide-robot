import sys
import cv2
import numpy as np
from PySide6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSlider, QFrame
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt

from contour_algorithm import ContourProcessor  # Import thuật toán

class ContourEditor(QWidget):
    def __init__(self, image_path):
        super().__init__()
        self.setWindowTitle("Contour Editor")
        self.resize(1000, 600)
        self.setMinimumSize(800, 400)

        # Sử dụng thuật toán từ file contour_algorithm.py
        self.processor = ContourProcessor(image_path)
        self.template_color = self.processor.template_color
        self.contours_template = self.processor.contours_template

        self.selected_contour = None
        self.contour_inner = None
        self.selected_point_idx = None
        self.contour_selected = False
        self.scale_factor = 0.8  

        self.label = QLabel(self)
        self.label.setScaledContents(True)

        # ====== Panel bên phải ======
        self.control_panel = QFrame(self)
        self.control_panel.setFrameShape(QFrame.StyledPanel)
        self.control_panel.setMinimumWidth(250)

        self.btn_reset = QPushButton("Reset Contour")
        self.btn_reset.clicked.connect(self.reset_selection)

        self.slider_scale = QSlider(Qt.Horizontal)
        self.slider_scale.setMinimum(-150)
        self.slider_scale.setMaximum(150)
        self.slider_scale.setValue(0)
        self.slider_scale.setTickInterval(10)
        self.slider_scale.setTickPosition(QSlider.TicksBelow)
        self.slider_scale.valueChanged.connect(self.update_scale)

        control_layout = QVBoxLayout()
        control_layout.addWidget(self.btn_reset)
        control_layout.addWidget(self.slider_scale)
        control_layout.addStretch()
        self.control_panel.setLayout(control_layout)

        # ====== Layout chính ======
        main_layout = QHBoxLayout()
        main_layout.addWidget(self.label, 2)
        main_layout.addWidget(self.control_panel, 1)

        self.setLayout(main_layout)
        self.update_display()

    def update_display(self):
        """ Cập nhật hiển thị hình ảnh """
        display = self.template_color.copy()
        cv2.drawContours(display, self.contours_template, -1, (255, 255, 255), 1)

        if self.selected_contour is not None:
            cv2.drawContours(display, [self.selected_contour], -1, (0, 0, 255), 2)
            for point in self.selected_contour:
                x, y = point[0]
                cv2.circle(display, (x, y), 5, (255, 0, 0), -1)

        if self.contour_inner is not None:
            cv2.drawContours(display, [self.contour_inner[:, :, 0:2]], -1, (0, 255, 0), 2)
            for point in self.contour_inner[:, :, 0:2]:
                x, y = point[0]
                cv2.circle(display, (x, y), 3, (0, 255, 255), -1)

        height, width, channel = display.shape
        bytes_per_line = 3 * width
        q_img = QImage(display.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
        pixmap = QPixmap.fromImage(q_img)
        self.label.setPixmap(pixmap)

    def reset_selection(self):
        """ Reset contour đã chọn """
        self.selected_contour = None
        self.contour_inner = None
        self.contour_selected = False
        self.update_display()

    def update_scale(self, value):
        """ Cập nhật scale factor khi kéo thanh trượt """
        self.scale_factor = value 
        print(f"Scale Factor: {self.scale_factor}")
        if self.selected_contour is not None:
            # self.contour_inner = self.processor.shrink_contour(self.selected_contour, self.scale_factor)
            self.contour_inner = self.processor.contour_offset(self.selected_contour,-self.scale_factor)
            self.contour_inner = cv2.approxPolyDP(self.contour_inner, epsilon=8, closed=True)
            self.contour_inner = np.concatenate((self.contour_inner, np.zeros((self.contour_inner.shape[0], 1, 1), dtype=self.contour_inner.dtype)), axis=2)
        self.update_display()

    def mousePressEvent(self, event):
        """ Xử lý sự kiện click chuột """
        if event.button() == Qt.LeftButton:
            label_width, label_height = self.label.width(), self.label.height()
            img_height, img_width = self.template_color.shape[:2]

            x = int(event.position().x() * (img_width / label_width))
            y = int(event.position().y() * (img_height / label_height))

            print(f"Clicked at (scaled): ({x}, {y})")

            if not self.contour_selected:
                for cnt in self.contours_template:
                    if cv2.pointPolygonTest(cnt, (x, y), False) >= 0:
                        self.selected_contour = cnt
                        # self.contour_inner = self.processor.shrink_contour(cnt, self.scale_factor)
                        self.contour_inner = self.processor.contour_offset(self.selected_contour,- self.scale_factor)
                        self.contour_inner = cv2.approxPolyDP(self.contour_inner, epsilon=8, closed=True)
                        self.contour_inner = np.concatenate((self.contour_inner, np.zeros((self.contour_inner.shape[0], 1, 1), dtype=self.contour_inner.dtype)), axis=2)
                        self.contour_selected = True
                        print("Contour đã chọn!")
                        break

            self.update_display()
if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = ContourEditor("/home/vinhdq/vision guide robot/image/captured_image.png")
    editor.show()
    sys.exit(app.exec())
