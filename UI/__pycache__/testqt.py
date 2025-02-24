from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel
from PySide6.QtGui import QMouseEvent
from PySide6.QtCore import Qt, QPoint

class CustomWidget(QWidget):
    def __init__(self, name, parent=None):
        super().__init__(parent)
        self.name = name
        self.setMouseTracking(True)  # Cho phép bắt sự kiện di chuột

    def enterEvent(self, event):
        print(f"Chuột vào {self.name}")
        self.setCursor(Qt.CrossCursor)  # Đổi con trỏ để nhận biết vùng khác nhau

    def mouseMoveEvent(self, event: QMouseEvent):
        global_pos = self.mapToGlobal(event.pos())  # Chuyển tọa độ local -> global
        local_pos = self.mapFromGlobal(global_pos)  # Chuyển global -> local (xác nhận)
        print(f"{self.name}: Tọa độ local {event.pos()} - Global {global_pos} - Converted Local {local_pos}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        main_widget = QWidget(self)
        self.setCentralWidget(main_widget)

        layout = QVBoxLayout(main_widget)

        self.image_area = CustomWidget("Khu vực Hình Ảnh", self)
        self.other_area = CustomWidget("Khu vực Khác", self)

        self.image_area.setStyleSheet("background-color: lightblue; border: 1px solid black;")
        self.other_area.setStyleSheet("background-color: lightgreen; border: 1px solid black;")

        layout.addWidget(self.image_area)
        layout.addWidget(self.other_area)

        self.setMouseTracking(True)  # Bật tracking toàn bộ cửa sổ

app = QApplication([])
window = MainWindow()
window.show()
app.exec()
