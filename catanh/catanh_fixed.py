import sys, io, json
from pathlib import Path
from typing import Optional

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFileDialog, QListWidget, QListWidgetItem,
    QGraphicsView, QGraphicsScene, QGraphicsEllipseItem, QGraphicsLineItem,
    QGraphicsRectItem, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMessageBox,
    QSplitter, QShortcut, QFrame
)
from PyQt5.QtGui import (
    QPixmap, QPen, QBrush, QPainter, QCursor, QIcon, QFont, QColor
)
from PyQt5.QtCore import Qt, QRectF, QPointF, QSize
from PIL import Image, ImageDraw

SUPPORTED = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}
OUTPUT_DIRNAME = "_poly_output"
THUMB = 96
SETTINGS_PATH = Path(__file__).with_name("settings.json")

# Modern color palette
COLORS = {
    'primary': '#2563eb',      # Blue
    'primary_hover': '#1d4ed8',
    'success': '#10b981',      # Green
    'danger': '#ef4444',       # Red
    'warning': '#f59e0b',      # Orange
    'bg_dark': '#1e293b',      # Dark slate
    'bg_medium': '#334155',    # Medium slate
    'bg_light': '#f8fafc',     # Light
    'text_dark': '#0f172a',
    'text_light': '#e2e8f0',
    'border': '#cbd5e1'
}

STYLESHEET = f"""
QMainWindow {{
    background-color: {COLORS['bg_light']};
}}

QLabel {{
    color: {COLORS['text_dark']};
    font-size: 13px;
    font-weight: 600;
    padding: 8px 4px;
}}

QListWidget {{
    background-color: white;
    border: 2px solid {COLORS['border']};
    border-radius: 8px;
    padding: 4px;
    outline: none;
}}

QListWidget::item {{
    padding: 8px;
    border-radius: 6px;
    margin: 2px;
}}

QListWidget::item:selected {{
    background-color: {COLORS['primary']};
    color: white;
}}

QListWidget::item:hover {{
    background-color: #e0e7ff;
}}

QPushButton {{
    background-color: {COLORS['primary']};
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 13px;
    font-weight: 600;
    min-height: 36px;
}}

QPushButton:hover {{
    background-color: {COLORS['primary_hover']};
}}

QPushButton:pressed {{
    background-color: #1e40af;
}}

QPushButton:checked {{
    background-color: #1e40af;
    border: 2px solid white;
}}

QPushButton#btnOpen {{
    background-color: {COLORS['success']};
}}

QPushButton#btnOpen:hover {{
    background-color: #059669;
}}

QPushButton#btnRect {{
    background-color: {COLORS['warning']};
}}

QPushButton#btnRect:hover {{
    background-color: #d97706;
}}

QPushButton#btnClear {{
    background-color: {COLORS['danger']};
}}

QPushButton#btnClear:hover {{
    background-color: #dc2626;
}}

QGraphicsView {{
    background-color: #f1f5f9;
    border: 2px solid {COLORS['border']};
    border-radius: 8px;
}}

QSplitter::handle {{
    background-color: {COLORS['border']};
    width: 2px;
}}

QFrame#sidePanel {{
    background-color: white;
    border-radius: 8px;
    padding: 8px;
}}
"""

class PolygonScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pix_item: Optional[QGraphicsRectItem] = None
        self.border_item: Optional[QGraphicsRectItem] = None
        self.rect_item: Optional[QGraphicsRectItem] = None
        self.rect_mode = self.dragging = False
        self.rect_start = QPointF()
        self.reset_polygon(False)

    def set_pixmap(self, pix: QPixmap):
        self.clear()
        self.pix_item = self.addPixmap(pix)
        w, h = pix.width(), pix.height()
        self.border_item = self.addRect(QRectF(0, 0, w, h), QPen(QColor('#94a3b8'), 2))
        self.border_item.setZValue(-1)
        self.img_w, self.img_h = w, h
        self.reset_polygon(False)

    def reset_polygon(self, erase=True):
        if erase:
            for item in getattr(self, "dot_items", []) + getattr(self, "line_items", []):
                self.removeItem(item)
            if self.rect_item:
                self.removeItem(self.rect_item)
            self.rect_item = None
        self.points, self.dot_items, self.line_items = [], [], []
        self.finished = False

    clear_polygon = reset_polygon

    def enable_rect(self, enable: bool):
        if enable == self.rect_mode:
            return
        self.rect_mode = enable
        self.dragging = False
        if enable:
            QApplication.setOverrideCursor(QCursor(Qt.CrossCursor))
        else:
            QApplication.restoreOverrideCursor()
            if self.rect_item:
                self.removeItem(self.rect_item)
                self.rect_item = None

    def mousePressEvent(self, e):
        if not self.pix_item:
            return
        
        p = e.scenePos()
        # Kiểm tra click ngoài vùng ảnh
        outside = not (0 <= p.x() < self.img_w and 0 <= p.y() < self.img_h)
        
        if self.rect_mode:
            if outside:
                # Click ngoài ảnh trong chế độ rectangle => xóa đa giác
                self.reset_polygon(True)
            else:
                self.dragging, self.rect_start = True, e.scenePos()
                self.rect_item = QGraphicsRectItem()
                self.rect_item.setPen(QPen(QColor(COLORS['primary']), 3, Qt.DashLine))
                self.addItem(self.rect_item)
        elif not self.finished:
            if outside:
                # Click ngoài ảnh trong chế độ đa giác => xóa đa giác
                self.reset_polygon(True)
            else:
                self._add_point(p)

    def mouseMoveEvent(self, e):
        if self.rect_mode and self.dragging and self.rect_item:
            end = e.scenePos()
            end.setX(min(max(end.x(), 0), self.img_w))
            end.setY(min(max(end.y(), 0), self.img_h))
            if QApplication.keyboardModifiers() & Qt.ShiftModifier:
                d = end - self.rect_start
                s = max(abs(d.x()), abs(d.y()))
                end = QPointF(
                    self.rect_start.x() + s * (1 if d.x() >= 0 else -1),
                    self.rect_start.y() + s * (1 if d.y() >= 0 else -1),
                )
                end.setX(min(max(end.x(), 0), self.img_w))
                end.setY(min(max(end.y(), 0), self.img_h))
            self.rect_item.setRect(QRectF(self.rect_start, end).normalized())
        else:
            super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        if self.rect_mode and self.dragging:
            self.dragging = False
            if self.rect_item and self.rect_item.rect().width() > 5:
                self._rect_to_polygon(self.rect_item.rect())
            if self.rect_item:
                self.removeItem(self.rect_item)
            self.rect_item = None
            self.enable_rect(False)

    def _add_point(self, p: QPointF):
        r = 5
        col = QColor(COLORS['success']) if not self.points else QColor(COLORS['danger'])
        dot = QGraphicsEllipseItem(p.x() - r, p.y() - r, r * 2, r * 2)
        dot.setBrush(QBrush(col))
        dot.setPen(QPen(QColor('white'), 2))
        self.addItem(dot)
        self.dot_items.append(dot)

        if self.points:
            last = self.points[-1]
            line = QGraphicsLineItem(last.x(), last.y(), p.x(), p.y())
            line.setPen(QPen(QColor(COLORS['warning']), 3))
            self.addItem(line)
            self.line_items.append(line)

        self.points.append(p)

    def _rect_to_polygon(self, rect: QRectF):
        self.clear_polygon(True)
        for p in (rect.topLeft(), rect.topRight(), rect.bottomRight(), rect.bottomLeft()):
            self._add_point(p)
        self.close_polygon()

    def close_polygon(self):
        if self.finished or len(self.points) < 3:
            return
        first, last = self.points[0], self.points[-1]
        line = QGraphicsLineItem(last.x(), last.y(), first.x(), first.y())
        line.setPen(QPen(QColor(COLORS['warning']), 3))
        self.addItem(line)
        self.line_items.append(line)
        for idx in (0, -1):
            self.dot_items[idx].setBrush(QBrush(QColor(COLORS['primary'])))
            self.dot_items[idx].setPen(QPen(QColor('white'), 2))
        self.finished = True

    def undo_point(self):
        if self.finished or not self.points:
            return
        self.removeItem(self.dot_items.pop())
        if self.line_items:
            self.removeItem(self.line_items.pop())
        self.points.pop()

    def polygon_xy(self):
        return [(int(p.x()), int(p.y())) for p in self.points]

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎨 Polygon Tool - Trích xuất vùng ảnh")
        self.setStyleSheet(STYLESHEET)
        self.folder = self.out_dir = self.cur_path = None

        # Left panel - Source images
        left_frame = QFrame()
        left_frame.setObjectName("sidePanel")
        ll = QVBoxLayout(left_frame)
        
        label_src = QLabel("📁 Ảnh gốc")
        label_src.setStyleSheet(f"font-size: 15px; color: {COLORS['text_dark']};")
        
        self.list_src = QListWidget()
        self.list_src.setIconSize(QSize(THUMB, THUMB))
        self.list_src.setUniformItemSizes(True)
        self.list_src.itemSelectionChanged.connect(self._load_src)
        
        ll.addWidget(label_src)
        ll.addWidget(self.list_src)
        ll.setContentsMargins(8, 8, 8, 8)

        # Center panel - Graphics view and controls
        center = QWidget()
        cl = QVBoxLayout(center)
        
        self.scene = PolygonScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.view.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Control buttons
        btn_layout = QHBoxLayout()
        
        btn_open = QPushButton("📂 Mở thư mục")
        btn_open.setObjectName("btnOpen")
        btn_open.setToolTip("Ctrl+O")
        
        btn_rect = QPushButton("▭ Rectangle")
        btn_rect.setObjectName("btnRect")
        btn_rect.setToolTip("M")
        btn_rect.setCheckable(True)
        
        btn_polygon = QPushButton("⬡ Đa giác")
        btn_polygon.setToolTip("N")
        btn_polygon.setCheckable(True)
        btn_polygon.setChecked(True)  # Mặc định chọn đa giác
        
        btn_full = QPushButton("⬚ Toàn ảnh")
        btn_full.setToolTip("Ctrl+A")
        
        btn_clear = QPushButton("🗑 Xóa đa giác")
        btn_clear.setObjectName("btnClear")
        btn_clear.setToolTip("Del")
        
        btn_export = QPushButton("💾 Xuất PNG")
        btn_export.setToolTip("Enter")
        
        for btn in [btn_open, btn_rect, btn_polygon, btn_full, btn_clear, btn_export]:
            btn_layout.addWidget(btn)
        btn_layout.addStretch()
        
        cl.addWidget(self.view)
        cl.addLayout(btn_layout)
        cl.setContentsMargins(8, 8, 8, 8)

        # Right panel - Output images
        right_frame = QFrame()
        right_frame.setObjectName("sidePanel")
        rl = QVBoxLayout(right_frame)
        
        # Header với nút mở folder
        out_header = QHBoxLayout()
        label_out = QLabel("✅ Ảnh đã tạo")
        label_out.setStyleSheet(f"font-size: 15px; color: {COLORS['text_dark']};")
        
        btn_open_output = QPushButton("📁")
        btn_open_output.setObjectName("btnOpen")
        btn_open_output.setToolTip("Mở folder đã cắt")
        btn_open_output.setMaximumWidth(50)
        btn_open_output.clicked.connect(self._open_output_folder)
        
        out_header.addWidget(label_out)
        out_header.addStretch()
        out_header.addWidget(btn_open_output)
        
        self.list_out = QListWidget()
        self.list_out.setIconSize(QSize(THUMB, THUMB))
        self.list_out.setUniformItemSizes(True)
        self.list_out.itemDoubleClicked.connect(self._preview_out)
        
        rl.addLayout(out_header)
        rl.addWidget(self.list_out)
        rl.setContentsMargins(8, 8, 8, 8)

        # Connect buttons
        btn_open.clicked.connect(self._open_folder)
        btn_rect.clicked.connect(lambda checked: self._toggle_mode('rect', checked, btn_rect, btn_polygon))
        btn_polygon.clicked.connect(lambda checked: self._toggle_mode('polygon', checked, btn_rect, btn_polygon))
        btn_full.clicked.connect(self._select_full)
        btn_clear.clicked.connect(lambda: self.scene.reset_polygon(True))
        btn_export.clicked.connect(self._export_png)

        # Shortcuts
        QShortcut("Ctrl+O", self, self._open_folder)
        QShortcut("M", self, lambda: self._activate_rect_mode(btn_rect, btn_polygon))
        QShortcut("N", self, lambda: self._activate_polygon_mode(btn_rect, btn_polygon))
        QShortcut("Ctrl+A", self, self._select_full)
        QShortcut(Qt.Key_Delete, self, lambda: self.scene.reset_polygon(True))
        QShortcut(Qt.Key_Return, self, self._export_png, context=Qt.ApplicationShortcut)
        QShortcut(Qt.Key_Enter, self, self._export_png, context=Qt.ApplicationShortcut)
        QShortcut("Ctrl+Z", self, self.scene.undo_point)
        QShortcut(Qt.Key_Escape, self, lambda: self.scene.enable_rect(False))

        # Main splitter
        splitter = QSplitter()
        splitter.addWidget(left_frame)
        splitter.addWidget(center)
        splitter.addWidget(right_frame)
        splitter.setSizes([280, 900, 280])

        self.setCentralWidget(splitter)
        self.resize(1600, 900)  # Kích thước cửa sổ lớn hơn
        self._load_last_folder()

    def _toggle_mode(self, mode, checked, btn_rect, btn_polygon):
        """Toggle between rectangle and polygon modes"""
        if mode == 'rect':
            if checked:
                btn_polygon.setChecked(False)
                self.scene.enable_rect(True)
            else:
                # Không cho bỏ chọn, phải chuyển sang mode khác
                btn_rect.setChecked(True)
        else:  # polygon
            if checked:
                btn_rect.setChecked(False)
                self.scene.enable_rect(False)
            else:
                # Không cho bỏ chọn, phải chuyển sang mode khác
                btn_polygon.setChecked(True)
    
    def _activate_rect_mode(self, btn_rect, btn_polygon):
        """Activate rectangle mode via shortcut"""
        btn_rect.setChecked(True)
        btn_polygon.setChecked(False)
        self.scene.enable_rect(True)
    
    def _activate_polygon_mode(self, btn_rect, btn_polygon):
        """Activate polygon mode via shortcut"""
        btn_polygon.setChecked(True)
        btn_rect.setChecked(False)
        self.scene.enable_rect(False)

    def _open_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Chọn thư mục ảnh", str(self.folder) if self.folder else "")
        if folder:
            self.folder = Path(folder)
            self.out_dir = self.folder / OUTPUT_DIRNAME
            self._build_src_list()
            self._build_out_list()
            self._save_last_folder()

    def _open_output_folder(self):
        """Mở thư mục chứa ảnh đã xuất trong file explorer"""
        if not self.out_dir:
            QMessageBox.information(self, "Thông báo", "Chưa có thư mục output. Vui lòng mở thư mục ảnh và xuất ảnh trước.")
            return
        
        if not self.out_dir.exists():
            QMessageBox.information(self, "Thông báo", "Thư mục output chưa tồn tại. Vui lòng xuất ảnh trước.")
            return
        
        # Mở thư mục trong file explorer tùy theo hệ điều hành
        import subprocess
        import platform
        
        try:
            if platform.system() == 'Windows':
                subprocess.run(['explorer', str(self.out_dir)])
            elif platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', str(self.out_dir)])
            else:  # Linux
                subprocess.run(['xdg-open', str(self.out_dir)])
        except Exception as e:
            QMessageBox.warning(self, "Lỗi", f"Không thể mở thư mục: {e}")

    def _build_src_list(self):
        self.list_src.clear()
        if not self.folder: return
        for f in sorted(self.folder.iterdir()):
            if f.suffix.lower() not in SUPPORTED: continue
            item = QListWidgetItem(f.stem)
            thumb = QPixmap(str(f)).scaled(THUMB, THUMB, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            item.setIcon(QIcon(thumb))
            self.list_src.addItem(item)
        if self.list_src.count():
            self.list_src.setCurrentRow(0)

    def _build_out_list(self):
        self.list_out.clear()
        if not self.out_dir or not self.out_dir.exists(): return
        for f in sorted(self.out_dir.glob("*.png"), key=lambda p: p.stat().st_mtime, reverse=True):
            item = QListWidgetItem(f.name)
            icon = QPixmap(str(f)).scaled(THUMB, THUMB, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            item.setIcon(QIcon(icon))
            item.setData(Qt.UserRole, str(f))
            self.list_out.addItem(item)

    def _save_last_folder(self):
        try:
            SETTINGS_PATH.write_text(json.dumps({"last_folder": str(self.folder)}))
        except Exception:
            pass

    def _load_last_folder(self):
        try:
            data = json.loads(SETTINGS_PATH.read_text())
            last = Path(data.get("last_folder", ""))
            if last.is_dir():
                self.folder, self.out_dir = last, last / OUTPUT_DIRNAME
                self._build_src_list()
                self._build_out_list()
        except Exception:
            pass

    def _load_src(self):
        if not self.folder or not self.list_src.currentItem(): return
        stem = self.list_src.currentItem().text()
        file = next(self.folder.glob(f"{stem}.*"))
        pix = QPixmap(str(file))
        if not pix.isNull():
            self.scene.set_pixmap(pix)
            self.scene.setSceneRect(QRectF(pix.rect()))
            self.view.fitInView(QRectF(pix.rect()), Qt.KeepAspectRatio)
            self.cur_path = file
            self.list_src.setFocus()

    def _select_full(self):
        if not self.scene.pix_item: return
        self.scene.clear_polygon()
        w, h = self.scene.img_w, self.scene.img_h
        for p in (QPointF(0,0), QPointF(w,0), QPointF(w,h), QPointF(0,h)):
            self.scene._add_point(p)
        self.scene.close_polygon()

    def _preview_out(self, item):
        path = item.data(Qt.UserRole)
        if not path: return
        dlg = QMainWindow(self)
        dlg.setWindowTitle(f"👁 {item.text()}")
        lbl = QLabel()
        lbl.setPixmap(QPixmap(path))
        dlg.setCentralWidget(lbl)
        dlg.resize(800, 600)
        dlg.show()

    def _export_png(self):
        sc = self.scene
        if not sc.points or not self.cur_path: return
        if not sc.finished:
            sc.close_polygon()
        try:
            img = Image.open(self.cur_path).convert("RGBA")
            mask = Image.new("L", img.size, 0)
            ImageDraw.Draw(mask).polygon(sc.polygon_xy(), fill=255)
            res = Image.new("RGBA", img.size)
            res.paste(img, (0, 0), mask)
            bbox = mask.getbbox()
            if bbox: res = res.crop(bbox)

            self.out_dir.mkdir(exist_ok=True)
            out_path = self.out_dir / f"{self.cur_path.stem}_poly.png"
            res.save(out_path)

            item = QListWidgetItem(out_path.name)
            icon = QPixmap(str(out_path)).scaled(THUMB, THUMB, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            item.setIcon(QIcon(icon))
            item.setData(Qt.UserRole, str(out_path))
            self.list_out.insertItem(0, item)

            self.list_src.setFocus()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", str(e))
        finally:
            sc.reset_polygon()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()  # Thay showMaximized() bằng show() để dùng kích thước tùy chỉnh
    sys.exit(app.exec_())