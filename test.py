import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, 
    QVBoxLayout, QHBoxLayout, QSpinBox, 
    QLabel, QScrollArea, QPushButton,
    QMessageBox, QGridLayout
)
from PySide6.QtCore import Qt

class BoxDisplayWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.grid_layout = QGridLayout(self)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.setLayout(self.grid_layout)
        self.rows = []  # Lưu trữ các hàng để thao tác sau này
        
    def update_rows(self, row_count):
        # Xóa các hàng hiện tại
        for row in self.rows:
            for widget in row:
                self.grid_layout.removeWidget(widget)
                widget.deleteLater()
        self.rows.clear()
        
        # Thêm các hàng mới (mỗi hàng gồm 1 label + 2 spinbox)
        for row_idx in range(row_count):
            row_widgets = []
            
            # Box 1: Label chỉ số thứ tự
            label = QLabel(f"Hàng {row_idx + 1}")
            self.grid_layout.addWidget(label, row_idx, 0)
            row_widgets.append(label)
            
            # Box 2: SpinBox thứ nhất
            spinbox1 = QSpinBox()
            spinbox1.setRange(0, 1000)
            spinbox1.setValue((row_idx + 1) * 10)
            self.grid_layout.addWidget(spinbox1, row_idx, 1)
            row_widgets.append(spinbox1)
            
            # Box 3: SpinBox thứ hai
            spinbox2 = QSpinBox()
            spinbox2.setRange(0, 1000)
            spinbox2.setValue((row_idx + 1) * 20)
            self.grid_layout.addWidget(spinbox2, row_idx, 2)
            row_widgets.append(spinbox2)
            
            self.rows.append(row_widgets)
    
    def get_spinbox_style(self, bg_color):
        return f"""
            QSpinBox {{
                background-color: {bg_color};
                color: white;
                font-weight: bold;
                padding: 10px;
                margin: 5px;
                border-radius: 5px;
                min-width: 80px;
                text-align: center;
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                width: 20px;
            }}
        """
    
    def get_all_values(self):
        """Lấy tất cả giá trị dưới dạng list[tuple] mỗi tuple là 2 giá trị spinbox"""
        return [(row[1].value(), row[2].value()) for row in self.rows]

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("3 Box Mỗi Hàng")
        self.setGeometry(100, 100, 800, 400)
        
        # Tạo widget chính
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        
        # Tạo control để nhập số lượng hàng
        control_layout = QHBoxLayout()
        self.row_spinbox = QSpinBox()
        self.row_spinbox.setRange(1, 100)  # Giới hạn từ 1-100 hàng
        self.row_spinbox.setValue(3)       # Giá trị mặc định
        self.row_spinbox.valueChanged.connect(self.update_row_display)
        
        # Nút để hiển thị các giá trị hiện tại
        self.show_values_btn = QPushButton("Hiển thị giá trị")
        self.show_values_btn.clicked.connect(self.show_current_values)
        
        control_layout.addWidget(QLabel("Số lượng hàng:"))
        control_layout.addWidget(self.row_spinbox)
        control_layout.addWidget(self.show_values_btn)
        control_layout.addStretch()
        
        # Tạo scroll area để hiển thị nhiều hàng khi cần
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        # Tạo widget hiển thị các hàng
        self.box_display = BoxDisplayWidget()
        scroll_area.setWidget(self.box_display)
        
        # Cập nhật lần đầu
        self.update_row_display(self.row_spinbox.value())
        
        # Thêm các widget vào layout chính
        main_layout.addLayout(control_layout)
        main_layout.addWidget(scroll_area)
        
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
    
    def update_row_display(self, row_count):
        self.box_display.update_rows(row_count)
    
    def show_current_values(self):
        """Hiển thị các giá trị hiện tại của các box"""
        values = self.box_display.get_all_values()
        values_str = "\n".join([f"Hàng {i+1}: {val1}, {val2}" 
                              for i, (val1, val2) in enumerate(values)])
        
        QMessageBox.information(
            self, 
            "Giá trị hiện tại", 
            f"Các giá trị trong các hàng:\n{values_str}"
        )

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())