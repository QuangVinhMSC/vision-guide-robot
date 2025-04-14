import sys
import cv2
import numpy as np
from PySide6.QtWidgets import (QApplication, QLabel, QWidget, QVBoxLayout, QHBoxLayout, 
                              QPushButton, QSlider, QFrame, QSpinBox, QMainWindow, 
                              QTabWidget, QFileDialog, QMessageBox, QScrollArea, QGridLayout)
from PySide6.QtGui import QPixmap, QImage, QPainter, QPen, QColor
from PySide6.QtCore import Qt
from camera_editor import CameraApp
from cam_view import CamView
import os
from PySide6.QtCore import Signal

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
        self.cap_a_shot = QPushButton("Capture Image")
        self.cap_a_shot.clicked.connect(self.capashot)
        self.btn_update = QPushButton("Cập nhật điểm")  # Thêm nút cập nhật
        self.btn_update.clicked.connect(self.update_box_container)  # Kết nối sự kiện
        
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
        self.slider_scale_epsilon.setMaximum(150)
        self.slider_scale_epsilon.setTickInterval(1)
        self.slider_scale_epsilon.setTickPosition(QSlider.TicksBelow)
        self.slider_scale_epsilon.valueChanged.connect(self.update_scale_epsilon)
        self.threshol_box = QSpinBox()
        self.threshol_box.setRange(0, 255)
        self.offset_box = QSpinBox()
        self.offset_box.setRange(-150, 150)
        self.epsilon_box = QSpinBox()
        self.epsilon_box.setRange(1, 150)
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
        #Panel Layout
        control_layout = QVBoxLayout()
        control_layout.addWidget(self.cap_a_shot)
        control_layout.addLayout(threshol_layout)
        control_layout.addLayout(offset_layout)
        control_layout.addLayout(epsilon_layout)
        control_layout.addWidget(self.btn_reset)
        control_layout.addWidget(self.btn_update)  # Thêm nút cập nhật vào layout
        control_layout.addLayout(ruler_layout)
        control_layout.addWidget(self.btn_save_npy)
        
        # Khu vực hiển thị các box (dùng QScrollArea)
        self.box_scroll = QScrollArea()
        self.box_scroll.setWidgetResizable(True)
        
        # Widget chứa các box thực tế
        self.box_container = BoxContainerWidget()
        self.box_scroll.setWidget(self.box_container)
        self.box_container.spinbox_value_changed.connect(self.method_to_run_on_spinbox_change)
        # Thêm vào control panel
        control_layout.addWidget(self.box_scroll)
        control_layout.addStretch()
        self.control_panel.setLayout(control_layout)

        main_layout = QHBoxLayout()
        main_layout.addWidget(self.label)
        main_layout.addWidget(self.control_panel, 1)

        self.setLayout(main_layout)
        self.update_display()
        
    def method_to_run_on_spinbox_change(self, idx, value):
        """Phương thức bạn tự xây dựng để xử lý khi giá trị trong SpinBox cột 1 thay đổi."""
        # Xử lý logic tại đây
        print(f"Giá trị SpinBox tại cột {idx} đã thay đổi: {value}")
        # (Tùy vào yêu cầu, bạn có thể cập nhật các giá trị khác hoặc tính toán gì đó)
        # Ví dụ: cập nhật giá trị vào final_contour_3d hoặc làm gì đó liên quan đến dữ liệu.
        self.contour_inner = self.processor.calculate_offset(self.selected_contour, self.sim_contour, -self.scale_factor, point=idx, individual_offset= -value)
        self.update_display()

    def update_box_spinboxes(self):
        """Cập nhật toàn bộ spinbox dựa theo scale factor hiện tại."""
        if self.box_container and self.box_container.rows:
            for i, (label, spinbox1, spinbox2) in enumerate(self.box_container.rows):
                # Set giá trị cho SpinBox thứ 1 (cột 1) theo giá trị scale_factor
                spinbox1.blockSignals(True)  # Chặn tín hiệu valueChanged trong lúc set
                spinbox1.setValue(self.scale_factor)  # Đồng bộ với scale_factor
                spinbox1.blockSignals(False)  # Mở lại tín hiệu
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
        
    def update_box_container(self):
        """Cập nhật box container dựa trên các điểm trong contour_inner khi nhấn nút."""
        if self.contour_inner is not None:
            self.box_container.update_rows(len(self.contour_inner))
            
            for i, point in enumerate(self.contour_inner):
                x, y = point[0]
                # Giá trị offset mặc định là scale_factor
                offset_value = self.scale_factor

                if i < len(self.final_contour_3d):
                    offset_value = self.final_contour_3d[i][2]

                # Cập nhật giá trị cho SpinBox
                spinbox = self.box_container.rows[i][1]
                spinbox.blockSignals(True)  # Chặn tín hiệu valueChanged trong lúc set
                spinbox.setValue(offset_value)
                spinbox.blockSignals(False)
                
                # Kết nối signal valueChanged
                spinbox.valueChanged.connect(
                    lambda value, idx=i: self.update_point_offset(idx, value)
                )


    def update_point_offset(self, point_idx, offset_value):
        """Cập nhật giá trị offset cho điểm được chọn."""
        if point_idx < len(self.final_contour_3d):
            self.final_contour_3d[point_idx][2] = offset_value
            self.update_display()

    def update_scale_epsilon(self,value):
        self.scale_epsilon = value
        if self.selected_contour is not None:
            self.sim_contour = self.processor.simplify_contour_min_distance(self.selected_contour, self.scale_epsilon)
            self.contour_inner = self.processor.calculate_offset(self.selected_contour,self.sim_contour, -self.scale_factor)
        self.update_display()

    def update_scale_threshol(self, value):
        self.processor.threshol_editor((value,255))
        self.contours_template = self.processor.contours_template
        self.update_display()

    def update_scale_offset(self, value):
        """Cập nhật scale factor và vẽ lại contour."""
        self.scale_factor = value
        if self.selected_contour is not None:
            self.contour_inner = self.processor.calculate_offset(self.selected_contour, self.sim_contour, -self.scale_factor)
        self.update_box_spinboxes()  # Đồng bộ lại các SpinBox trong BoxContainer với scale_factor mới
        self.update_display()

    def draw_point(self,display):
        x, y = self.final_contour[self.point_box.value()]
        cv2.circle(display, (x, y), 8, (100, 0, 255), -1)  # Màu khác để phân biệt

    def draw_contours(self, display):
        """Vẽ các contour lên hình ảnh."""
        cv2.drawContours(display, self.contours_template, -1, (255,255, 0), 3)

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
        """Reset các lựa chọn contour và BoxContainer."""
        self.selected_contour = None
        self.contour_inner = None
        self.contour_selected = False
        self.final_contour = []
        self.final_contour_3d = []
        self.temp_masked_points = []  # Xóa danh sách điểm tạm thời
        self.box_container.update_rows(0)  # Reset BoxContainer (xóa hết các hàng)
        self.update_display()  # Cập nhật lại giao diện

    def capashot(self):
        self.processor.take_a_image()
        self.template_color = self.processor.template_color
        self.contours_template = self.processor.contours_template
        self.update_display()
            
    def save_numpy(self):
        """Lưu trực tiếp các điểm trong contour_inner vào file numpy với shape (N,1,3)."""
        if self.contour_inner is not None:
            # Tạo một mảng numpy mới có shape (N, 1, 3)
            contour_with_value = []

            for i, point in enumerate(self.contour_inner):
                x, y = point[0]
                extra_value = self.box_container.rows[i][2].value()  # Lấy giá trị từ SpinBox thứ 2 (cột thêm)
                contour_with_value.append([[x, y, extra_value]])

            contour_with_value = np.array(contour_with_value, dtype=np.float32)  # Ép kiểu float32 cho chuẩn

            # Save vào file .npy
            current_dir = os.path.dirname(os.path.abspath(__file__))
            template_folder = os.path.join(current_dir, "template")

            if not os.path.exists(template_folder):
                os.makedirs(template_folder)

            file_path1 = os.path.join(template_folder, "contour_inner.npy")
            file_path2 = os.path.join(template_folder, "selected_contour.npy")

            if os.path.exists(file_path1) or os.path.exists(file_path2):
                reply = QMessageBox.question(self, "Xác nhận",
                                            f"Có file trùng trong thư mục:\n{file_path1}\n{file_path2}\nBạn có muốn ghi đè không?",
                                            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.No:
                    return
            try:
                np.save(file_path1, contour_with_value)  # Đây! Lưu đúng shape (N,1,3)
                np.save(file_path2, self.selected_contour)

                QMessageBox.information(self, "Thành công", f"Đã lưu file vào thư mục:\n{template_folder}")
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể lưu file: {str(e)}")
                print("Lỗi khi lưu file:", e)


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
                        self.sim_contour = self.processor.simplify_contour_min_distance(self.selected_contour,self.scale_epsilon)
                        self.contour_inner = self.processor.calculate_offset(self.selected_contour,self.sim_contour, -self.scale_factor)
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


class BoxContainerWidget(QWidget):
    # Tạo tín hiệu khi giá trị SpinBox thay đổi
    spinbox_value_changed = Signal(int, int)  # Tín hiệu truyền index và giá trị mới

    def __init__(self):
        super().__init__()
        self.grid = QGridLayout(self)
        self.grid.setSpacing(5)
        self.rows = []

    def update_rows(self, row_count):
        """Cập nhật lại số lượng hàng trong BoxContainer và reset giá trị."""
        # Xóa các hàng cũ
        for row in self.rows:
            for widget in row:
                self.grid.removeWidget(widget)
                widget.deleteLater()
        self.rows = []

        # Thêm hàng mới (mỗi hàng gồm label, spinbox 1, spinbox 2)
        for i in range(row_count):
            row_widgets = [
                QLabel(f"{i}"),
                QSpinBox(),
                QSpinBox()  # Cột thêm (spinbox thứ 2)
            ]
            
            # Style cho các widget
            row_widgets[0].setStyleSheet("background: #3498db; color: white; padding: 5px;")
            row_widgets[1].setStyleSheet("background: #e74c3c; color: white;")
            row_widgets[2].setStyleSheet("background: #e74c3c; color: white;")  # Style cho cột thêm
            
            row_widgets[1].setRange(-200, 200)  # Giới hạn giá trị offset
            row_widgets[2].setRange(-200, 200)  # Cột thêm có giới hạn tương tự

            # Lắng nghe sự thay đổi của SpinBox thứ nhất (cột thứ 1)
            row_widgets[1].valueChanged.connect(
                lambda value, idx=i: self.spinbox_value_changed.emit(idx, value)  # Phát tín hiệu khi giá trị thay đổi
            )
            
            # Thêm vào layout
            self.grid.addWidget(row_widgets[0], i, 0)
            self.grid.addWidget(row_widgets[1], i, 1)
            self.grid.addWidget(row_widgets[2], i, 2)  # Thêm cột mới

            self.rows.append(row_widgets)



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
        self.tab2.thr = self.tab1.slider_scale_thresh.value()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())