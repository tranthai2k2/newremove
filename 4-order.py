import sys
import os
import json
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTableWidget, QTableWidgetItem, 
                             QComboBox, QPushButton, QLineEdit, QFileDialog, 
                             QHeaderView, QLabel, QMessageBox)
from PyQt6.QtGui import QColor, QPixmap
from PyQt6.QtCore import Qt, QTimer

class ExcelLikeOrderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Quản Lý Order Ảnh Lora (Tự Động Ảnh & Triggers)")
        self.resize(1400, 800) # Tăng thêm chiều rộng để chứa 2 cột mới
        
        # Đường dẫn thư mục Lora
        self.lora_dir = r"E:\webui_forge_cu121_torch231\webui\models\Lora"
        
        self.lora_data = self.load_loras_info()
        self.lora_names = list(self.lora_data.keys())
        self.lora_names.sort() 
        
        self.setup_ui()
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_status_colors)
        self.timer.start(2000)

    def load_loras_info(self):
        data = {}
        valid_model_exts = {'.safetensors', '.pt', '.ckpt'}
        valid_img_exts = ['.png', '.jpg', '.jpeg', '.webp', '.preview.png']
        
        if not os.path.exists(self.lora_dir):
            return data

        for root, dirs, files in os.walk(self.lora_dir):
            for file in files:
                name, ext = os.path.splitext(file)
                if ext.lower() in valid_model_exts:
                    img_path = None
                    triggers = ""
                    
                    for img_ext in valid_img_exts:
                        potential_path = os.path.join(root, name + img_ext)
                        if os.path.exists(potential_path):
                            img_path = potential_path
                            break
                        if img_ext == '.png':
                            potential_path_preview = os.path.join(root, name + ".preview.png")
                            if os.path.exists(potential_path_preview):
                                img_path = potential_path_preview
                                break
                    
                    json_path = os.path.join(root, name + ".json")
                    if os.path.exists(json_path):
                        try:
                            with open(json_path, 'r', encoding='utf-8') as f:
                                jdata = json.load(f)
                                if "trainedWords" in jdata and isinstance(jdata["trainedWords"], list):
                                    triggers = ", ".join(jdata["trainedWords"])
                                elif "activation_text" in jdata:
                                    triggers = jdata["activation_text"]
                        except Exception:
                            pass
                            
                    data[name] = {"image": img_path, "triggers": triggers}
        return data

    def setup_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        btn_layout = QHBoxLayout()
        self.btn_add_row = QPushButton("+ Thêm Order Mới")
        self.btn_add_row.setFixedSize(150, 40)
        self.btn_add_row.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.btn_add_row.clicked.connect(self.add_row)
        btn_layout.addWidget(self.btn_add_row)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Bảng giờ đây có 9 cột
        self.table = QTableWidget(0, 9)
        self.table.setHorizontalHeaderLabels([
            "Nhân vật / Lora", "Ảnh Preview", "Giá tiền", "Yêu cầu (Triggers)", 
            "Số ảnh yêu cầu", "Folder ảnh Order", "Tiến độ (Auto)", "Trạng thái Order", "Hành động"
        ])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed) 
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.Fixed)
        
        self.table.setColumnWidth(0, 180)
        self.table.setColumnWidth(1, 200) 
        self.table.setColumnWidth(8, 80) # Cột Nút Xoá
        
        layout.addWidget(self.table)
        self.add_row()

    def add_row(self):
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        self.table.setRowHeight(row, 200)
        
        # 0. Lora
        combo_lora = QComboBox()
        combo_lora.setEditable(True) 
        combo_lora.addItems(["-- Chọn Lora --"] + self.lora_names)
        self.table.setCellWidget(row, 0, combo_lora)
        
        # 1. Ảnh preview
        lbl_img = QLabel("No Image")
        lbl_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_img.setStyleSheet("border: 1px solid #ddd;")
        self.table.setCellWidget(row, 1, lbl_img)
        
        combo_lora.currentTextChanged.connect(lambda text, r=row: self.update_lora_data(r, text))
        
        # 2. Giá tiền
        combo_price = QComboBox()
        combo_price.addItems(["20k", "50k", "100k"])
        self.table.setCellWidget(row, 2, combo_price)
        
        # 3. Yêu cầu
        item_req = QTableWidgetItem("")
        self.table.setItem(row, 3, item_req)
        
        # 4. Số ảnh
        item_count = QTableWidgetItem("0")
        item_count.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 4, item_count)
        
        # 5. Folder
        folder_widget = QWidget()
        folder_layout = QHBoxLayout(folder_widget)
        folder_layout.setContentsMargins(5, 2, 5, 2)
        txt_path = QLineEdit()
        txt_path.setPlaceholderText("Chọn folder...")
        btn_browse = QPushButton("📁")
        btn_browse.setFixedWidth(35)
        btn_browse.clicked.connect(lambda _, t=txt_path: self.browse_folder(t))
        folder_layout.addWidget(txt_path)
        folder_layout.addWidget(btn_browse)
        self.table.setCellWidget(row, 5, folder_widget)
        
        # 6. Tiến độ sinh ảnh tự động
        item_status = QTableWidgetItem("Chưa có folder")
        item_status.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        item_status.setFlags(item_status.flags() ^ Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, 6, item_status)
        
        # 7. Trạng thái Order (Dropdown: Chưa xong, Đến hẹn, Done)
        combo_order_status = QComboBox()
        combo_order_status.addItems(["Chưa xong", "Đến hẹn", "Done"])
        combo_order_status.currentTextChanged.connect(
            lambda text, cb=combo_order_status: self.style_status_combobox(cb, text)
        )
        self.style_status_combobox(combo_order_status, "Chưa xong") # Set màu mặc định ban đầu
        self.table.setCellWidget(row, 7, combo_order_status)

        # 8. Cột Hành động (Nút Xoá)
        btn_delete = QPushButton("Xóa ✖")
        btn_delete.setStyleSheet("background-color: #ff4d4d; color: white; font-weight: bold; border-radius: 4px; padding: 5px;")
        btn_delete.clicked.connect(lambda checked, w=btn_delete: self.delete_row(w))
        
        # Đặt nút xoá vào một layout để căn giữa
        del_widget = QWidget()
        del_layout = QHBoxLayout(del_widget)
        del_layout.setContentsMargins(5, 5, 5, 5)
        del_layout.addWidget(btn_delete)
        self.table.setCellWidget(row, 8, del_widget)

    def style_status_combobox(self, combobox, text):
        """Đổi màu Dropdown trạng thái dựa trên lựa chọn"""
        if text == "Done":
            combobox.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;") # Xanh lá
        elif text == "Đến hẹn":
            combobox.setStyleSheet("background-color: #FF9800; color: white; font-weight: bold;") # Cam cảnh báo
        else:
            combobox.setStyleSheet("background-color: #f1f1f1; color: black;") # Mặc định xám nhạt

    def delete_row(self, widget):
        """Hàm xử lý xóa dòng có xác nhận"""
        # Tìm vị trí của nút được bấm để suy ra index của hàng
        index = self.table.indexAt(widget.parent().pos())
        if index.isValid():
            row = index.row()
            # Hộp thoại xác nhận xóa
            reply = QMessageBox.question(self, 'Xóa Order', 'Bạn có chắc chắn muốn xóa Order này không?',
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                         QMessageBox.StandardButton.No)
            
            if reply == QMessageBox.StandardButton.Yes:
                self.table.removeRow(row)

    def update_lora_data(self, row, lora_name):
        lbl_img = self.table.cellWidget(row, 1)
        item_req = self.table.item(row, 3)
        
        lora_info = self.lora_data.get(lora_name, {"image": None, "triggers": ""})
        img_path = lora_info["image"]
        triggers = lora_info["triggers"]
        
        if img_path and os.path.exists(img_path) and lbl_img:
            pixmap = QPixmap(img_path)
            scaled_pixmap = pixmap.scaled(190, 190, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            lbl_img.setPixmap(scaled_pixmap)
            lbl_img.setText("") 
        elif lbl_img:
            lbl_img.clear()
            lbl_img.setText("No Image")
            
        if item_req and triggers:
            if not item_req.text().strip():
                item_req.setText(triggers)

    def browse_folder(self, line_edit):
        folder_path = QFileDialog.getExistingDirectory(self, "Chọn Folder Ảnh Order")
        if folder_path:
            line_edit.setText(folder_path)
            self.update_status_colors()

    def count_images_in_folder(self, folder_path):
        if not folder_path or not os.path.isdir(folder_path):
            return 0
        valid_extensions = {'.png', '.jpg', '.jpeg', '.webp'}
        count = 0
        try:
            for f in os.listdir(folder_path):
                if os.path.splitext(f)[1].lower() in valid_extensions:
                    count += 1
        except Exception:
            pass
        return count

    def update_status_colors(self):
        for row in range(self.table.rowCount()):
            item_target = self.table.item(row, 4) 
            target_count = int(item_target.text()) if item_target and item_target.text().isdigit() else 0
            
            folder_widget = self.table.cellWidget(row, 5)
            folder_path = folder_widget.findChild(QLineEdit).text().strip() if folder_widget else ""
            
            item_status = self.table.item(row, 6)
            if not item_status: continue

            if folder_path and os.path.isdir(folder_path):
                actual_count = self.count_images_in_folder(folder_path)
                item_status.setText(f"{actual_count} / {target_count}")
                
                if actual_count >= target_count and target_count > 0:
                    item_status.setBackground(QColor(144, 238, 144))
                else:
                    item_status.setBackground(QColor(255, 182, 193))
            else:
                item_status.setText("Chưa có folder")
                item_status.setBackground(QColor(255, 255, 255))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = ExcelLikeOrderApp()
    window.show()
    sys.exit(app.exec())