import sys
import cv2
import numpy as np
from PySide6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSlider, QFrame

class ContourEditor(QWidget):
    def __init__(self, image_path):
        super().__init__()
        self.setWindowTitle("Contour Editor")
        self.resize(1000, 600)  # Cửa sổ rộng hơn để có không gian cho hai phần
        self.setMinimumSize(800, 400)

        # Đọc ảnh và xử lý (giữ nguyên code của bạn)
        self.template_gray = cv2.imread(image_path, 0)
        self.template_color = cv2.cvtColor(self.template_gray, cv2.COLOR_GRAY2BGR)
        _, self.template_edges = cv2.threshold(self.template_gray, 90, 255, cv2.THRESH_BINARY)
        self.contours_template, _ = cv2.findContours(self.template_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        self.min_perimeter = 100
        self.contours_template = [cv2.approxPolyDP(cnt, epsilon=8, closed=True) for cnt in self.contours_template 
                                  if cv2.arcLength(cnt, closed=True) > self.min_perimeter]

        print(f'Số lượng contours sau khi lọc: {len(self.contours_template)}')

        self.selected_contour = None
        self.contour_inner = None
        self.selected_point_idx = None
        self.contour_selected = False
        self.scale_factor = 0.8  

        # Tạo QLabel để hiển thị ảnh
        self.label = QLabel(self)
        self.label.setScaledContents(True)

        # ====== Tạo khu vực chức năng (panel bên phải) ======
        self.control_panel = QFrame(self)
        self.control_panel.setFrameShape(QFrame.StyledPanel)
        self.control_panel.setMinimumWidth(250)

        # Các nút điều khiển
        self.btn_reset = QPushButton("Reset Contour")
        self.btn_reset.clicked.connect(self.reset_selection)

        self.slider_scale = QSlider(Qt.Horizontal)
        self.slider_scale.setMinimum(50)
        self.slider_scale.setMaximum(150)
        self.slider_scale.setValue(80)
        self.slider_scale.setTickInterval(10)
        self.slider_scale.setTickPosition(QSlider.TicksBelow)
        self.slider_scale.valueChanged.connect(self.update_scale)

        # Layout của panel bên phải
        control_layout = QVBoxLayout()
        control_layout.addWidget(self.btn_reset)
        control_layout.addWidget(self.slider_scale)
        control_layout.addStretch()
        self.control_panel.setLayout(control_layout)

        # ====== Bố cục chính (chia hai bên) ======
        main_layout = QHBoxLayout()
        main_layout.addWidget(self.label, 2)  # Chiếm 2 phần tỷ lệ
        main_layout.addWidget(self.control_panel, 1)  # Chiếm 1 phần tỷ lệ

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
        self.scale_factor = value / 100.0
        print(f"Scale Factor: {self.scale_factor}")
        if self.selected_contour is not None:
            self.contour_inner = self.shrink_contour(self.selected_contour, self.scale_factor)
            self.contour_inner = cv2.approxPolyDP(self.contour_inner, epsilon=8, closed=True)
            self.contour_inner = np.concatenate((self.contour_inner, np.zeros((self.contour_inner.shape[0], 1, 1), dtype=self.contour_inner.dtype)), axis=2)
        self.update_display()

    def update_display(self):
        """ Cập nhật hiển thị bằng PySide6 """
        display = self.template_color.copy()
        cv2.drawContours(display, self.contours_template, -1, (255, 255, 255), 1)

        if self.selected_contour is not None:
            cv2.drawContours(display, [self.selected_contour], -1, (0, 0, 255), 2)
            for point in self.selected_contour:
                x, y = point[0]
                cv2.circle(display, (x, y), 5, (255, 0, 0), -1)  # Chấm tròn xanh dương

        if self.contour_inner is not None:
            cv2.drawContours(display, [self.contour_inner[:, :, 0:2]], -1, (0, 255, 0), 2)  # Contour nhỏ với màu xanh lá
            for point in self.contour_inner[:, :, 0:2]:
                x, y = point[0]
                cv2.circle(display, (x, y), 3, (0, 255, 255), -1)  # Chấm tròn vàng

        # Chuyển đổi ảnh OpenCV sang QImage
        height, width, channel = display.shape
        bytes_per_line = 3 * width
        q_img = QImage(display.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
        pixmap = QPixmap.fromImage(q_img)

        # Hiển thị trên QLabel
        self.label.setPixmap(pixmap)

    def mousePressEvent(self, event):
        """ Xử lý sự kiện click chuột """
        if event.button() == Qt.LeftButton:
            # Lấy kích thước hiển thị của QLabel
            label_width = self.label.width()
            label_height = self.label.height()
            
            # Lấy kích thước ảnh gốc
            img_height, img_width = self.template_color.shape[:2]

            # Lấy tọa độ chuột trên QLabel
            label_x, label_y = event.position().x(), event.position().y()

            # Tính tỷ lệ scale theo từng chiều
            scale_x = img_width / label_width
            scale_y = img_height / label_height

            # Chuyển đổi tọa độ chuột về ảnh gốc
            x = int(label_x * scale_x)
            y = int(label_y * scale_y)

            print(f"Clicked at (scaled): ({x}, {y})")

            # Kiểm tra xem tọa độ có nằm trong contour nào không
            if not self.contour_selected:
                for cnt in self.contours_template:
                    if cv2.pointPolygonTest(cnt, (x, y), False) >= 0:
                        self.selected_contour = cnt
                        self.contour_inner = self.shrink_contour(cnt, self.scale_factor)  # Tạo contour nhỏ hơn
                        self.contour_inner = cv2.approxPolyDP(self.contour_inner, epsilon=8, closed=True)
                        self.contour_inner = np.concatenate((self.contour_inner, np.zeros((self.contour_inner.shape[0], 1, 1), dtype=self.contour_inner.dtype)), axis=2)
                        self.contour_selected = True
                        print("Contour đã chọn!")
                        break

            if self.selected_contour is not None:
                for i, point in enumerate(self.selected_contour):
                    px, py = point[0]
                    if abs(px - x) < 5 and abs(py - y) < 5:
                        self.selected_point_idx = i
                        print(f"Điểm đã chọn trên contour gốc: {px}, {py}")
                        break

            if self.contour_inner is not None:
                for i, point in enumerate(self.contour_inner[:, :, 0:2]):
                    px, py = point[0]
                    if abs(px - x) < 5 and abs(py - y) < 5:
                        self.selected_point_idx = i
                        print(f"Điểm đã chọn trên contour nhỏ: {px}, {py}")
                        break

            self.update_display()


    def shrink_contour(self, contour, scale):
        """ Hàm tạo contour nhỏ hơn """
        M = cv2.moments(contour)
        if M["m00"] == 0:
            return contour

        cx, cy = int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"])
        new_contour = []
        for point in contour:
            x, y = point[0]
            x_new = cx + scale * (x - cx)
            y_new = cy + scale * (y - cy)
            new_contour.append([[int(x_new), int(y_new)]])

        return np.array(new_contour, dtype=np.int32)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = ContourEditor("/home/vinhdq/vision guide robot/image/captured_image.png")
    editor.show()
    sys.exit(app.exec())
