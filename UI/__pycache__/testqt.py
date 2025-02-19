from PySide6.QtWidgets import QApplication, QLabel, QMainWindow
from PySide6.QtGui import QPixmap, QPainter, QPen, QColor
from PySide6.QtCore import Qt, QPoint
import sys

class ImageLabel(QLabel):
    def __init__(self, image_path):
        super().__init__()
        self.pixmap = QPixmap(image_path)
        self.setPixmap(self.pixmap)
        self.start_pos = None
        self.end_pos = None
        self.mask = []  # Lưu danh sách điểm được tô đen

    def mousePressEvent(self, event):
        print(1)
        self.start_pos = event.pos()
        self.end_pos = self.start_pos
        self.update()

    def mouseMoveEvent(self, event):
        print(2)
        if self.start_pos:
            self.end_pos = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        print(3)
        if self.start_pos:
            self.end_pos = event.pos()
            self.add_mask_region(self.start_pos, self.end_pos)
            self.start_pos = None
            self.update()

    def add_mask_region(self, start, end):
        print(4)
        """Lưu danh sách điểm nằm trong vùng bôi đen"""
        x1, y1 = min(start.x(), end.x()), min(start.y(), end.y())
        x2, y2 = max(start.x(), end.x()), max(start.y(), end.y())
        for x in range(x1, x2):
            for y in range(y1, y2):
                self.mask.append((x, y))  # Lưu điểm bôi đen

    def is_inside_mask(self, x, y):
        print(5)
        """Kiểm tra điểm (x, y) có nằm trong vùng bôi đen không"""
        return (x, y) in self.mask

    def paintEvent(self, event):
        print(6)
        """Vẽ lại hình ảnh kèm theo vùng bôi đen"""
        super().paintEvent(event)
        if not self.pixmap:
            return
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.pixmap)
        if self.start_pos and self.end_pos:
            painter.setPen(QPen(Qt.red, 2, Qt.DashLine))
            painter.setBrush(QColor(0, 0, 0, 100))  # Màu đen trong suốt
            painter.drawRect(self.start_pos.x(), self.start_pos.y(),
                             self.end_pos.x() - self.start_pos.x(),
                             self.end_pos.y() - self.start_pos.y())

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.image_label = ImageLabel("/home/vinhdq/vision guide robot/image/captured_image.png")
        self.setCentralWidget(self.image_label)

app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()
