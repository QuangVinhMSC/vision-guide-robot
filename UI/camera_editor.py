import sys
import cv2
import numpy as np
from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QFileDialog, QSizePolicy
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import Qt
from camera import ContourDetector


class CameraApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.matcher = None

    def initUI(self):
        self.setWindowTitle("Contour Detection")
        self.setGeometry(100, 100, 1000, 600)
        self.setMinimumSize(800, 400)
        
        # Layout chính
        self.main_layout = QVBoxLayout()
        
        # Layout ngang để đặt hai nút ở góc trái trên
        self.button_layout = QHBoxLayout()
        
        self.select_button = QPushButton("Chọn thư mục chứa file .npy", self)
        self.select_button.clicked.connect(self.select_directory)
        self.button_layout.addWidget(self.select_button)

        self.button = QPushButton("Run Contour Detection", self)
        self.button.clicked.connect(self.run_detection)
        self.button.setEnabled(False)
        self.button_layout.addWidget(self.button)

        # Canh lề bên trái
        self.button_layout.addStretch()
        
        self.main_layout.addLayout(self.button_layout)

        # QLabel để hiển thị ảnh
        self.image_label = QLabel(self)
        self.image_label.setScaledContents(False)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.main_layout.addWidget(self.image_label)

        self.setLayout(self.main_layout)

    def select_directory(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Chọn thư mục chứa file .npy")
        if folder_path:
            file1 = f"{folder_path}/selected_contour.npy"
            file2 = f"{folder_path}/contour_inner.npy"
            
            if not (cv2.os.path.exists(file1) and cv2.os.path.exists(file2)):
                print("Không tìm thấy hai file .npy trong thư mục đã chọn.")
                return
            
            self.matcher = ContourDetector(file1, file2)
            self.button.setEnabled(True)

    def run_detection(self):
        if self.matcher is None:
            print("Chưa chọn thư mục chứa file .npy!")
            return

        gray = self.matcher.capture_single_shot()
        # try:
        cnt_inner, cnt_image, best_contour, best_iou, best_iou_translation, best_iou_size, processing_time = self.matcher.contour_detection(gray)

        # Vẽ kết quả lên ảnh gốc
        cv2.drawContours(gray, [cnt_inner[:, :, 0:2]], -1, (0, 255, 0), 2)
        cv2.drawContours(gray, [cnt_image], -1, (0, 255, 0), 2)
        cv2.drawContours(gray, [best_contour], -1, (255, 0, 0), 2)
        cv2.putText(gray, f'IoU Rotation: {best_iou:.4f}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
        cv2.putText(gray, f'IoU Translation: {best_iou_translation:.4f}', (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
        cv2.putText(gray, f'IoU Size: {best_iou_size:.4f}', (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
        cv2.putText(gray, f'Latency: {processing_time:.4f}', (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

        # Chuyển ảnh từ OpenCV sang QImage để hiển thị
        height, width = gray.shape
        q_image = QImage(gray.data, width, height, width, QImage.Format_Grayscale8)

        # Tạo QPixmap từ QImage
        pixmap = QPixmap.fromImage(q_image)

        # Lấy kích thước QLabel
        label_width = self.image_label.width()
        label_height = self.image_label.height()

        # Resize ảnh nhưng giữ đúng tỷ lệ
        pixmap = pixmap.scaled(label_width, label_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        self.image_label.setPixmap(pixmap)
        # except:
        #     print("ko co contour")
        #     pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CameraApp()
    window.show()
    sys.exit(app.exec())
