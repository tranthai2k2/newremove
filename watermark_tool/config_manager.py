import sys
sys.dont_write_bytecode = True

import os
import pickle
import tkinter as tk
from tkinter import messagebox

class ConfigManager:
    def __init__(self):
        self.config_file = "watermark_config.pkl"
        self.registered_watermarks_file = "registered_watermarks.pkl"

    def save_watermark_config(self, watermark_path, wm_size, wm_position):
        config = {
            "watermark_path": watermark_path,
            "wm_size": wm_size,
            "wm_position": wm_position
        }
        try:
            with open(self.config_file, "wb") as f:
                pickle.dump(config, f)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lưu cấu hình watermark: {e}")

    def load_last_watermark_path(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "rb") as f:
                    config = pickle.load(f)
                if isinstance(config, dict):
                    return config.get("watermark_path")
                return config
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể tải cấu hình: {e}")
        return None

    def save_registered_watermarks(self, registered_watermarks):
        try:
            with open(self.registered_watermarks_file, "wb") as f:
                pickle.dump(registered_watermarks, f)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lưu watermark đã đăng ký: {e}")

    def load_registered_watermarks(self):
        if os.path.exists(self.registered_watermarks_file):
            try:
                with open(self.registered_watermarks_file, "rb") as f:
                    data = pickle.load(f)
                if data and isinstance(data, list):
                    if data and isinstance(data[0], dict):
                        return data
                    else:
                        watermarks = []
                        for item in data:
                            if len(item) == 3:
                                wm = {"filename": item[0], "path": item[1], "wm_size": item[2]}
                            else:
                                wm = {"filename": item[0], "path": item[1], "wm_size": 50}
                            watermarks.append(wm)
                        return watermarks
                return []
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể tải watermark đã đăng ký: {e}")
                return []
        return []
