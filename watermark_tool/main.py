import sys
sys.dont_write_bytecode = True

import tkinter as tk
from ui_panels import UIPanels
from image_processor import ImageProcessor
from config_manager import ConfigManager

class WatermarkApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Watermark Tool")
        self.root.geometry("1150x700")
        self.root.configure(bg="#e8f0fe")
        
        # Khởi tạo các thành phần chính
        self.config_manager = ConfigManager()
        self.image_processor = ImageProcessor(self.config_manager)
        self.ui_panels = UIPanels(root, self.image_processor, self.config_manager)
        
        # Tải watermark đã lưu nếu có đường dẫn hợp lệ
        if self.image_processor.watermark_path:
            self.ui_panels.load_watermark()

if __name__ == "__main__":
    root = tk.Tk()
    app = WatermarkApp(root)
    root.mainloop()