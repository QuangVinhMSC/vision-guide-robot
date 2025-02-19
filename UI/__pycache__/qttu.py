# import sys

# from PySide6.QtCore import Qt
# from PySide6.QtWidgets import QApplication, QLabel, QMainWindow

# class MainWindow(QMainWindow):
#     def __init__(self):
#         super().__init__()
#         self.label = QLabel("Click in this window")
#         self.setCentralWidget(self.label)

#     def mousePressEvent(self, e):
#         if e.button() == Qt.MouseButton.LeftButton:
#             # handle the left-button press in here
#             self.label.setText("mousePressEvent LEFT")

#         elif e.button() == Qt.MouseButton.MiddleButton:
#             # handle the middle-button press in here.
#             self.label.setText("mousePressEvent MIDDLE")

#         elif e.button() == Qt.MouseButton.RightButton:
#             # handle the right-button press in here.
#             self.label.setText("mousePressEvent RIGHT")

#     def mouseReleaseEvent(self, e):
#         if e.button() == Qt.MouseButton.LeftButton:
#             self.label.setText("mouseReleaseEvent LEFT")

#         elif e.button() == Qt.MouseButton.MiddleButton:
#             self.label.setText("mouseReleaseEvent MIDDLE")

#         elif e.button() == Qt.MouseButton.RightButton:
#             self.label.setText("mouseReleaseEvent RIGHT")

#     def mouseDoubleClickEvent(self, e):
#         if e.button() == Qt.MouseButton.LeftButton:
#             self.label.setText("mouseDoubleClickEvent LEFT")

#         elif e.button() == Qt.MouseButton.MiddleButton:
#             self.label.setText("mouseDoubleClickEvent MIDDLE")

#         elif e.button() == Qt.MouseButton.RightButton:
#             self.label.setText("mouseDoubleClickEvent RIGHT")

# app = QApplication(sys.argv)

# window = MainWindow()
# window.show()

# app.exec()



# import sys

# from PySide6.QtWidgets import (
#     QApplication,
#     QCheckBox,
#     QComboBox,
#     QDateEdit,
#     QDateTimeEdit,
#     QDial,
#     QDoubleSpinBox,
#     QFontComboBox,
#     QLabel,
#     QLCDNumber,
#     QLineEdit,
#     QMainWindow,
#     QProgressBar,
#     QPushButton,
#     QRadioButton,
#     QSlider,
#     QSpinBox,
#     QTimeEdit,
#     QVBoxLayout,
#     QWidget,
# )

# class MainWindow(QMainWindow):
#     def __init__(self):
#         super().__init__()

#         self.setWindowTitle("Widgets App")

#         layout = QVBoxLayout()
#         widgets = [
#             QCheckBox,
#             QComboBox,
#             QDateEdit,
#             QDateTimeEdit,
#             QDial,
#             QDoubleSpinBox,
#             QFontComboBox,
#             QLCDNumber,
#             QLabel,
#             QLineEdit,
#             QProgressBar,
#             QPushButton,
#             QRadioButton,
#             QSlider,
#             QSpinBox,
#             QTimeEdit,
#         ]

#         for widget in widgets:
#             layout.addWidget(widget())

#         central_widget = QWidget()
#         central_widget.setLayout(layout)

#         self.setCentralWidget(central_widget)

# app = QApplication(sys.argv)
# window = MainWindow()
# window.show()
# app.exec()



# import sys
# from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout,QHBoxLayout,QGridLayout
# from PySide6.QtGui import QPalette, QColor

# class MainWindow(QMainWindow):
#     def __init__(self):
#         super().__init__()

#         self.setWindowTitle("My App")

#         layout = QGridLayout()

#         layout.addWidget(Color('red'), 0, 0)
#         layout.addWidget(Color('green'), 1, 0)
#         layout.addWidget(Color('blue'), 1, 1)
#         layout.addWidget(Color('purple'), 2, 1)

#         widget = QWidget()
#         widget.setLayout(layout)
#         self.setCentralWidget(widget)
# class Color(QWidget):
#     def __init__(self, color):
#         super().__init__()
#         self.setAutoFillBackground(True)

#         palette = self.palette()
#         palette.setColor(QPalette.Window, QColor(color))
#         self.setPalette(palette)

# app = QApplication(sys.argv)
# window = MainWindow()
# window.show()
# app.exec()






import sys
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()

        self.label = QtWidgets.QLabel()
        canvas = QtGui.QPixmap(400, 300)
        canvas.fill(Qt.white)
        self.label.setPixmap(canvas)
        self.setCentralWidget(self.label)

        self.last_x, self.last_y = None, None

    def mouseMoveEvent(self, e):
        if self.last_x is None: # First event.
            self.last_x = e.x()
            self.last_y = e.y()
            return # Ignore the first time.

        pixmap = self.label.pixmap()
        painter = QtGui.QPainter(pixmap)
        painter.drawLine(self.last_x, self.last_y, e.x(), e.y())
        painter.end()
        self.label.setPixmap(pixmap)

        # Update the origin for next time.
        self.last_x = e.x()
        self.last_y = e.y()

    def mouseReleaseEvent(self, e):
        self.last_x = None
        self.last_y = None


app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()