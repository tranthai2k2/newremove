import os
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageFilter  # Sử dụng Pillow để xử lý ảnh
import ttkbootstrap as tb  # Sử dụng ttkbootstrap để xây dựng giao diện hiện đại
from ttkbootstrap.constants import *

class WatermarkApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Watermark Tool (Modern)")
        self.root.geometry("1150x700")
        tb.Style("flatly")

        # ---------------------------
        # Thuộc tính liên quan đến watermark, ảnh và cấu hình
        # ---------------------------
        self.watermark_path = None
        self.original_watermark_image = None
        self.selected_image_path = None
        
        # Mỗi phần tử: {"path":..., "blur": bool, "wm": bool}
        self.image_data = []
        self.image_folder = None
        self.registered_watermarks = []

        # Vị trí/kích thước watermark trên ảnh preview
        self.wm_position = (10, 10)
        self.wm_size = 50
        self.preview_offset = (0, 0)
        self.preview_size = None
        self.original_img_size = None

        # Biến hỗ trợ kéo thả watermark
        self.dragging = False
        self.drag_offset = (0, 0)

        # File cấu hình
        self.config_file = "watermark_config.json"
        self.registered_watermarks_file = "registered_watermarks.json"

        # Biến chọn theo khoảng (áp dụng cho đánh dấu Blur/Watermark)
        self.entry_range_start = None
        self.entry_range_end = None

        # Biến toggle header Blur/Watermark
        self.blur_all_selected = False
        self.wm_all_selected = False

        # Biến chọn chế độ lưu (tạo folder mới hoặc ghi đè)
        self.save_mode = tk.StringVar(value="new")

        # Canvas sẽ được khởi tạo trong init_center_panel
        self.canvas = None

        # Treeview hiển thị danh sách ảnh sẽ được khởi tạo trong init_right_panel
        self.tree = None
        # Label hiển thị số lượng ảnh trong folder
        self.lbl_count = None

        # Đọc file cấu hình và watermark đã đăng ký
        self.load_config()

        # Xây dựng giao diện
        self.build_gui()

        # Nếu có watermark_path, load watermark
        if self.watermark_path:
            self.load_watermark(self.watermark_path)

        # Hiển thị danh sách watermark đã đăng ký
        self.populate_registered_watermarks_listbox()

    # ========================================================
    #  TỔNG HỢP GIAO DIỆN
    # ========================================================
    def build_gui(self):
        self.main_frame = ttk.Frame(self.root, padding=10)
        self.main_frame.pack(fill="both", expand=True)
        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.rowconfigure(0, weight=1)

        self.init_left_panel()
        self.init_center_panel()
        self.init_right_panel()
        self.init_bottom_panel()
    def set_watermark_position_top_left(self):
        if not self.canvas or not self.preview_size or not self.original_watermark_image:
            messagebox.showwarning("Thông báo", "Vui lòng chọn ảnh trước!")
            return
        self.wm_position = (0, 0)          # x = 0, y = 0
        self.show_preview()

    # ========================================================
    #  GIAO DIỆN BÊN TRÁI - QUẢN LÝ WATERMARK
    # ========================================================
    def init_left_panel(self):
        self.left_frame = ttk.LabelFrame(self.main_frame, text="Watermark", padding=10)
        self.left_frame.grid(row=0, column=0, sticky="ns", padx=5, pady=5)

        ttk.Button(self.left_frame, text="Chọn Ảnh Watermark", command=self.select_watermark).pack(fill="x", pady=5)
        ttk.Button(self.left_frame, text="Đăng ký Watermark", command=self.register_watermark).pack(fill="x", pady=5)
        ttk.Button(self.left_frame, text="Xóa Watermark", command=self.delete_registered_watermark).pack(fill="x", pady=5)

        # Slider chỉnh kích thước watermark
        self.slider = ttk.Scale(self.left_frame, from_=10, to=300, orient="horizontal", command=self.update_slider)
        self.slider.set(self.wm_size)
        self.slider.pack(fill="x", pady=5)

        ttk.Button(self.left_frame, text="Preset: Center", command=self.set_watermark_position_center).pack(fill="x", pady=2)
        ttk.Button(self.left_frame, text="Preset: Bottom-Right", command=self.set_watermark_position_bottom_right).pack(fill="x", pady=2)
        ttk.Button(self.left_frame, text="Preset: Top-left",
           command=self.set_watermark_position_top_left).pack(fill="x", pady=2)


        ttk.Label(self.left_frame, text="Watermark đã đăng ký:").pack(anchor="w", pady=(10, 0))
        self.wm_listbox = tk.Listbox(self.left_frame, height=6)
        self.wm_listbox.pack(fill="both", expand=True, pady=5)
        self.wm_listbox.bind("<<ListboxSelect>>", self.select_registered_watermark)

    # ========================================================
    #  GIAO DIỆN GIỮA - HIỂN THỊ ẢNH
    # ========================================================
    def init_center_panel(self):
        self.center_frame = ttk.Frame(self.main_frame, padding=10)
        self.center_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        self.center_frame.columnconfigure(0, weight=1)
        self.center_frame.rowconfigure(1, weight=1)

        ttk.Button(self.center_frame, text="Chọn Folder Ảnh", command=self.load_images).grid(row=0, column=0, sticky="ew", pady=5)

        self.canvas = tk.Canvas(self.center_frame, bg="white")
        self.canvas.grid(row=1, column=0, sticky="nsew", pady=5)

        # Liên kết sự kiện cho canvas
        self.canvas.bind("<Button-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.do_drag)
        self.canvas.bind("<ButtonRelease-1>", self.stop_drag)
        self.canvas.bind("<MouseWheel>", self.zoom_watermark)
        self.canvas.bind("<Configure>", lambda e: self.show_preview())

    # ========================================================
    #  GIAO DIỆN BÊN PHẢI - DANH SÁCH ẢNH (Treeview + Label count)
    # ========================================================
    def init_right_panel(self):
        self.right_frame = ttk.LabelFrame(self.main_frame, text="Danh sách Ảnh (0)", padding=10)
        self.right_frame.grid(row=0, column=2, sticky="ns", padx=5, pady=5)

        # Label hiển thị số lượng ảnh
        self.lbl_count = ttk.Label(self.right_frame, text="Số ảnh: 0")
        self.lbl_count.pack(fill="x", padx=5, pady=(0,5))

        # Khung nhập chọn STT và thao tác theo khoảng
        top_controls = ttk.Frame(self.right_frame)
        top_controls.pack(fill="x", pady=5)

        ttk.Label(top_controls, text="Chọn STT từ:").grid(row=0, column=0, padx=2)
        self.entry_range_start = ttk.Entry(top_controls, width=5)
        self.entry_range_start.grid(row=0, column=1, padx=2)

        ttk.Label(top_controls, text="đến:").grid(row=0, column=2, padx=2)
        self.entry_range_end = ttk.Entry(top_controls, width=5)
        self.entry_range_end.grid(row=0, column=3, padx=2)

        ttk.Button(top_controls, text="Watermark A→B", command=self.mark_watermark_range).grid(row=0, column=4, padx=5)
        ttk.Button(top_controls, text="Blur A→B", command=self.mark_blur_range).grid(row=0, column=5, padx=5)
        ttk.Button(top_controls, text="Bỏ chọn tất cả", command=self.uncheck_all).grid(row=1, column=0, columnspan=6, pady=5)

        # Treeview hiển thị danh sách ảnh
        columns = ("stt", "filename", "blur", "wm")
        self.tree = ttk.Treeview(self.right_frame, columns=columns, show="headings", selectmode="browse", height=15)
        self.tree.pack(fill="both", expand=True, side="left")

        # Cấu hình các cột
        self.tree.heading("stt", text="STT", command=lambda: self.on_header_click("stt"))
        self.tree.heading("filename", text="Ảnh")
        self.tree.heading("blur", text="Blur", command=lambda: self.on_header_click("blur"))
        self.tree.heading("wm", text="Watermark", command=lambda: self.on_header_click("wm"))

        self.tree.column("stt", width=50, anchor="center")
        self.tree.column("filename", width=180, anchor="center")
        self.tree.column("blur", width=80, anchor="center")
        self.tree.column("wm", width=100, anchor="center")

        # Scrollbar cho Treeview
        scrollbar = ttk.Scrollbar(self.right_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        # Gán sự kiện khi chọn dòng
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        # Cấu hình zebra stripes
        style = ttk.Style()
        style.configure("Treeview", rowheight=25, borderwidth=1, relief="solid")
        self.tree.tag_configure("evenrow", background="#ffffff")
        self.tree.tag_configure("oddrow", background="#f0f0f0")

    # ========================================================
    #  GIAO DIỆN DƯỚI - CHỨC NĂNG LƯU ẢNH
    # ========================================================
    def init_bottom_panel(self):
        self.bottom_frame = ttk.Frame(self.root, padding=10)
        self.bottom_frame.pack(fill="x", pady=5)

        ttk.Button(self.bottom_frame, text="Lưu Ảnh Watermark", command=self.save_watermarked_images_to_folder).pack(side="left", padx=5)
        ttk.Button(self.bottom_frame, text="Lưu Ảnh Blur", command=self.save_blurred_images_to_folder).pack(side="left", padx=5)
        ttk.Button(self.bottom_frame, text="Lưu Ảnh Blur & Watermark", command=self.save_blurred_and_watermarked_images_to_folder).pack(side="left", padx=5)

        save_mode_frame = ttk.Frame(self.bottom_frame)
        save_mode_frame.pack(side="right", padx=5)
        ttk.Label(save_mode_frame, text="Chế độ lưu:").pack(side="left", padx=5)
        ttk.Radiobutton(save_mode_frame, text="Tạo folder mới", variable=self.save_mode, value="new").pack(side="left", padx=2)
        ttk.Radiobutton(save_mode_frame, text="Ghi đè file gốc", variable=self.save_mode, value="overwrite").pack(side="left", padx=2)

    # ========================================================
    #  LOAD/SAVE CẤU HÌNH & WATERMARK
    # ========================================================
    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    self.watermark_path = config.get("watermark_path")
                    self.wm_size = config.get("wm_size", 50)
                    self.wm_position = tuple(config.get("wm_position", (10, 10)))
            except:
                pass
        if os.path.exists(self.registered_watermarks_file):
            try:
                with open(self.registered_watermarks_file, "r", encoding="utf-8") as f:
                    self.registered_watermarks = json.load(f)
            except:
                pass

    def save_config(self):
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump({
                    "watermark_path": self.watermark_path,
                    "wm_size": self.wm_size,
                    "wm_position": list(self.wm_position)
                }, f, indent=2)
        except:
            pass

    def save_registered_watermarks(self):
        try:
            with open(self.registered_watermarks_file, "w", encoding="utf-8") as f:
                json.dump(self.registered_watermarks, f, indent=2)
        except:
            pass

    # ========================================================
    #  HÀM XỬ LÝ WATERMARK ĐĂNG KÝ
    # ========================================================
    def select_watermark(self):
        path = filedialog.askopenfilename(filetypes=[("PNG files", "*.png")])
        if path:
            self.load_watermark(path)

    def load_watermark(self, path):
        try:
            self.watermark_path = path
            self.original_watermark_image = Image.open(path).convert("RGBA")
            self.save_config()
            if self.canvas is not None:
                self.show_preview()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tải watermark: {e}")

    def register_watermark(self):
        if not self.watermark_path:
            messagebox.showerror("Lỗi", "Chưa có watermark để đăng ký.")
            return
        for item in self.registered_watermarks:
            if item["path"] == self.watermark_path:
                messagebox.showwarning("Cảnh báo", "Watermark này đã được đăng ký trước đó.")
                return
        filename = os.path.basename(self.watermark_path)
        wm_data = {"filename": filename, "path": self.watermark_path, "wm_size": self.wm_size}
        self.registered_watermarks.append(wm_data)
        self.save_registered_watermarks()
        self.populate_registered_watermarks_listbox()
        messagebox.showinfo("Thành công", "Watermark đã được đăng ký.")

    def delete_registered_watermark(self):
        selection = self.wm_listbox.curselection()
        if not selection:
            messagebox.showerror("Lỗi", "Vui lòng chọn watermark cần xóa.")
            return
        index = selection[0]
        if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn xóa watermark này không?"):
            del self.registered_watermarks[index]
            self.save_registered_watermarks()
            self.populate_registered_watermarks_listbox()
            messagebox.showinfo("Thông báo", "Đã xóa watermark.")

    def populate_registered_watermarks_listbox(self):
        self.wm_listbox.delete(0, tk.END)
        for wm in self.registered_watermarks:
            self.wm_listbox.insert(tk.END, wm["filename"])

    def select_registered_watermark(self, event):
        selection = self.wm_listbox.curselection()
        if selection:
            index = selection[0]
            wm = self.registered_watermarks[index]
            self.load_watermark(wm["path"])
            self.wm_size = wm.get("wm_size", 50)
            self.slider.set(self.wm_size)
            if self.canvas is not None:
                self.show_preview()

    # ========================================================
    #  HIỂN THỊ ẢNH VÀ WATERMARK
    # ========================================================
    def show_preview(self):
        if self.canvas is None or not self.selected_image_path:
            return
        try:
            img = Image.open(self.selected_image_path).convert("RGBA")
            self.original_img_size = img.size
            c_w = self.canvas.winfo_width()
            c_h = self.canvas.winfo_height()
            if c_w <= 0 or c_h <= 0:
                return
            scale = min(c_w / img.width, c_h / img.height)
            preview_w = int(img.width * scale)
            preview_h = int(img.height * scale)
            self.preview_size = (preview_w, preview_h)
            self.preview_offset = ((c_w - preview_w) // 2, (c_h - preview_h) // 2)
            img_resized = img.resize((preview_w, preview_h), Image.Resampling.LANCZOS)
            if self.original_watermark_image:
                wm = self.resize_watermark(self.wm_size)
                x, y = self.wm_position
                # Dán watermark trực tiếp vào ảnh preview, giữ nguyên độ mờ ban đầu nếu có
                img_resized.paste(wm, (x, y), wm)
            self.tk_img = ImageTk.PhotoImage(img_resized)
            self.canvas.delete("all")
            self.canvas.create_image(self.preview_offset[0], self.preview_offset[1], anchor="nw", image=self.tk_img)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể hiển thị ảnh: {e}")

    def resize_watermark(self, size):
        if not self.original_watermark_image:
            return None
        w, h = self.original_watermark_image.size
        ratio = w / h
        new_w = size
        new_h = int(size / ratio)
        return self.original_watermark_image.resize((new_w, new_h), Image.Resampling.LANCZOS)

    def update_slider(self, val):
        self.wm_size = int(float(val))
        if self.canvas is not None:
            self.show_preview()

    # ========================================================
    #  KÉO THẢ WATERMARK
    # ========================================================
    def start_drag(self, event):
        if not (self.canvas and self.preview_size and self.original_watermark_image):
            return
        offset_x, offset_y = self.preview_offset
        local_x = event.x - offset_x
        local_y = event.y - offset_y
        wm_img = self.resize_watermark(self.wm_size)
        if not wm_img:
            return
        wm_w, wm_h = wm_img.size
        if (self.wm_position[0] <= local_x <= self.wm_position[0] + wm_w and
            self.wm_position[1] <= local_y <= self.wm_position[1] + wm_h):
            self.dragging = True
            self.drag_offset = (local_x - self.wm_position[0], local_y - self.wm_position[1])
        else:
            self.dragging = False

    def do_drag(self, event):
        if not self.dragging or not self.canvas:
            return
        offset_x, offset_y = self.preview_offset
        preview_w, preview_h = self.preview_size
        wm_img = self.resize_watermark(self.wm_size)
        if not wm_img:
            return
        wm_w, wm_h = wm_img.size
        local_x = event.x - offset_x
        local_y = event.y - offset_y
        new_x = local_x - self.drag_offset[0]
        new_y = local_y - self.drag_offset[1]
        new_x = max(0, min(new_x, preview_w - wm_w))
        new_y = max(0, min(new_y, preview_h - wm_h))
        self.wm_position = (new_x, new_y)
        self.show_preview()

    def stop_drag(self, event):
        self.dragging = False

    def zoom_watermark(self, event):
        if hasattr(event, 'delta'):
            delta = 5 if event.delta > 0 else -5
        elif event.num == 4:
            delta = 5
        elif event.num == 5:
            delta = -5
        else:
            delta = 0
        self.wm_size = max(10, self.wm_size + delta)
        self.slider.set(self.wm_size)
        if self.canvas:
            self.show_preview()

    def set_watermark_position_center(self):
        if not self.canvas or not self.preview_size or not self.original_watermark_image:
            messagebox.showwarning("Thông báo", "Vui lòng chọn ảnh trước!")
            return
        preview_w, preview_h = self.preview_size
        wm = self.resize_watermark(self.wm_size)
        wm_w, wm_h = wm.size
        self.wm_position = ((preview_w - wm_w) // 2, (preview_h - wm_h) // 2)
        self.show_preview()

    def set_watermark_position_bottom_right(self):
        if not self.canvas or not self.preview_size or not self.original_watermark_image:
            messagebox.showwarning("Thông báo", "Vui lòng chọn ảnh trước!")
            return
        preview_w, preview_h = self.preview_size
        wm = self.resize_watermark(self.wm_size)
        wm_w, wm_h = wm.size
        self.wm_position = (preview_w - wm_w, preview_h - wm_h)
        self.show_preview()

    # ========================================================
    #  XỬ LÝ DANH SÁCH ẢNH (Treeview)
    # ========================================================
    def load_images(self):
        folder = filedialog.askdirectory()
        if folder:
            self.image_folder = folder
            self.image_data.clear()
            files = [f for f in os.listdir(folder) if f.lower().endswith((".jpg", ".png", ".jpeg"))]
            for file in files:
                self.image_data.append({
                    "path": os.path.join(folder, file),
                    "blur": False,
                    "wm": False
                })
            self.update_treeview()
            self.right_frame.config(text=f"Danh sách Ảnh ({len(self.image_data)})")
            self.lbl_count.config(text=f"Số ảnh: {len(self.image_data)}")
            if self.image_data:
                self.selected_image_path = self.image_data[0]["path"]
                self.show_preview()

    def update_treeview(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for idx, data in enumerate(self.image_data, start=1):
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            blur_text = "☑" if data["blur"] else "☐"
            wm_text = "☑" if data["wm"] else "☐"
            self.tree.insert("", tk.END, values=(idx, os.path.basename(data["path"]), blur_text, wm_text), tags=(tag,))

    def on_tree_select(self, event):
        selected = self.tree.focus()
        if selected:
            values = self.tree.item(selected, "values")
            if values:
                idx = int(values[0])
                self.selected_image_path = self.image_data[idx - 1]["path"]
                self.show_preview()

    def mark_watermark_range(self):
        start_s = self.entry_range_start.get()
        end_s = self.entry_range_end.get()
        if not (start_s.isdigit() and end_s.isdigit()):
            messagebox.showerror("Lỗi", "STT phải là số.")
            return
        start = int(start_s)
        end = int(end_s)
        if start < 1:
            start = 1
        if end > len(self.image_data):
            end = len(self.image_data)
        if start > end:
            messagebox.showerror("Lỗi", "STT bắt đầu phải nhỏ hơn hoặc bằng STT kết thúc.")
            return
        for i in range(len(self.image_data)):
            self.image_data[i]["wm"] = False
        for i in range(start, end + 1):
            self.image_data[i - 1]["wm"] = True
        self.update_treeview()

    def mark_blur_range(self):
        start_s = self.entry_range_start.get()
        end_s = self.entry_range_end.get()
        if not (start_s.isdigit() and end_s.isdigit()):
            messagebox.showerror("Lỗi", "STT phải là số.")
            return
        start = int(start_s)
        end = int(end_s)
        if start < 1:
            start = 1
        if end > len(self.image_data):
            end = len(self.image_data)
        if start > end:
            messagebox.showerror("Lỗi", "STT bắt đầu phải nhỏ hơn hoặc bằng STT kết thúc.")
            return
        for i in range(len(self.image_data)):
            self.image_data[i]["blur"] = False
        for i in range(start, end + 1):
            self.image_data[i - 1]["blur"] = True
        self.update_treeview()

    def uncheck_all(self):
        for data in self.image_data:
            data["blur"] = False
            data["wm"] = False
        self.update_treeview()

    def on_header_click(self, col):
        if col == "blur":
            self.blur_all_selected = not self.blur_all_selected
            for data in self.image_data:
                data["blur"] = self.blur_all_selected
        elif col == "wm":
            self.wm_all_selected = not self.wm_all_selected
            for data in self.image_data:
                data["wm"] = self.wm_all_selected
        self.update_treeview()

    # ========================================================
    #  HÀM ÁP DỤNG BLUR & WATERMARK TRƯỚC KHI LƯU
    # ========================================================
    def apply_blur_effect(self, img):
        img_blurred = img.filter(ImageFilter.GaussianBlur(5))
        pixel_size = 10
        w, h = img.size
        return img_blurred.resize((w // pixel_size, h // pixel_size), Image.NEAREST).resize(img.size, Image.NEAREST)

    # --- Hàm apply_watermark_full được cải tiến:
    #     Dán watermark trực tiếp (giống Merge Down của PTS) mà không ép chỉnh mask alpha, 
    #     nhằm giữ nguyên độ mờ (opacity) gốc của ảnh watermark.
    def apply_watermark_full(self, img):
        if not self.original_img_size or not self.preview_size:
            return img
        orig_w, orig_h = self.original_img_size
        preview_w, preview_h = self.preview_size
        scale = orig_w / preview_w
        wm = self.resize_watermark(int(self.wm_size * scale))
        if not wm:
            return img
        actual_x = int(self.wm_position[0] * scale)
        actual_y = int(self.wm_position[1] * scale)
        # Dán watermark trực tiếp vào ảnh, sử dụng mask alpha theo giá trị gốc của watermark
        img.paste(wm, (actual_x, actual_y), wm)
        return img

    # ========================================================
    #  LƯU ẢNH THEO CÁC CHẾ ĐỘ
    # ========================================================
    def save_watermarked_images_to_folder(self):
        if not self.image_data or not self.image_folder:
            messagebox.showerror("Lỗi", "Chưa chọn folder chứa ảnh.")
            return
        images_to_process = [data["path"] for data in self.image_data if data["wm"]]
        if not images_to_process:
            messagebox.showinfo("Thông báo", "Không có ảnh nào được chọn Watermark.")
            return
        new_folder = self.image_folder
        if self.save_mode.get() == "new":
            folder_name = os.path.basename(self.image_folder)
            new_folder = os.path.join(self.image_folder, f"{folder_name}_watermark")
            os.makedirs(new_folder, exist_ok=True)
        for img_path in images_to_process:
            try:
                img = Image.open(img_path).convert("RGBA")
                watermarked_img = self.apply_watermark_full(img)
                base_name = os.path.basename(img_path)
                save_path = os.path.join(new_folder, base_name)
                watermarked_img.save(save_path, "PNG")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể lưu ảnh {img_path}: {e}")
        self.save_config()
        messagebox.showinfo("Completed", f"Watermarked images have been saved to:\n{new_folder}")

    def save_blurred_images_to_folder(self):
        if not self.image_data or not self.image_folder:
            messagebox.showerror("Lỗi", "Chưa chọn folder chứa ảnh.")
            return
        images_to_process = [data["path"] for data in self.image_data if data["blur"]]
        if not images_to_process:
            messagebox.showinfo("Thông báo", "Không có ảnh nào được chọn Blur.")
            return
        new_folder = self.image_folder
        if self.save_mode.get() == "new":
            folder_name = os.path.basename(self.image_folder)
            new_folder = os.path.join(self.image_folder, f"{folder_name}_blurred")
            os.makedirs(new_folder, exist_ok=True)
        for img_path in images_to_process:
            try:
                img = Image.open(img_path)
                img_blurred = self.apply_blur_effect(img)
                base_name = os.path.basename(img_path)
                save_path = os.path.join(new_folder, base_name)
                img_blurred.save(save_path)
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể xử lý ảnh {img_path}: {e}")
        messagebox.showinfo("Completed", f"Blurred images have been saved to:\n{new_folder}")

    def save_blurred_and_watermarked_images_to_folder(self):
        """
        Xử lý từng ảnh theo:
         - Nếu chỉ tick Blur → chỉ blur.
         - Nếu chỉ tick Watermark → chỉ watermark.
         - Nếu tick cả hai → blur trước, sau đó watermark.
        """
        if not self.image_data or not self.image_folder:
            messagebox.showerror("Lỗi", "Chưa chọn folder chứa ảnh.")
            return
        images_to_process = [data["path"] for data in self.image_data if data["blur"] or data["wm"]]
        if not images_to_process:
            messagebox.showinfo("Thông báo", "Không có ảnh nào được chọn Blur hoặc Watermark.")
            return
        new_folder = self.image_folder
        if self.save_mode.get() == "new":
            folder_name = os.path.basename(self.image_folder)
            new_folder = os.path.join(self.image_folder, f"{folder_name}_blur_watermark")
            os.makedirs(new_folder, exist_ok=True)
        for img_path in images_to_process:
            try:
                img = Image.open(img_path).convert("RGBA")
                index = None
                for i, data in enumerate(self.image_data):
                    if data["path"] == img_path:
                        index = i
                        break
                if index is not None:
                    if self.image_data[index]["blur"]:
                        img = self.apply_blur_effect(img)
                        img = img.convert("RGBA")
                    if self.image_data[index]["wm"]:
                        img = self.apply_watermark_full(img)
                base_name = os.path.basename(img_path)
                save_path = os.path.join(new_folder, base_name)
                img.save(save_path, "PNG")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể xử lý ảnh {img_path}: {e}")
        messagebox.showinfo("Completed", f"Processed images have been saved to:\n{new_folder}")

# ============================================================
#  CHẠY CHƯƠNG TRÌNH
# ============================================================
if __name__ == "__main__":
    root = tb.Window(themename="flatly")
    app = WatermarkApp(root)
    root.mainloop()
