import sys
sys.dont_write_bytecode = True

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk, ImageFilter

class ImageProcessor:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        
        # Các thuộc tính ảnh và watermark
        self.watermark_image = None
        self.original_watermark_image = None
        self.watermark_path = self.config_manager.load_last_watermark_path()
        self.registered_watermarks = self.config_manager.load_registered_watermarks()
        
        # Các thuộc tính ảnh đang xử lý
        self.selected_image_path = None
        self.image_paths = []
        self.image_folder = None
        
        # Các thuộc tính watermark (vị trí, kích thước)
        self.wm_position = (10, 10)
        self.wm_size = 50
       
        # Các thuộc tính preview
        self.img_size = (600, 600)
        self.original_img_size = None
        self.preview_size = None
        self.preview_offset = (0, 0)

        # Canvas tham chiếu (từ ui)
        self.img_canvas = None
        self.wm_canvas = None

        # Checkbox biến (được set từ UI)
        self.image_wm_vars = {}
        self.image_blur_vars = {}

    # --- Xử lý watermark ---
    def load_watermark(self, path=None):
        if not path:
            path = filedialog.askopenfilename(filetypes=[("PNG files", "*.png")])
        if path:
            try:
                self.watermark_path = path
                img = Image.open(path).convert("RGBA")
                self.original_watermark_image = img.copy()
                self.watermark_image = img.copy()
                
                # Hiển thị watermark mới bên panel trái
                self.display_watermark()
                
                # (Sửa) Reset vị trí watermark về (10,10) và show preview để loại watermark cũ
                self.wm_position = (10, 10)
                self.show_preview()

                self.config_manager.save_watermark_config(
                    self.watermark_path, self.wm_size, self.wm_position
                )
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể tải watermark: {e}")

    def register_watermark(self):
        path = filedialog.askopenfilename(filetypes=[("PNG files", "*.png")])
        if path:
            try:
                filename = os.path.basename(path)
                wm_data = {"filename": filename, "path": path, "wm_size": self.wm_size}
                self.registered_watermarks.append(wm_data)
                self.config_manager.save_registered_watermarks(self.registered_watermarks)
                messagebox.showinfo("Thành công", "Watermark đã được đăng ký.")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể đăng ký watermark: {e}")

    def delete_registered_watermark(self, index):
        if index is None:
            messagebox.showerror("Lỗi", "Vui lòng chọn watermark cần xóa.")
            return
        answer = messagebox.askyesno("Xác nhận", "Bạn có chắc chắn muốn xóa watermark đã đăng ký này không?")
        if answer:
            try:
                del self.registered_watermarks[index]
                self.config_manager.save_registered_watermarks(self.registered_watermarks)
                messagebox.showinfo("Thông báo", "Đã xóa watermark đã đăng ký.")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể xóa watermark: {e}")

    def select_registered_watermark(self, index):
        try:
            wm = self.registered_watermarks[index]
            img = Image.open(wm["path"]).convert("RGBA")
            self.original_watermark_image = img.copy()
            self.watermark_image = img.copy()
            self.wm_size = wm["wm_size"]
            
            # (Sửa) Reset vị trí, hiển thị watermark mới
            self.display_watermark()
            self.wm_position = (10, 10)
            self.show_preview()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tải watermark: {e}")

    def display_watermark(self):
        """Hiển thị watermark ở panel trái (canvas wm_canvas)."""
        if self.original_watermark_image:
            orig_w, orig_h = self.original_watermark_image.size
            new_w = self.wm_size
            new_h = int(self.wm_size * (orig_h / orig_w))
            wm_resized = self.original_watermark_image.resize(
                (new_w, new_h), Image.Resampling.LANCZOS
            )
            self.watermark_image = wm_resized
            if self.wm_canvas:
                self.wm_tk = ImageTk.PhotoImage(wm_resized)
                self.wm_canvas.delete("all")
                canvas_width = self.wm_canvas.winfo_width()
                canvas_height = self.wm_canvas.winfo_height()
                canvas_center = (canvas_width // 2, canvas_height // 2)
                self.wm_canvas.create_image(canvas_center, image=self.wm_tk)

    def resize_watermark(self, size: int) -> Image.Image:
        if self.original_watermark_image is None:
            return None
        orig_w, orig_h = self.original_watermark_image.size
        new_w = size
        new_h = int(size * (orig_h / orig_w))
        return self.original_watermark_image.resize(
            (new_w, new_h), Image.Resampling.LANCZOS
        )

    def zoom_watermark(self, event: tk.Event) -> None:
        if hasattr(event, 'delta'):
            delta = 5 if event.delta > 0 else -5
        elif event.num == 4:
            delta = 5
        elif event.num == 5:
            delta = -5
        else:
            delta = 0
        self.wm_size = max(10, self.wm_size + delta)
        self.display_watermark()
        self.show_preview()

    def set_watermark_position_center(self) -> None:
        if self.preview_size is None:
            self.show_preview()
        preview_w, preview_h = self.preview_size or (0, 0)
        wm_img = self.resize_watermark(self.wm_size)
        if wm_img:
            wm_w, wm_h = wm_img.size
            new_x = (preview_w - wm_w) // 2
            new_y = (preview_h - wm_h) // 2
            self.wm_position = (new_x, new_y)
            self.show_preview()

    def set_watermark_position_bottom_right(self) -> None:
        if self.preview_size is None:
            self.show_preview()
        preview_w, preview_h = self.preview_size or (0, 0)
        wm_img = self.resize_watermark(self.wm_size)
        if wm_img:
            wm_w, wm_h = wm_img.size
            new_x = preview_w - wm_w
            new_y = preview_h - wm_h
            self.wm_position = (new_x, new_y)
            self.show_preview()

    # --- Xử lý ảnh & preview ---
    def load_images(self) -> None:
        folder = filedialog.askdirectory()
        if folder:
            if os.path.basename(folder) == "__pycache__":
                messagebox.showerror("Lỗi", "Không cho phép chọn folder __pycache__.")
                return
            self.image_folder = folder
            try:
                all_files = [
                    os.path.join(folder, f) for f in os.listdir(folder)
                    if f.lower().endswith((".jpg", ".jpeg", ".png"))
                ]
                self.image_paths = sorted(
                    all_files,
                    key=lambda x: os.path.basename(x).lower()
                )
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể tải ảnh từ folder: {e}")

    def display_selected_image(self) -> None:
        if not self.selected_image_path and self.image_paths:
            self.selected_image_path = self.image_paths[0]
        self.show_preview()

    def on_canvas_resize(self, event: tk.Event) -> None:
        if not self.img_canvas:
            return
        self.img_size = (event.width, event.height)
        self.show_preview()

    def show_preview(self) -> None:
        if not self.img_canvas or not self.selected_image_path:
            if self.img_canvas:
                self.img_canvas.delete("all")
            return
        try:
            base_img = Image.open(self.selected_image_path).convert("RGBA")
            self.original_img_size = base_img.size
            canvas_w = self.img_canvas.winfo_width()
            canvas_h = self.img_canvas.winfo_height()
            if canvas_w <= 0 or canvas_h <= 0:
                return
            
            ratio = min(canvas_w / base_img.width, canvas_h / base_img.height)
            preview_size = (
                int(base_img.width * ratio), 
                int(base_img.height * ratio)
            )
            offset_x = (canvas_w - preview_size[0]) // 2
            offset_y = (canvas_h - preview_size[1]) // 2
            self.preview_size = preview_size
            self.preview_offset = (offset_x, offset_y)

            preview_img = base_img.resize(preview_size, Image.Resampling.LANCZOS)
            if self.watermark_image:
                wm_img = self.resize_watermark(self.wm_size)
                wm_x, wm_y = self.wm_position
                preview_img.paste(wm_img, (wm_x, wm_y), wm_img)
            
            self.tk_preview = ImageTk.PhotoImage(preview_img)
            self.img_canvas.delete("all")
            self.img_canvas.create_image(offset_x, offset_y, anchor="nw", image=self.tk_preview)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể hiển thị ảnh: {e}")

    def move_watermark(self, event: tk.Event) -> None:
        if not (self.preview_offset and self.preview_size):
            return
        offset_x, offset_y = self.preview_offset
        preview_w, preview_h = self.preview_size
        wm_img = self.resize_watermark(self.wm_size)
        if wm_img is None:
            return
        wm_w, wm_h = wm_img.size
        new_x = event.x - offset_x
        new_y = event.y - offset_y
        new_x = max(0, min(new_x, preview_w - wm_w))
        new_y = max(0, min(new_y, preview_h - wm_h))
        self.wm_position = (new_x, new_y)
        self.show_preview()

    def apply_watermark(self, img: Image.Image) -> Image.Image:
        if not self.watermark_image or not self.preview_size:
            return img
        orig_w, _ = self.original_img_size
        preview_w, _ = self.preview_size
        scale = orig_w / preview_w
        actual_position = (
            int(self.wm_position[0] * scale), 
            int(self.wm_position[1] * scale)
        )
        wm_resized = self.resize_watermark(int(self.wm_size * scale))
        img.paste(wm_resized, actual_position, wm_resized)
        return img

    def set_preview_image(self, path: str) -> None:
        self.selected_image_path = path
        self.show_preview()

    # --- Các hàm lưu ảnh ---
    def save_watermarked_images_to_folder(self, save_mode: str) -> None:
        if not self.image_paths or not self.image_folder:
            messagebox.showerror("Lỗi", "Chưa chọn folder chứa ảnh.")
            return
        images_to_process = [
            img for img in self.image_paths 
            if self.image_wm_vars.get(img, tk.IntVar(value=0)).get() == 1
        ]
        if not images_to_process:
            images_to_process = self.image_paths
        
        folder_name = os.path.basename(self.image_folder)
        if save_mode == "new":
            new_folder = os.path.join(self.image_folder, f"{folder_name}_watermark")
            if not os.path.exists(new_folder):
                os.makedirs(new_folder)
        else:
            new_folder = self.image_folder
        
        for img_path in images_to_process:
            try:
                img = Image.open(img_path).convert("RGBA")
                watermarked_img = self.apply_watermark(img)
                base_name = os.path.basename(img_path)
                save_path = os.path.join(new_folder, base_name)
                watermarked_img.save(save_path, "PNG")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể lưu ảnh {img_path}: {e}")

        self.config_manager.save_watermark_config(self.watermark_path, self.wm_size, self.wm_position)
        messagebox.showinfo("Completed", f"Watermarked images have been saved to:\n{new_folder}")

    def save_blurred_images_to_folder(self, save_mode: str) -> None:
        if not self.image_paths or not self.image_folder:
            messagebox.showerror("Lỗi", "Chưa chọn folder chứa ảnh.")
            return
        images_to_process = [
            img for img in self.image_paths 
            if self.image_blur_vars.get(img, tk.IntVar(value=0)).get() == 1
        ]
        if not images_to_process:
            images_to_process = self.image_paths
        
        folder_name = os.path.basename(self.image_folder)
        if save_mode == "new":
            new_folder = os.path.join(self.image_folder, f"{folder_name}_blurred")
            if not os.path.exists(new_folder):
                os.makedirs(new_folder)
        else:
            new_folder = self.image_folder
        
        for img_path in images_to_process:
            try:
                img = Image.open(img_path)
                img_blurred = img.filter(ImageFilter.GaussianBlur(5))
                pixel_size = 10
                img_pixelated = img_blurred.resize(
                    (img.width // pixel_size, img.height // pixel_size), 
                    Image.NEAREST
                ).resize(img.size, Image.NEAREST)
                base_name = os.path.basename(img_path)
                save_path = os.path.join(new_folder, base_name)
                img_pixelated.save(save_path)
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể xử lý ảnh {img_path}: {e}")
        messagebox.showinfo("Completed", f"Blurred images have been saved to:\n{new_folder}")

    def save_blurred_and_watermarked_images_to_folder(self, save_mode: str) -> None:
        if not self.image_paths or not self.image_folder:
            messagebox.showerror("Lỗi", "Chưa chọn folder chứa ảnh.")
            return
        images_to_process = [
            img for img in self.image_paths 
            if (self.image_wm_vars.get(img, tk.IntVar(value=0)).get() == 1 and
                self.image_blur_vars.get(img, tk.IntVar(value=0)).get() == 1)
        ]
        if not images_to_process:
            images_to_process = self.image_paths
        
        folder_name = os.path.basename(self.image_folder)
        if save_mode == "new":
            new_folder = os.path.join(self.image_folder, f"{folder_name}_blur_watermark")
            if not os.path.exists(new_folder):
                os.makedirs(new_folder)
        else:
            new_folder = self.image_folder
        
        for img_path in images_to_process:
            try:
                img = Image.open(img_path)
                img_blurred = img.filter(ImageFilter.GaussianBlur(5))
                pixel_size = 10
                img_pixelated = img_blurred.resize(
                    (img.width // pixel_size, img.height // pixel_size), 
                    Image.NEAREST
                ).resize(img.size, Image.NEAREST)
                img_pixelated = img_pixelated.convert("RGBA")
                watermarked_img = self.apply_watermark(img_pixelated)
                base_name = os.path.basename(img_path)
                save_path = os.path.join(new_folder, base_name)
                watermarked_img.save(save_path, "PNG")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể xử lý ảnh {img_path}: {e}")
        messagebox.showinfo("Completed", f"Blurred & Watermarked images have been saved to:\n{new_folder}")
