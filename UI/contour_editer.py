import sys
import cv2
import numpy as np
from PySide6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSlider, QFrame, QSpinBox, QMainWindow
from PySide6.QtGui import QPixmap, QImage, QPainter, QPen, QColor
from PySide6.QtCore import Qt

from contour_algorithm import ContourProcessor  # Import thuật toán

class ContourEditor(QWidget):
    def __init__(self, image_path):
        super().__init__()
        # Algorithm
        self.processor = ContourProcessor(image_path)
        self.template_color = self.processor.template_color
        self.contours_template = self.processor.contours_template

        # Variables
        self.start_pos = None
        self.end_pos = None
        self.selected_contour = None
        self.contour_inner = None
        self.selected_point_idx = None
        self.contour_selected = False
        self.scale_factor = 0.8
        self.final_offset = []
        self.mask = []
        self.temp_masked_points = []  # Danh sách tạm thời các điểm bị bôi đen
        self.final_contour = []  # Danh sách các điểm đã được lưu

        # Label Widget
        self.label = QLabel(self)
        self.label.setScaledContents(True)

        # Frame Widget
        self.control_panel = QFrame(self)
        self.control_panel.setFrameShape(QFrame.StyledPanel)
        self.control_panel.setMinimumWidth(250)

        # Buttons, Slider, and SpinBox
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

        # Layout
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
        """Cập nhật hình ảnh hiển thị trên QLabel."""
        display = self.template_color.copy()
        self.draw_contours(display)
        self.draw_inner_contour(display)
        self.draw_final_offset(display)
        self.draw_final_contour(display)  # Vẽ final_contour lên giao diện

        # Chuyển đổi hình ảnh OpenCV sang QImage
        q_img = self.convert_cv_image_to_qimage(display)
        self.pixmap = QPixmap.fromImage(q_img)

        # Vẽ lại các hình chữ nhật (nếu có) lên QPixmap
        self.draw_rectangles_on_pixmap()

        # Cập nhật QLabel
        self.label.setPixmap(self.pixmap)

    def draw_contours(self, display):
        """Vẽ các contour lên hình ảnh."""
        cv2.drawContours(display, self.contours_template, -1, (255, 255, 255), 1)

    def draw_inner_contour(self, display):
        """Vẽ inner contour lên hình ảnh."""
        if self.contour_inner is not None:
            cv2.drawContours(display, [self.contour_inner[:, :, 0:2]], -1, (0, 0, 255), 2)
            for i, point in enumerate(self.contour_inner[:, :, 0:2]):
                x, y = point[0]
                cv2.circle(display, (x, y), 5, (255, 0, 0), -1)
                cv2.putText(display, str(i), (x + 5, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

    def draw_final_offset(self, display):
        """Vẽ các điểm final offset lên hình ảnh."""
        if self.final_offset:
            for i, point in enumerate(self.final_offset):
                x, y = point
                cv2.circle(display, (x, y), 3, (0, 255, 0), -1)
                cv2.putText(display, str(i), (x + 5, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)
            if len(self.final_offset) > 1:
                cv2.polylines(display, [np.array(self.final_offset)], isClosed=False, color=(0, 255, 0), thickness=2)

    def draw_final_contour(self, display):
        """Vẽ final_contour lên hình ảnh."""
        if self.final_contour:
            for i, point in enumerate(self.final_contour):
                x, y = point
                cv2.circle(display, (x, y), 3, (255, 0, 255), -1)  # Màu khác để phân biệt
                cv2.putText(display, str(i), (x + 5, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 1, cv2.LINE_AA)
            if len(self.final_contour) > 1:
                cv2.polylines(display, [np.array(self.final_contour)], isClosed=False, color=(255, 0, 255), thickness=2)

    def convert_cv_image_to_qimage(self, display):
        """Chuyển đổi hình ảnh OpenCV sang QImage."""
        height, width, channel = display.shape
        bytes_per_line = 3 * width
        return QImage(display.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()

    def draw_rectangles_on_pixmap(self):
        """Vẽ hình chữ nhật lên QPixmap."""
        if self.start_pos and self.end_pos:
            painter = QPainter(self.pixmap)
            painter.setPen(QPen(Qt.red, 2, Qt.DashLine))
            painter.setBrush(QColor(0, 0, 0, 100))  # Màu đen trong suốt
            painter.drawRect(self.start_pos.x(), self.start_pos.y(),
                            self.end_pos.x() - self.start_pos.x(),
                            self.end_pos.y() - self.start_pos.y())
            painter.end()

    def reset_selection(self):
        """Reset các lựa chọn contour."""
        self.selected_contour = None
        self.contour_inner = None
        self.contour_selected = False
        self.update_display()

    def update_scale(self, value):
        """Cập nhật scale factor và vẽ lại contour."""
        self.scale_factor = value
        if self.selected_contour is not None:
            self.contour_inner = self.processor.contour_offset(self.selected_contour, -self.scale_factor)
            self.contour_inner = cv2.approxPolyDP(self.contour_inner, epsilon=1, closed=True)
            self.contour_inner = np.concatenate((self.contour_inner, np.zeros((self.contour_inner.shape[0], 1, 1), dtype=self.contour_inner.dtype)), axis=2)
        self.update_display()

    def save_points(self):
        """Lưu các điểm được chọn."""
        if self.contour_inner is not None:
            # Thêm các điểm tạm thời bị bôi đen vào final_contour
            self.final_contour.extend(self.temp_masked_points)
            self.temp_masked_points = []  # Xóa danh sách tạm thời
            self.update_display()

    def clear_final_offset(self):
        """Xóa các điểm đã lưu."""
        self.final_offset = []
        self.final_contour = []
        self.update_display()

    def mouseDoubleClickEvent(self, event):
        """Xử lý sự kiện double click chuột."""
        if event.button() == Qt.MouseButton.LeftButton:
            label_width, label_height = self.label.width(), self.label.height()
            img_height, img_width = self.template_color.shape[:2]

            pos = event.position().toPoint()
            x = int(pos.x() * (img_width / label_width))
            y = int(pos.y() * (img_height / label_height))

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

    def mousePressEvent(self, event):
        """Xử lý sự kiện nhấn chuột."""
        self.start_pos = event.position().toPoint()
        self.end_pos = self.start_pos
        self.update()

    def mouseMoveEvent(self, event):
        """Xử lý sự kiện di chuyển chuột."""
        if self.start_pos:
            self.end_pos = event.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, event):
        """Xử lý sự kiện thả chuột."""
        if self.start_pos:
            self.end_pos = event.position().toPoint()
            self.add_mask_region(self.start_pos, self.end_pos)
            self.start_pos = None
            self.update()

    def add_mask_region(self, start, end):
        """Lưu danh sách điểm nằm trong vùng bôi đen."""
        label_width = self.label.width()
        label_height = self.label.height()
        img_width = self.template_color.shape[1]
        img_height = self.template_color.shape[0]

        scale_x = label_width / img_width
        scale_y = label_height / img_height

        start_x = int(self.start_pos.x() / scale_x)
        start_y = int(self.start_pos.y() / scale_y)
        end_x = int(self.end_pos.x() / scale_x)
        end_y = int(self.end_pos.y() / scale_y)
        x1 = min(max(start_x, 0), max(end_x, 0))
        y1 = min(max(start_y, 0), max(end_y, 0))
        x2 = max(min(start_x, self.template_color.shape[1]), min(end_x, self.template_color.shape[1]))
        y2 = max(min(start_y, self.template_color.shape[0]), min(end_y, self.template_color.shape[0]))

        # Kiểm tra các điểm trong contour_inner có nằm trong vùng bôi đen không
        if self.contour_inner is not None:
            for point in self.contour_inner[:, :, 0:2]:
                x, y = point[0]
                if x1 <= x <= x2 and y1 <= y <= y2:
                    self.temp_masked_points.append((x, y))  # Lưu điểm bị bôi đen

    def is_inside_mask(self, x, y):
        """Kiểm tra điểm (x, y) có nằm trong vùng bôi đen không."""
        return (x, y) in self.mask and 0 <= x < self.template_color.shape[1] and 0 <= y < self.template_color.shape[0]

    def paintEvent(self, event):
        """Vẽ lại hình ảnh và các hình chữ nhật."""
        pixmap = self.pixmap.copy()
        painter = QPainter(pixmap)

        if self.start_pos and self.end_pos:
            label_width = self.label.width()
            label_height = self.label.height()
            img_width = self.template_color.shape[1]
            img_height = self.template_color.shape[0]

            scale_x = label_width / img_width
            scale_y = label_height / img_height

            start_x = int(self.start_pos.x() / scale_x)
            start_y = int(self.start_pos.y() / scale_y)
            end_x = int(self.end_pos.x() / scale_x)
            end_y = int(self.end_pos.y() / scale_y)

            painter.setPen(QPen(Qt.red, 2, Qt.DashLine))
            painter.setBrush(QColor(0, 0, 0, 100))  # Màu đen trong suốt
            painter.drawRect(start_x, start_y, end_x - start_x, end_y - start_y)

        painter.end()
        self.label.setPixmap(pixmap)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.editor = ContourEditor("/home/vinhdq/vision guide robot/image/captured_image.png")
        self.setWindowTitle("Contour Editor")
        self.resize(1000, 600)
        self.setMinimumSize(800, 400)
        self.setCentralWidget(self.editor)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())