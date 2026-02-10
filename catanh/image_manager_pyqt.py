import sys
import json
import re
from pathlib import Path
from typing import List
from concurrent.futures import ThreadPoolExecutor

from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
import cv2
import numpy as np

class FlowLayout(QLayout):
    """Custom flow layout for arranging widgets in grid"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.item_list = []
        self.spacing = 10
        
    def addItem(self, item):
        self.item_list.append(item)
        
    def count(self):
        return len(self.item_list)
        
    def itemAt(self, index):
        return self.item_list[index] if 0 <= index < len(self.item_list) else None
        
    def takeAt(self, index):
        return self.item_list.pop(index) if 0 <= index < len(self.item_list) else None
        
    def setGeometry(self, rect):
        super().setGeometry(rect)
        self.do_layout(rect, False)
        
    def sizeHint(self):
        return self.minimumSize()
        
    def minimumSize(self):
        size = QSize()
        for item in self.item_list:
            size = size.expandedTo(item.minimumSize())
        return QSize(300, 200)
        
    def do_layout(self, rect, test_only):
        x = rect.x()
        y = rect.y()
        line_height = 0
        
        for item in self.item_list:
            widget = item.widget()
            space_x = self.spacing
            space_y = self.spacing
            
            next_x = x + item.sizeHint().width() + space_x
            if next_x - space_x > rect.right() and line_height > 0:
                x = rect.x()
                y = y + line_height + space_y
                next_x = x + item.sizeHint().width() + space_x
                line_height = 0
                
            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))
                
            x = next_x
            line_height = max(line_height, item.sizeHint().height())
            
        return y + line_height - rect.y()

class ImageItem:
    __slots__ = ('path', 'idx', 'orig_idx', 'thumbnail')
    
    def __init__(self, path: Path, idx: int):
        self.path = path
        self.idx = idx
        self.orig_idx = idx
        self.thumbnail = None

class UltraFastGallery(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("⚡ Ultra Fast Image Sorter")
        self.setGeometry(100, 100, 1600, 900)
        
        self.items: List[ImageItem] = []
        self.current_folder = None
        self.dirty = False
        self.thumb_size = QSize(120, 120)
        
        self.init_ui()
        self.load_last_folder()
    
    def init_ui(self):
        # Main widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Control panel
        control_panel = QHBoxLayout()
        control_panel.setSpacing(10)
        
        self.folder_btn = QPushButton("📂 Open Folder")
        self.folder_btn.clicked.connect(self.open_folder)
        self.folder_btn.setFixedHeight(40)
        
        self.sort_btn = QPushButton("🔤 Sort by Name")
        self.sort_btn.clicked.connect(self.sort_by_name)
        self.sort_btn.setFixedHeight(40)
        
        self.reset_btn = QPushButton("↺ Reset Order")
        self.reset_btn.clicked.connect(self.reset_order)
        self.reset_btn.setFixedHeight(40)
        
        self.save_btn = QPushButton("💾 Apply Order")
        self.save_btn.clicked.connect(self.apply_order)
        self.save_btn.setFixedHeight(40)
        self.save_btn.setEnabled(False)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
            QPushButton:hover:enabled {
                background-color: #45a049;
            }
        """)
        
        control_panel.addWidget(self.folder_btn)
        control_panel.addWidget(self.sort_btn)
        control_panel.addWidget(self.reset_btn)
        control_panel.addWidget(self.save_btn)
        control_panel.addStretch()
        
        # Status label
        self.status_label = QLabel("Ready to load images")
        self.status_label.setStyleSheet("color: #666; font-size: 12px; padding: 5px;")
        
        control_panel.addWidget(self.status_label)
        
        # Scroll area for image grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        self.container = QWidget()
        self.grid_layout = FlowLayout()
        self.container.setLayout(self.grid_layout)
        scroll.setWidget(self.container)
        
        layout.addLayout(control_panel)
        layout.addWidget(scroll, 1)
        
        # Enable drag and drop
        self.container.setAcceptDrops(True)
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat('application/x-image-widget'):
            event.accept()
        else:
            event.ignore()
    
    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat('application/x-image-widget'):
            event.accept()
        else:
            event.ignore()
    
    def dropEvent(self, event):
        if event.mimeData().hasFormat('application/x-image-widget'):
            data = event.mimeData().data('application/x-image-widget')
            drag_idx = int(data.data().decode())
            drop_pos = event.position().toPoint()
            
            # Find drop target widget
            for i in range(self.grid_layout.count()):
                item = self.grid_layout.itemAt(i)
                if item and item.widget():
                    widget_rect = item.geometry()
                    if widget_rect.contains(drop_pos):
                        drop_idx = i
                        if drag_idx != drop_idx and 0 <= drop_idx < len(self.items):
                            # Swap items
                            self.swap_items(drag_idx, drop_idx)
                            self.rearrange_grid()
                            self.dirty = True
                            self.save_btn.setEnabled(True)
                            self.status_label.setText(f"📋 Modified - Item {drag_idx+1} ↔ {drop_idx+1}")
                            self.status_label.setStyleSheet("color: #ff9800; font-weight: bold;")
                        break
            
            event.accept()
        else:
            event.ignore()
    
    def open_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, 
            "Select Image Folder",
            str(Path.home())
        )
        if folder:
            self.load_folder(Path(folder))
    
    def load_folder(self, folder: Path):
        if not folder.exists():
            QMessageBox.warning(self, "Error", "Folder does not exist!")
            return
        
        self.current_folder = folder
        self.items = []
        
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        
        # Get image files with multiple extensions
        extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff']
        image_paths = []
        
        for ext in extensions:
            # Case insensitive search
            image_paths.extend(folder.glob(f'*{ext}'))
            image_paths.extend(folder.glob(f'*{ext.upper()}'))
        
        if not image_paths:
            QApplication.restoreOverrideCursor()
            QMessageBox.information(self, "No Images", "No image files found in selected folder!")
            return
        
        # Sort naturally by filename
        image_paths.sort(key=lambda x: self.natural_sort_key(x.name))
        
        # Create items
        self.items = [ImageItem(p, i) for i, p in enumerate(image_paths)]
        
        # Clear current grid
        self.clear_grid()
        
        # Create placeholder widgets immediately
        for item in self.items:
            widget = self.create_image_widget(item)
            self.grid_layout.addWidget(widget)
        
        # Load thumbnails in background
        self.load_thumbnails_async()
        
        # Save last folder
        self.save_last_folder(folder)
        
        self.status_label.setText(f"📁 {folder.name} - Loading {len(self.items)} images...")
        self.status_label.setStyleSheet("color: #2196F3; font-weight: bold;")
        
        QApplication.restoreOverrideCursor()
    
    def natural_sort_key(self, s):
        """Natural sort key function"""
        return [int(text) if text.isdigit() else text.lower()
                for text in re.split(r'(\d+)', s)]
    
    def clear_grid(self):
        """Clear all widgets from grid"""
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
    
    def create_image_widget(self, item):
        """Create widget for an image item"""
        widget = QFrame()
        widget.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        widget.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 5px;
            }
            QFrame:hover {
                border: 2px solid #4CAF50;
                background-color: #f9f9f9;
            }
        """)
        widget.setFixedSize(self.thumb_size.width() + 30, self.thumb_size.height() + 70)
        widget.setCursor(Qt.CursorShape.OpenHandCursor)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Thumbnail label
        thumb_label = QLabel()
        thumb_label.setFixedSize(self.thumb_size)
        thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thumb_label.setStyleSheet("""
            QLabel {
                background-color: #f5f5f5;
                border-radius: 6px;
                border: 1px solid #ddd;
            }
        """)
        
        # Loading text
        loading_text = QLabel("Loading...")
        loading_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        loading_text.setStyleSheet("color: #888; font-size: 9px;")
        
        # Index badge
        idx_frame = QFrame()
        idx_frame.setStyleSheet("""
            QFrame {
                background-color: #2196F3;
                border-radius: 10px;
                padding: 2px 8px;
            }
        """)
        idx_layout = QHBoxLayout(idx_frame)
        idx_layout.setContentsMargins(0, 0, 0, 0)
        idx_label = QLabel(f"#{item.idx+1:03d}")
        idx_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        idx_label.setStyleSheet("color: white; font-weight: bold; font-size: 10px;")
        idx_layout.addWidget(idx_label)
        
        # Filename label (truncated)
        name = item.path.name
        if len(name) > 20:
            name = name[:17] + "..."
        name_label = QLabel(name)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet("color: #333; font-size: 11px; margin-top: 3px;")
        name_label.setWordWrap(True)
        name_label.setMaximumWidth(self.thumb_size.width() + 10)
        
        layout.addWidget(thumb_label)
        layout.addWidget(loading_text)
        layout.addWidget(idx_frame, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(name_label)
        
        # Store references
        widget.thumb_label = thumb_label
        widget.loading_text = loading_text
        widget.idx_label = idx_label
        widget.name_label = name_label
        widget.item_idx = item.idx
        
        # Make draggable
        widget.mousePressEvent = lambda e, w=widget: self.start_drag(w, e)
        
        return widget
    
    def load_thumbnails_async(self):
        """Load thumbnails in background thread"""
        def load_thumb(item):
            try:
                # Use OpenCV for faster image loading
                img = cv2.imread(str(item.path))
                if img is not None:
                    # Calculate thumbnail size maintaining aspect ratio
                    h, w = img.shape[:2]
                    scale = min(self.thumb_size.width() / w, self.thumb_size.height() / h)
                    new_w = int(w * scale)
                    new_h = int(h * scale)
                    
                    # Resize image
                    if new_w > 0 and new_h > 0:
                        resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
                        
                        # Convert BGR to RGB
                        resized_rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
                        
                        # Create QImage
                        height, width, channels = resized_rgb.shape
                        bytes_per_line = channels * width
                        q_img = QImage(resized_rgb.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
                        
                        # Create QPixmap
                        pixmap = QPixmap.fromImage(q_img.copy())
                        return item.idx, pixmap
            except Exception as e:
                print(f"Error loading thumbnail for {item.path.name}: {e}")
            return item.idx, None
        
        def on_thumbnails_loaded(results):
            """Callback when thumbnails are loaded"""
            for idx, pixmap in results:
                if pixmap:
                    widget = self.find_widget_by_idx(idx)
                    if widget:
                        # Update widget with thumbnail
                        widget.thumb_label.setPixmap(pixmap)
                        widget.loading_text.hide()
            
            # Update status
            self.status_label.setText(f"📊 {len(self.items)} images loaded")
            self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            
            # Enable buttons
            self.sort_btn.setEnabled(True)
            self.reset_btn.setEnabled(True)
            if self.dirty:
                self.save_btn.setEnabled(True)
        
        # Start thumbnail loading in thread pool
        self.executor = ThreadPoolExecutor(max_workers=4)
        future = self.executor.submit(lambda: [load_thumb(item) for item in self.items])
        future.add_done_callback(lambda f: on_thumbnails_loaded(f.result()))
    
    def start_drag(self, widget, event):
        """Start drag operation from widget"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Create drag object
            drag = QDrag(widget)
            mime_data = QMimeData()
            
            # Store widget index in mime data
            mime_data.setData('application/x-image-widget', str(widget.item_idx).encode())
            drag.setMimeData(mime_data)
            
            # Create drag pixmap (snapshot of widget)
            pixmap = QPixmap(widget.size())
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            widget.render(painter)
            painter.end()
            
            drag.setPixmap(pixmap)
            drag.setHotSpot(event.position().toPoint())
            
            # Change cursor during drag
            widget.setCursor(Qt.CursorShape.ClosedHandCursor)
            
            # Execute drag
            drag.exec(Qt.DropAction.MoveAction)
            
            # Restore cursor
            widget.setCursor(Qt.CursorShape.OpenHandCursor)
    
    def find_widget_by_idx(self, idx):
        """Find widget by item index"""
        for i in range(self.grid_layout.count()):
            item = self.grid_layout.itemAt(i)
            if item and item.widget() and item.widget().item_idx == idx:
                return item.widget()
        return None
    
    def swap_items(self, i, j):
        """Swap two items in the list"""
        if 0 <= i < len(self.items) and 0 <= j < len(self.items):
            # Swap items in list
            self.items[i], self.items[j] = self.items[j], self.items[i]
            
            # Update indices
            self.items[i].idx = i
            self.items[j].idx = j
    
    def rearrange_grid(self):
        """Rearrange widgets in grid according to new order"""
        # Collect all widgets
        widgets = []
        for i in range(self.grid_layout.count()):
            item = self.grid_layout.itemAt(i)
            if item and item.widget():
                widgets.append(item.widget())
        
        # Sort widgets by current index
        widgets.sort(key=lambda w: self.items[w.item_idx].idx)
        
        # Clear and re-add in correct order
        self.clear_grid()
        for widget in widgets:
            # Update widget display
            new_idx = self.items[widget.item_idx].idx
            widget.item_idx = new_idx
            widget.idx_label.setText(f"#{new_idx+1:03d}")
            
            # Update filename label if needed
            item = self.items[new_idx]
            name = item.path.name
            if len(name) > 20:
                name = name[:17] + "..."
            widget.name_label.setText(name)
            
            self.grid_layout.addWidget(widget)
    
    def sort_by_name(self):
        """Sort images by filename"""
        if not self.items:
            return
        
        # Sort items by filename
        self.items.sort(key=lambda x: self.natural_sort_key(x.path.name))
        
        # Update indices
        for i, item in enumerate(self.items):
            item.idx = i
        
        self.rearrange_grid()
        self.dirty = True
        self.save_btn.setEnabled(True)
        self.status_label.setText("🔤 Sorted by name")
        self.status_label.setStyleSheet("color: #2196F3; font-weight: bold;")
    
    def reset_order(self):
        """Reset to original order"""
        if not self.items or not self.dirty:
            return
        
        # Reset to original order
        self.items.sort(key=lambda x: x.orig_idx)
        for i, item in enumerate(self.items):
            item.idx = i
        
        self.rearrange_grid()
        self.dirty = False
        self.save_btn.setEnabled(False)
        self.status_label.setText("↺ Order reset to original")
        self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
    
    def apply_order(self):
        """Rename files according to new order"""
        if not self.items or not self.dirty:
            return
        
        # Confirm with user
        reply = QMessageBox.question(
            self, 
            'Confirm Rename',
            f'This will rename {len(self.items)} files according to the new order.\n\n'
            'Original files will be renamed with sequential numbers.\n\n'
            'Do you want to continue?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            
            success = 0
            errors = 0
            error_list = []
            
            # First, create a mapping of new names
            rename_plan = []
            for item in self.items:
                try:
                    if item.idx != item.orig_idx:
                        new_name = f"{item.idx:04d}{item.path.suffix}"
                        new_path = item.path.parent / new_name
                        rename_plan.append((item, new_path))
                except Exception as e:
                    errors += 1
                    error_list.append(f"{item.path.name}: {str(e)}")
            
            # Execute rename operations
            for item, new_path in rename_plan:
                try:
                    # Rename image file
                    item.path.rename(new_path)
                    
                    # Rename corresponding txt file if exists
                    txt_file = item.path.with_suffix('.txt')
                    if txt_file.exists():
                        txt_file.rename(new_path.with_suffix('.txt'))
                    
                    # Rename caption file if exists
                    caption_file = item.path.with_suffix('.caption')
                    if caption_file.exists():
                        caption_file.rename(new_path.with_suffix('.caption'))
                    
                    # Update item
                    item.path = new_path
                    item.orig_idx = item.idx
                    success += 1
                    
                except Exception as e:
                    errors += 1
                    error_list.append(f"{item.path.name}: {str(e)}")
            
            QApplication.restoreOverrideCursor()
            
            # Show result
            if errors == 0:
                QMessageBox.information(
                    self, 
                    'Success',
                    f'Successfully renamed {success} files!'
                )
            else:
                error_msg = f'Renamed {success} files, {errors} errors:\n\n' + '\n'.join(error_list[:10])
                if len(error_list) > 10:
                    error_msg += f'\n\n... and {len(error_list) - 10} more errors'
                
                QMessageBox.warning(
                    self,
                    'Partial Success',
                    error_msg
                )
            
            self.dirty = False
            self.save_btn.setEnabled(False)
            
            # Refresh display
            self.status_label.setText(f"✓ Renamed {success} files" + (f", {errors} errors" if errors else ""))
            self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;" if errors == 0 else "color: #ff9800; font-weight: bold;")
    
    def save_last_folder(self, folder: Path):
        """Save last opened folder"""
        try:
            with open('last_folder.json', 'w', encoding='utf-8') as f:
                json.dump({'folder': str(folder)}, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def load_last_folder(self):
        """Load last opened folder"""
        try:
            if Path('last_folder.json').exists():
                with open('last_folder.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    folder = Path(data.get('folder', ''))
                    if folder.exists():
                        # Load after UI is shown
                        QTimer.singleShot(500, lambda: self.load_folder(folder))
        except:
            pass

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Set application palette
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(240, 240, 240))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(50, 50, 50))
    palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(245, 245, 245))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(50, 50, 50))
    palette.setColor(QPalette.ColorRole.Text, QColor(30, 30, 30))
    palette.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(50, 50, 50))
    palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
    palette.setColor(QPalette.ColorRole.Highlight, QColor(33, 150, 243))
    palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
    app.setPalette(palette)
    
    # Set application font
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    window = UltraFastGallery()
    window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()