import sys
import cv2
import numpy as np
from PySide6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSlider, QFrame, QSpinBox, QMainWindow,QTabWidget,QFileDialog,QMessageBox
from PySide6.QtGui import QPixmap, QImage, QPainter, QPen, QColor
from PySide6.QtCore import Qt
from camera_editor import CameraApp
from cam_view import CamView
import os

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
        self.scale_epsilon = 1
        self.final_offset = []
        self.mask = []
        self.temp_masked_points = []  # Danh sách tạm thời các điểm bị bôi đen
        self.final_contour = []  # Danh sách các điểm đã được lưu
        self.final_contour_3d = []

        # Label Widget
        self.label = QLabel(self)
        self.label.setScaledContents(True)
        self.ruler = QLabel("Ruler")
        self.ruler_x = QLabel("0")
        self.ruler_y = QLabel("0")
        self.ruler_diag = QLabel("0")
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
        self.cap_a_shot = QPushButton("Capture Image")
        self.cap_a_shot.clicked.connect(self.capashot)
        self.slider_scale_offset = QSlider(Qt.Horizontal)
        self.slider_scale_offset.setMinimum(-150)
        self.slider_scale_offset.setMaximum(150)
        self.slider_scale_offset.setTickInterval(10)
        self.slider_scale_offset.setTickPosition(QSlider.TicksBelow)
        self.slider_scale_offset.valueChanged.connect(self.update_scale_offset)
        self.offsetbox = QSpinBox()
        self.slider_scale_thresh = QSlider(Qt.Horizontal)
        self.slider_scale_thresh.setMinimum(0)
        self.slider_scale_thresh.setMaximum(255)
        self.slider_scale_thresh.setTickInterval(10)
        self.slider_scale_thresh.setTickPosition(QSlider.TicksBelow)
        self.slider_scale_thresh.valueChanged.connect(self.update_scale_threshol)
        self.slider_scale_epsilon = QSlider(Qt.Horizontal)
        self.slider_scale_epsilon.setMinimum(1)
        self.slider_scale_epsilon.setMaximum(10)
        self.slider_scale_epsilon.setTickInterval(1)
        self.slider_scale_epsilon.setTickPosition(QSlider.TicksBelow)
        self.slider_scale_epsilon.valueChanged.connect(self.update_scale_epsilon)
        self.threshol_box = QSpinBox()
        self.threshol_box.setRange(0, 255)
        self.offset_box = QSpinBox()
        self.offset_box.setRange(-150, 150)
        self.epsilon_box = QSpinBox()
        self.epsilon_box.setRange(1, 10)
        self.point_box = QSpinBox()
        self.point_box.setRange(0,0)
        self.point_box.valueChanged.connect(self.select_point2edit)
        self.zedit_box = QSpinBox()
        self.zedit_box.setRange(-100,100)
        self.zedit_box.valueChanged.connect(self.z_editor)
        self.btn_save_npy = QPushButton("Save Points")
        self.btn_save_npy.clicked.connect(self.save_numpy)

        #connect value
        self.slider_scale_thresh.valueChanged.connect(self.threshol_box.setValue)
        self.threshol_box.valueChanged.connect(self.slider_scale_thresh.setValue)
        self.slider_scale_offset.valueChanged.connect(self.offset_box.setValue)
        self.offset_box.valueChanged.connect(self.slider_scale_offset.setValue)
        self.slider_scale_epsilon.valueChanged.connect(self.epsilon_box.setValue)
        self.epsilon_box.valueChanged.connect(self.slider_scale_epsilon.setValue)
        #pre-setvalue
        self.slider_scale_thresh.setValue(90)
        self.slider_scale_offset.setValue(0)
        self.slider_scale_epsilon.setValue(1)

        # Small Layout
        threshol_layout = QHBoxLayout()#
        threshol_layout.addWidget(self.slider_scale_thresh)
        threshol_layout.addWidget(self.threshol_box)
        offset_layout = QHBoxLayout()#
        offset_layout.addWidget(self.slider_scale_offset)
        offset_layout.addWidget(self.offset_box)
        epsilon_layout = QHBoxLayout()#
        epsilon_layout.addWidget(self.slider_scale_epsilon)
        epsilon_layout.addWidget(self.epsilon_box)
        ruler_layout = QHBoxLayout()
        ruler_layout.addWidget(self.ruler)
        ruler_layout.addWidget(self.ruler_x)
        ruler_layout.addWidget(self.ruler_y)
        ruler_layout.addWidget(self.ruler_diag)
        z_editor = QHBoxLayout()
        z_editor.addWidget(self.point_box)
        z_editor.addWidget(self.zedit_box)
        #Panel Layout
        control_layout = QVBoxLayout()
        control_layout.addWidget(self.cap_a_shot)
        control_layout.addLayout(threshol_layout)
        control_layout.addLayout(offset_layout)
        control_layout.addLayout(epsilon_layout)
        control_layout.addWidget(self.btn_reset)
        control_layout.addWidget(self.btn_save)
        control_layout.addWidget(self.btn_clear)
        control_layout.addLayout(ruler_layout)
        control_layout.addLayout(z_editor)
        control_layout.addWidget(self.btn_save_npy)
        control_layout.addStretch()
        self.control_panel.setLayout(control_layout)

        main_layout = QHBoxLayout()
        main_layout.addWidget(self.label)
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
        try:
            self.draw_point(display)
        except:
            pass
        q_img = self.convert_cv_image_to_qimage(display)
        self.pixmap = QPixmap.fromImage(q_img)
        self.draw_rectangles_on_pixmap()
        self.label.setPixmap(self.pixmap)
    def update_scale_epsilon(self,value):
        self.scale_epsilon = value
        if self.selected_contour is not None:
            self.contour_inner = self.processor.contour_offset(self.selected_contour, -self.scale_factor)
            self.contour_inner = cv2.approxPolyDP(self.contour_inner, epsilon=self.scale_epsilon, closed=True)
        self.update_display()
    def update_scale_threshol(self, value):
        self.processor.threshol_editor((value,255))
        self.contours_template = self.processor.contours_template
        self.update_display()
    def update_scale_offset(self, value):
        """Cập nhật scale factor và vẽ lại contour."""
        self.scale_factor = value
        if self.selected_contour is not None:
            self.contour_inner = self.processor.contour_offset(self.selected_contour, -self.scale_factor)
            self.contour_inner = cv2.approxPolyDP(self.contour_inner, epsilon=self.scale_epsilon, closed=True)
            # self.contour_inner = np.concatenate((self.contour_inner, np.zeros((self.contour_inner.shape[0], 1, 1), dtype=self.contour_inner.dtype)), axis=2)
        self.update_display()
    def draw_point(self,display):
        x, y = self.final_contour[self.point_box.value()]
        cv2.circle(display, (x, y), 8, (100, 0, 255), -1)  # Màu khác để phân biệt
    def draw_contours(self, display):
        """Vẽ các contour lên hình ảnh."""
        cv2.drawContours(display, self.contours_template, -1, (255,255, 0), 3)
    def select_point2edit(self):
        self.zedit_box.setValue(self.final_contour_3d[self.point_box.value()][2])
        self.update_display()
    def z_editor(self):
        try:
            self.final_contour_3d[self.point_box.value()][2] = self.zedit_box.value()
            print(self.final_contour_3d[self.point_box.value()])
        except:
            pass
    def draw_inner_contour(self, display):
        """Vẽ inner contour lên hình ảnh."""
        if self.contour_inner is not None:
            cv2.drawContours(display, [self.contour_inner], -1, (0, 0, 255), 2)
            for i, point in enumerate(self.contour_inner):
                x, y = point[0]
                cv2.circle(display, (x, y), 5, (255, 0, 0), -1)
                cv2.putText(display, str(i), (x + 5, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

    def draw_final_offset(self, display):
        """Vẽ các điểm final offset lên hình ảnh."""
        if self.final_offset:
            for i, point in enumerate(self.final_offset):
                x, y = point
                cv2.circle(display, (x, y), 3, (0, 0, 0), -1)
                cv2.putText(display, str(i), (x + 5, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)
            if len(self.final_offset) > 1:
                cv2.polylines(display, [np.array(self.final_offset)], isClosed=False, color=(0, 255, 0), thickness=2)

    def draw_final_contour(self, display):
        """Vẽ final_contour lên hình ảnh."""
        if self.final_contour:
            for i, point in enumerate(self.final_contour):
                x, y = point
                cv2.circle(display, (x, y), 3, (0, 0, 0), -1)  # Màu khác để phân biệt
                cv2.putText(display, str(i), (x + 5, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 3, cv2.LINE_AA)
            if len(self.final_contour) > 1:
                cv2.polylines(display, [np.array(self.final_contour)], isClosed=False, color=(0, 0, 0), thickness=2)

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
    def capashot(self):
        self.processor.take_a_image()
        self.template_color = self.processor.template_color
        self.contours_template = self.processor.contours_template
        
        self.update_display()
    def save_numpy(self):
        self.final_contour_3d = np.array(self.final_contour_3d).reshape(len(self.final_contour_3d),1,3)
        print(self.contour_selected)
        # Lấy đường dẫn thư mục chứa mã nguồn
        current_dir = os.path.dirname(os.path.abspath(__file__))  # Thư mục chứa file code
        template_folder = os.path.join(current_dir, "template")  # Tạo thư mục "template"

        # Tạo thư mục nếu chưa tồn tại
        if not os.path.exists(template_folder):
            os.makedirs(template_folder)

        # Định nghĩa đường dẫn file
        file_path1 = os.path.join(template_folder, "contour_inner.npy")
        file_path2 = os.path.join(template_folder, "selected_contour.npy")

        # Kiểm tra nếu file đã tồn tại, yêu cầu xác nhận trước khi ghi đè
        if os.path.exists(file_path1) or os.path.exists(file_path2):
            reply = QMessageBox.question(self, "Xác nhận",
                                        f"Có file trùng trong thư mục:\n{file_path1}\n{file_path2}\nBạn có muốn ghi đè không?",
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                return
        try:
            np.save(file_path1, self.final_contour_3d)
            np.save(file_path2, self.selected_contour)

            QMessageBox.information(self, "Thành công", f"Đã lưu file vào thư mục:\n{template_folder}")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể lưu file: {str(e)}")
            print("Lỗi khi lưu file:", e)

    def save_points(self):
        """Lưu các điểm được chọn."""
        if self.contour_inner is not None:
            # Thêm các điểm tạm thời bị bôi đen vào final_contour
            self.final_contour.extend(self.temp_masked_points)
            self.final_contour_3d.extend([[x, y, 0] for x, y in self.temp_masked_points])
            
            self.temp_masked_points = []  # Xóa danh sách tạm thời
            self.point_box.setRange(0,len(self.final_contour)-1)
            
            self.update_display()

    def clear_final_offset(self):
        """Xóa các điểm đã lưu."""
        self.final_offset = []
        self.final_contour = []
        self.final_contour_3d = []
        self.point_box.setRange(0,len(self.final_contour))
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
                        self.contour_inner = cv2.approxPolyDP(self.contour_inner, epsilon=self.scale_epsilon, closed=True)
                        # self.contour_inner = np.concatenate((self.contour_inner, np.zeros((self.contour_inner.shape[0], 1, 1), dtype=self.contour_inner.dtype)), axis=2)
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
            self.add_mask_region()
            self.start_pos = None
            self.update()

    def add_mask_region(self):
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
        self.ruler_x.setText(f"{abs(x1-x2)}")
        self.ruler_y.setText(f"{abs(y1-y2)}")
        self.ruler_diag.setText(f"{int(np.sqrt((x1-x2)**2+(y1-y2)**2))}")
        # Kiểm tra các điểm trong contour_inner có nằm trong vùng bôi đen không
        if self.contour_inner is not None:
            print(self.contour_inner.shape)
            for point in self.contour_inner:
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
        self.setWindowTitle("Contour Editor")
        self.resize(1000, 600)
        self.setMinimumSize(800, 400)
        self.initUI()
    def initUI(self):
        tab_widget = QTabWidget()

        # Tạo hai tab
        self.tab0 = CamView()
        self.tab1 = ContourEditor("/home/vinhdq/vision guide robot/image/captured_image.png")
        self.tab2 = CameraApp()
        # Layout cho tab 1

        # Thêm tab vào QTabWidget
        tab_widget.addTab(self.tab0, "Tab 0")
        tab_widget.addTab(self.tab1, "Tab 1")
        tab_widget.addTab(self.tab2, "Tab 2")
        tab_widget.currentChanged.connect(self.on_tab_changed)
        self.setCentralWidget(tab_widget)
    def on_tab_changed(self, index):
        self.pr_index = 0
        if self.pr_index == 0:  # Tab 2 được chọn
            self.tab0.close_app()
        if index == 0:
            self.tab0.restart_camera()
        self.pr_index = index
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())