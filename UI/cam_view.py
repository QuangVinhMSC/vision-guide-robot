from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget, QPushButton, QMessageBox
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import QTimer, Qt
import cv2
import numpy as np
from pypylon import pylon

class CamView(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Camera acA2440-20gm Viewer")
        self.setGeometry(100, 100, 800, 600)
        
        self.layout = QVBoxLayout()
        self.label = QLabel("Initializing camera...")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setFixedSize(800, 600)
        self.layout.addWidget(self.label)
        
        self.setLayout(self.layout)
        
        if self.init_camera():
            self.timer = QTimer()
            self.timer.timeout.connect(self.update_frame)
            self.timer.start(30)
        else:
            QMessageBox.critical(self, "Error", "No camera found!")
            self.label.setText("No camera detected")
    
    def init_camera(self):
        try:
            TLFactory = pylon.TlFactory.GetInstance()
            devices = TLFactory.EnumerateDevices()
            if not devices:
                return False

            self.camera = pylon.InstantCamera(TLFactory.CreateDevice(devices[0]))
            self.camera.Open()
            self.camera.PixelFormat.SetValue("Mono8")
            self.camera.Width.SetValue(2440)
            self.camera.Height.SetValue(2048)

            self.camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
            self.converter = pylon.ImageFormatConverter()
            self.converter.OutputPixelFormat = pylon.PixelType_Mono8
            self.converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned
            return True
        except Exception as e:
            print(f"Camera error: {e}")
            return False
    
    def update_frame(self):
        if self.camera.IsGrabbing():
            grabResult = self.camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
            if grabResult.GrabSucceeded():
                image = self.converter.Convert(grabResult)
                img = image.GetArray()
                grabResult.Release()

                height, width = img.shape
                qimg = QImage(img.data, width, height, width, QImage.Format_Grayscale8)
                pixmap = QPixmap.fromImage(qimg)

                scaled_pixmap = pixmap.scaled(self.label.width(), self.label.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.label.setPixmap(scaled_pixmap)
    
    def close_app(self):
        self.timer.stop()
        if self.camera.IsGrabbing():
            self.camera.StopGrabbing()
        self.camera.Close()
    
    def restart_camera(self):
        self.timer.stop()
        if self.camera.IsGrabbing():
            self.camera.StopGrabbing()
        self.camera.Close()
        
        if self.init_camera():
            self.timer.start(30)
        else:
            QMessageBox.critical(self, "Error", "Failed to restart camera!")
            self.label.setText("Failed to restart camera")

if __name__ == "__main__":
    app = QApplication([])
    window = CamView()
    window.show()
    app.exec()