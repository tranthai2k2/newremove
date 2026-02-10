import os
import pickle
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageFilter

class WatermarkApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Watermark Tool")
        self.root.geometry("1150x700")
        self.root.configure(bg="#e8f0fe")
        
        # -- Các thuộc tính liên quan đến ảnh, watermark, folder --
        self.watermark_image = None
        self.original_watermark_image = None
        self.watermark_path = None
        self.selected_image_path = None
        
        # Danh sách đường dẫn ảnh + biến checkbox
        self.image_data = []  # Mỗi phần tử: {"path":..., "blur_var":..., "wm_var":...}
        self.image_folder = None
        
        # -- Biến xử lý watermark --
        self.wm_position = (10, 10)
        self.wm_size = 50
        
        # -- Preview --
        self.original_img_size = None
        self.preview_size = None
        self.preview_offset = (0, 0)
        
        # -- Kéo thả watermark --
        self.dragging = False
        self.drag_offset = (0, 0)
        
        # -- File cấu hình --
        self.config_file = "watermark_config.pkl"
        self.registered_watermarks_file = "registered_watermarks.pkl"
        self.registered_watermarks = []
        
        # -- Tải cấu hình cũ --
        self.load_config()
        
        # -- Khung chính: chia 3 vùng (trái - giữa - phải) --
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(side="top", fill="both", expand=True)
        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.rowconfigure(0, weight=1)
        
        self.init_left_panel(self.main_frame)
        self.init_center_panel(self.main_frame)
        self.init_right_panel(self.main_frame)
        self.init_bottom_panel()
        
        if self.watermark_path:
            self.load_watermark(self.watermark_path)
        
        self.populate_registered_watermarks_listbox()
    
    # ============================
    #  LOAD/SAVE CẤU HÌNH
    # ============================
    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "rb") as f:
                    config = pickle.load(f)
                if isinstance(config, dict):
                    self.watermark_path = config.get("watermark_path")
                    self.wm_size = config.get("wm_size", 50)
                    self.wm_position = config.get("wm_position", (10, 10))
            except:
                pass
        
        if os.path.exists(self.registered_watermarks_file):
            try:
                with open(self.registered_watermarks_file, "rb") as f:
                    data = pickle.load(f)
                if data and isinstance(data, list):
                    if len(data) > 0 and isinstance(data[0], dict):
                        self.registered_watermarks = data
                    else:
                        self.registered_watermarks = []
                        for item in data:
                            if len(item) == 3:
                                wm = {"filename": item[0], "path": item[1], "wm_size": item[2]}
                            else:
                                wm = {"filename": item[0], "path": item[1], "wm_size": 50}
                            self.registered_watermarks.append(wm)
            except:
                pass
    
    def save_config(self):
        config = {
            "watermark_path": self.watermark_path,
            "wm_size": self.wm_size,
            "wm_position": self.wm_position
        }
        try:
            with open(self.config_file, "wb") as f:
                pickle.dump(config, f)
        except:
            pass
    
    def save_registered_watermarks(self):
        try:
            with open(self.registered_watermarks_file, "wb") as f:
                pickle.dump(self.registered_watermarks, f)
        except:
            pass
    
    # ===============================
    #  GIAO DIỆN: 3 VÙNG
    # ===============================
    def init_left_panel(self, parent) -> None:
        self.left_frame = ttk.Frame(parent, padding=10)
        self.left_frame.grid(row=0, column=0, sticky="ns")
        
        ttk.Label(self.left_frame, text="Watermark Controls", font=("Helvetica", 12, "bold")).pack(pady=(0,10))
        
        frame_select = ttk.Frame(self.left_frame)
        frame_select.pack(fill="x", pady=5)
        
        try:
            self.icon_watermark = tk.PhotoImage(file="icon_watermark.png")
        except:
            self.icon_watermark = None
        
        ttk.Button(frame_select, text="Chọn Ảnh Watermark",
                   image=self.icon_watermark,
                   compound="left",
                   command=self.load_watermark).pack(side="left", expand=True, fill="x", padx=2)
        
        ttk.Button(frame_select, text="Đăng ký Watermark", command=self.register_watermark).pack(side="left", expand=True, fill="x", padx=2)
        ttk.Button(frame_select, text="Xóa Watermark", command=self.delete_registered_watermark).pack(side="left", expand=True, fill="x", padx=2)
        
        frame_preset = ttk.Frame(self.left_frame)
        frame_preset.pack(fill="x", pady=5)
        ttk.Label(frame_preset, text="Preset vị trí:").pack(side="left", padx=2)
        ttk.Button(frame_preset, text="Căn Giữa", command=self.set_watermark_position_center).pack(side="left", padx=2)
        ttk.Button(frame_preset, text="Góc Dưới Phải", command=self.set_watermark_position_bottom_right).pack(side="left", padx=2)
        
        frame_slider = ttk.Frame(self.left_frame)
        frame_slider.pack(fill="x", pady=10)
        ttk.Label(frame_slider, text="Chỉnh kích thước watermark:").pack(anchor="w")
        self.size_slider = ttk.Scale(frame_slider, from_=10, to=300, orient=tk.HORIZONTAL, command=self.on_size_slider_change)
        self.size_slider.set(self.wm_size)
        self.size_slider.pack(fill="x", pady=2)
        
        ttk.Label(self.left_frame, text="Watermark Đã đăng ký:", anchor="w").pack(pady=(10,0), fill="x")
        self.wm_listbox = tk.Listbox(self.left_frame, height=8, font=("Helvetica", 10))
        self.wm_listbox.pack(fill="both", expand=True, pady=5)
        self.wm_listbox.bind("<<ListboxSelect>>", self.select_registered_watermark)
        
        self.wm_canvas = tk.Canvas(self.left_frame, width=150, height=150, bg="white", bd=2, relief="sunken")
        self.wm_canvas.pack(pady=10)
    
    def init_center_panel(self, parent) -> None:
        self.center_frame = ttk.Frame(parent, padding=10)
        self.center_frame.grid(row=0, column=1, sticky="nsew")
        self.center_frame.columnconfigure(0, weight=1)
        self.center_frame.rowconfigure(1, weight=1)
        
        folder_frame = ttk.Frame(self.center_frame)
        folder_frame.grid(row=0, column=0, sticky="ew")
        ttk.Button(folder_frame, text="Chọn Folder Ảnh", command=self.load_images).pack(side="left", padx=2)
        
        self.img_canvas = tk.Canvas(self.center_frame, bg="white", bd=2, relief="sunken")
        self.img_canvas.grid(row=1, column=0, sticky="nsew", pady=10)
        
        self.img_canvas.bind("<Button-1>", self.start_drag)
        self.img_canvas.bind("<B1-Motion>", self.do_drag)
        self.img_canvas.bind("<ButtonRelease-1>", self.stop_drag)
        
        self.img_canvas.bind("<MouseWheel>", self.zoom_watermark)
        self.img_canvas.bind("<Button-4>", self.zoom_watermark)
        self.img_canvas.bind("<Button-5>", self.zoom_watermark)
        
        self.img_canvas.bind("<Configure>", self.on_canvas_resize)
    
    def init_right_panel(self, parent) -> None:
        """
        Vùng danh sách ảnh: STT | Ảnh | Blur | Watermark
        Thêm nút Bỏ chọn tất cả + chọn STT a->b
        """
        self.right_frame = ttk.Frame(parent, padding=10)
        self.right_frame.grid(row=0, column=2, sticky="ns")
        
        # Tiêu đề
        ttk.Label(self.right_frame, text="Danh sách Ảnh", font=("Helvetica", 12, "bold")).pack(pady=(0,10))
        
        # Frame chứa các nút & entry
        top_controls_frame = ttk.Frame(self.right_frame)
        top_controls_frame.pack(fill="x", pady=5)
        
        # 2 dòng: 
        #   Dòng 1: [Chọn STT từ ... đến ...] [Watermark A->B] [Blur A->B]
        #   Dòng 2: [Bỏ chọn tất cả]
        
        # Dòng 1
        row1_frame = ttk.Frame(top_controls_frame)
        row1_frame.pack(fill="x", pady=2)
        
        ttk.Label(row1_frame, text="Chọn STT từ:").pack(side="left", padx=2)
        self.entry_range_start = ttk.Entry(row1_frame, width=5)
        self.entry_range_start.pack(side="left", padx=2)
        
        ttk.Label(row1_frame, text="đến:").pack(side="left", padx=2)
        self.entry_range_end = ttk.Entry(row1_frame, width=5)
        self.entry_range_end.pack(side="left", padx=2)
        
        ttk.Button(row1_frame, text="Watermark A->B", command=self.mark_watermark_range).pack(side="left", padx=5)
        ttk.Button(row1_frame, text="Blur A->B", command=self.mark_blur_range).pack(side="left", padx=5)
        
        # Dòng 2: nút Bỏ chọn tất cả
        row2_frame = ttk.Frame(top_controls_frame)
        row2_frame.pack(fill="x", pady=2)
        ttk.Button(row2_frame, text="Bỏ chọn tất cả", command=self.uncheck_all).pack(side="left", padx=5)
        
        # Bảng hiển thị
        self.table_canvas = tk.Canvas(self.right_frame, bg="#e8f0fe", highlightthickness=0)
        self.table_canvas.pack(side="left", fill="both", expand=True)
        
        self.table_scrollbar = ttk.Scrollbar(self.right_frame, orient="vertical", command=self.table_canvas.yview)
        self.table_scrollbar.pack(side="right", fill="y")
        self.table_canvas.configure(yscrollcommand=self.table_scrollbar.set)
        
        self.table_frame = ttk.Frame(self.table_canvas)
        self.table_canvas.create_window((0, 0), window=self.table_frame, anchor="nw")
        self.table_frame.bind("<Configure>", lambda e: self.table_canvas.configure(scrollregion=self.table_canvas.bbox("all")))
        
        # Header
        header_frame = ttk.Frame(self.table_frame)
        header_frame.pack(fill="x")
        
        self.blur_all_selected = False
        self.wm_all_selected = False
        
        lbl_stt = ttk.Label(header_frame, text="STT", width=5, anchor="center", font=("Helvetica", 10, "bold"))
        lbl_stt.grid(row=0, column=0, padx=5, pady=2)
        
        lbl_name = ttk.Label(header_frame, text="Ảnh", width=20, anchor="center", font=("Helvetica", 10, "bold"))
        lbl_name.grid(row=0, column=1, padx=5, pady=2)
        
        lbl_blur = ttk.Label(header_frame, text="Blur", width=10, anchor="center", font=("Helvetica", 10, "bold"))
        lbl_blur.grid(row=0, column=2, padx=5, pady=2)
        lbl_blur.bind("<Button-1>", self.on_header_blur_click)
        
        lbl_wm = ttk.Label(header_frame, text="Watermark", width=10, anchor="center", font=("Helvetica", 10, "bold"))
        lbl_wm.grid(row=0, column=3, padx=5, pady=2)
        lbl_wm.bind("<Button-1>", self.on_header_wm_click)
        
        self.data_frame = ttk.Frame(self.table_frame)
        self.data_frame.pack(fill="both", expand=True)
    
    def init_bottom_panel(self) -> None:
        self.bottom_frame = ttk.Frame(self.root, padding=10)
        self.bottom_frame.pack(side="bottom", fill="x")
        
        ttk.Button(self.bottom_frame, text="Lưu Ảnh Watermark", command=self.save_watermarked_images_to_folder).pack(side="left", padx=5)
        ttk.Button(self.bottom_frame, text="Lưu Ảnh Blur", command=self.save_blurred_images_to_folder).pack(side="left", padx=5)
        ttk.Button(self.bottom_frame, text="Lưu Ảnh Blur & Watermark", command=self.save_blurred_and_watermarked_images_to_folder).pack(side="left", padx=5)
        
        frame_save_mode = ttk.Frame(self.bottom_frame)
        frame_save_mode.pack(side="right", padx=5)
        self.save_mode = tk.StringVar(value="new")
        ttk.Radiobutton(frame_save_mode, text="Lưu vào folder mới", variable=self.save_mode, value="new").pack(side="left", padx=2)
        ttk.Radiobutton(frame_save_mode, text="Lưu đè file gốc", variable=self.save_mode, value="overwrite").pack(side="left", padx=2)
    
    # ==========================
    #  HÀM XỬ LÝ SỰ KIỆN
    # ==========================
    def on_size_slider_change(self, value) -> None:
        self.wm_size = int(float(value))
        self.display_watermark()
        self.show_preview()
    
    def on_header_blur_click(self, event):
        self.blur_all_selected = not self.blur_all_selected
        for d in self.image_data:
            d["blur_var"].set(1 if self.blur_all_selected else 0)
    
    def on_header_wm_click(self, event):
        self.wm_all_selected = not self.wm_all_selected
        for d in self.image_data:
            d["wm_var"].set(1 if self.wm_all_selected else 0)
    
    def uncheck_all(self):
        """
        Bỏ chọn tất cả (Blur, Watermark) cho mọi ảnh.
        """
        for d in self.image_data:
            d["blur_var"].set(0)
            d["wm_var"].set(0)
    
    def mark_watermark_range(self):
        """
        Bỏ chọn tất cả watermark, rồi chỉ chọn STT a->b.
        """
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
        
        # Bỏ chọn tất cả watermark trước
        for d in self.image_data:
            d["wm_var"].set(0)
        
        # Chỉ chọn watermark cho STT từ start -> end
        for i in range(start, end+1):
            self.image_data[i-1]["wm_var"].set(1)
    
    def mark_blur_range(self):
        """
        Bỏ chọn tất cả blur, rồi chỉ chọn STT a->b.
        """
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
        
        # Bỏ chọn tất cả blur trước
        for d in self.image_data:
            d["blur_var"].set(0)
        
        # Chỉ chọn blur cho STT từ start -> end
        for i in range(start, end+1):
            self.image_data[i-1]["blur_var"].set(1)
    
    # ============================
    #  KÉO THẢ WATERMARK
    # ============================
    def start_drag(self, event):
        if not (self.preview_size and self.original_watermark_image):
            return
        offset_x, offset_y = self.preview_offset
        local_x = event.x - offset_x
        local_y = event.y - offset_y
        
        wm_img = self.resize_watermark(self.wm_size)
        wm_w, wm_h = wm_img.size
        
        if (self.wm_position[0] <= local_x <= self.wm_position[0] + wm_w and
            self.wm_position[1] <= local_y <= self.wm_position[1] + wm_h):
            self.dragging = True
            dx = local_x - self.wm_position[0]
            dy = local_y - self.wm_position[1]
            self.drag_offset = (dx, dy)
        else:
            self.dragging = False
    
    def do_drag(self, event):
        if not self.dragging:
            return
        offset_x, offset_y = self.preview_offset
        preview_w, preview_h = self.preview_size
        
        wm_img = self.resize_watermark(self.wm_size)
        wm_w, wm_h = wm_img.size
        
        local_x = event.x - offset_x
        local_y = event.y - offset_y
        
        new_x = local_x - self.drag_offset[0]
        new_y = local_y - self.drag_offset[1]
        
        if new_x < 0: 
            new_x = 0
        if new_y < 0: 
            new_y = 0
        if new_x + wm_w > preview_w:
            new_x = preview_w - wm_w
        if new_y + wm_h > preview_h:
            new_y = preview_h - wm_h
        
        self.wm_position = (new_x, new_y)
        self.show_preview()
    
    def stop_drag(self, event):
        self.dragging = False
    
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
        self.size_slider.set(self.wm_size)
        self.display_watermark()
        self.show_preview()
    
    # =====================
    #  HIỂN THỊ PREVIEW
    # =====================
    def on_canvas_resize(self, event: tk.Event) -> None:
        self.show_preview()
    
    def show_preview(self) -> None:
        if not self.img_canvas or not self.selected_image_path:
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
            preview_w = int(base_img.width * ratio)
            preview_h = int(base_img.height * ratio)
            offset_x = (canvas_w - preview_w) // 2
            offset_y = (canvas_h - preview_h) // 2
            
            self.preview_size = (preview_w, preview_h)
            self.preview_offset = (offset_x, offset_y)
            
            preview_img = base_img.resize((preview_w, preview_h), Image.Resampling.LANCZOS)
            if self.original_watermark_image:
                preview_img = self.apply_watermark(preview_img)
            
            self.img_tk = ImageTk.PhotoImage(preview_img)
            self.img_canvas.delete("all")
            self.img_canvas.create_image(offset_x, offset_y, anchor="nw", image=self.img_tk)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể hiển thị ảnh: {e}")
    
    def apply_watermark(self, preview_img: Image.Image) -> Image.Image:
        wm_resized = self.resize_watermark(self.wm_size)
        if not wm_resized:
            return preview_img
        x, y = int(self.wm_position[0]), int(self.wm_position[1])
        preview_img.paste(wm_resized, (x, y), wm_resized)
        return preview_img
    
    def resize_watermark(self, size: int) -> Image.Image:
        if not self.original_watermark_image:
            return None
        w, h = self.original_watermark_image.size
        ratio = w / h
        new_w = size
        new_h = int(size / ratio)
        return self.original_watermark_image.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    def display_watermark(self) -> None:
        if not self.original_watermark_image:
            self.wm_canvas.delete("all")
            return
        wm_resized = self.resize_watermark(self.wm_size)
        if wm_resized:
            tk_img = ImageTk.PhotoImage(wm_resized)
            self.wm_canvas.delete("all")
            cx = self.wm_canvas.winfo_width() // 2
            cy = self.wm_canvas.winfo_height() // 2
            self.wm_canvas.create_image(cx, cy, image=tk_img)
            self.wm_canvas.image = tk_img
    
    # ===========================
    #  QUẢN LÝ WATERMARK
    # ===========================
    def load_watermark(self, path: str = None) -> None:
        if not path:
            path = filedialog.askopenfilename(filetypes=[("PNG files", "*.png")])
        if path:
            try:
                self.watermark_path = path
                img = Image.open(path).convert("RGBA")
                self.original_watermark_image = img
                self.display_watermark()
                self.show_preview()
                self.save_config()
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể tải watermark: {e}")
    
    def register_watermark(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("PNG files", "*.png")])
        if path:
            try:
                filename = os.path.basename(path)
                wm_data = {"filename": filename, "path": path, "wm_size": self.wm_size}
                self.registered_watermarks.append(wm_data)
                self.save_registered_watermarks()
                self.populate_registered_watermarks_listbox()
                messagebox.showinfo("Thành công", "Watermark đã được đăng ký.")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể đăng ký watermark: {e}")
    
    def delete_registered_watermark(self) -> None:
        selection = self.wm_listbox.curselection()
        if not selection:
            messagebox.showerror("Lỗi", "Vui lòng chọn watermark cần xóa.")
            return
        index = selection[0]
        answer = messagebox.askyesno("Xác nhận", "Bạn có chắc muốn xóa watermark đã đăng ký này không?")
        if answer:
            del self.registered_watermarks[index]
            self.save_registered_watermarks()
            self.populate_registered_watermarks_listbox()
            messagebox.showinfo("Thông báo", "Đã xóa watermark đã đăng ký.")
    
    def select_registered_watermark(self, event: tk.Event) -> None:
        selection = self.wm_listbox.curselection()
        if selection:
            index = selection[0]
            wm = self.registered_watermarks[index]
            try:
                img = Image.open(wm["path"]).convert("RGBA")
                self.original_watermark_image = img
                self.wm_size = wm["wm_size"]
                self.size_slider.set(self.wm_size)
                self.display_watermark()
                self.show_preview()
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể tải watermark: {e}")
    
    def populate_registered_watermarks_listbox(self) -> None:
        self.wm_listbox.delete(0, tk.END)
        for wm in self.registered_watermarks:
            self.wm_listbox.insert(tk.END, wm["filename"])
    
    # ====================
    #  LƯU ẢNH
    # ====================
    def load_images(self) -> None:
        folder = filedialog.askdirectory()
        if folder:
            self.image_folder = folder
            try:
                files = [f for f in os.listdir(folder) if f.lower().endswith((".jpg", ".png", ".jpeg"))]
                self.image_data.clear()
                for i, filename in enumerate(files, start=1):
                    path = os.path.join(folder, filename)
                    self.image_data.append({
                        "path": path,
                        "blur_var": tk.IntVar(value=0),
                        "wm_var": tk.IntVar(value=0)
                    })
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể tải ảnh từ folder: {e}")
                return
            
            # Vẽ lại bảng
            for widget in self.data_frame.winfo_children():
                widget.destroy()
            for i, d in enumerate(self.image_data, start=1):
                lbl_stt = ttk.Label(self.data_frame, text=str(i), width=5, anchor="center")
                lbl_stt.grid(row=i, column=0, padx=5, pady=2)
                
                lbl_name = ttk.Label(self.data_frame, text=os.path.basename(d["path"]), width=20, anchor="center")
                lbl_name.grid(row=i, column=1, padx=5, pady=2)
                lbl_name.bind("<Button-1>", lambda e, idx=i: self.set_selected_image(idx))
                
                cb_blur = ttk.Checkbutton(self.data_frame, variable=d["blur_var"], width=10)
                cb_blur.grid(row=i, column=2, padx=5, pady=2)
                
                cb_wm = ttk.Checkbutton(self.data_frame, variable=d["wm_var"], width=10)
                cb_wm.grid(row=i, column=3, padx=5, pady=2)
            
            if self.image_data:
                self.set_selected_image(1)
    
    def set_selected_image(self, index: int):
        if 1 <= index <= len(self.image_data):
            self.selected_image_path = self.image_data[index-1]["path"]
            self.show_preview()
    
    def save_watermarked_images_to_folder(self) -> None:
        if not self.image_data or not self.image_folder:
            messagebox.showerror("Lỗi", "Chưa chọn folder chứa ảnh.")
            return
        images_to_process = [d["path"] for d in self.image_data if d["wm_var"].get() == 1]
        if not images_to_process:
            messagebox.showinfo("Thông báo", "Không có ảnh nào được chọn Watermark.")
            return
        folder_name = os.path.basename(self.image_folder)
        if self.save_mode.get() == "new":
            new_folder = os.path.join(self.image_folder, f"{folder_name}_watermark")
            if not os.path.exists(new_folder):
                os.makedirs(new_folder)
        else:
            new_folder = self.image_folder
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
    
    def save_blurred_images_to_folder(self) -> None:
        if not self.image_data or not self.image_folder:
            messagebox.showerror("Lỗi", "Chưa chọn folder chứa ảnh.")
            return
        images_to_process = [d["path"] for d in self.image_data if d["blur_var"].get() == 1]
        if not images_to_process:
            messagebox.showinfo("Thông báo", "Không có ảnh nào được chọn Blur.")
            return
        folder_name = os.path.basename(self.image_folder)
        if self.save_mode.get() == "new":
            new_folder = os.path.join(self.image_folder, f"{folder_name}_blurred")
            if not os.path.exists(new_folder):
                os.makedirs(new_folder)
        else:
            new_folder = self.image_folder
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
    
    def save_blurred_and_watermarked_images_to_folder(self) -> None:
        if not self.image_data or not self.image_folder:
            messagebox.showerror("Lỗi", "Chưa chọn folder chứa ảnh.")
            return
        images_to_process = [d["path"] for d in self.image_data if d["blur_var"].get() == 1 and d["wm_var"].get() == 1]
        if not images_to_process:
            messagebox.showinfo("Thông báo", "Không có ảnh nào được chọn Blur & Watermark.")
            return
        folder_name = os.path.basename(self.image_folder)
        if self.save_mode.get() == "new":
            new_folder = os.path.join(self.image_folder, f"{folder_name}_blur_watermark")
            if not os.path.exists(new_folder):
                os.makedirs(new_folder)
        else:
            new_folder = self.image_folder
        for img_path in images_to_process:
            try:
                img = Image.open(img_path)
                img_blurred = self.apply_blur_effect(img)
                img_blurred = img_blurred.convert("RGBA")
                watermarked_img = self.apply_watermark_full(img_blurred)
                base_name = os.path.basename(img_path)
                save_path = os.path.join(new_folder, base_name)
                watermarked_img.save(save_path, "PNG")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể xử lý ảnh {img_path}: {e}")
        messagebox.showinfo("Completed", f"Blurred & Watermarked images have been saved to:\n{new_folder}")
    
    # ==========================
    #  XỬ LÝ WATERMARK CHO FILE
    # ==========================
    def apply_blur_effect(self, img: Image.Image) -> Image.Image:
        img_blurred = img.filter(ImageFilter.GaussianBlur(5))
        pixel_size = 10
        w, h = img.size
        img_pixelated = img_blurred.resize((w // pixel_size, h // pixel_size), Image.NEAREST).resize(img.size, Image.NEAREST)
        return img_pixelated
    
    def apply_watermark_full(self, img: Image.Image) -> Image.Image:
        if not self.original_img_size or not self.preview_size:
            return img
        orig_w, orig_h = self.original_img_size
        preview_w, preview_h = self.preview_size
        if preview_w == 0 or preview_h == 0:
            return img
        
        scale = orig_w / preview_w
        wm_resized = self.resize_watermark(int(self.wm_size * scale))
        if not wm_resized:
            return img
        
        actual_x = int(self.wm_position[0] * scale)
        actual_y = int(self.wm_position[1] * scale)
        img.paste(wm_resized, (actual_x, actual_y), wm_resized)
        return img
    
    # =============================
    #  PRESET VỊ TRÍ WATERMARK
    # =============================
    def set_watermark_position_center(self) -> None:
        if not (self.preview_size and self.original_watermark_image):
            messagebox.showwarning("Thông báo", "Vui lòng chọn ảnh trước!")
            return
        preview_w, preview_h = self.preview_size
        wm_resized = self.resize_watermark(self.wm_size)
        wm_w, wm_h = wm_resized.size
        new_x = (preview_w - wm_w) // 2
        new_y = (preview_h - wm_h) // 2
        self.wm_position = (new_x, new_y)
        self.show_preview()
    
    def set_watermark_position_bottom_right(self) -> None:
        if not (self.preview_size and self.original_watermark_image):
            messagebox.showwarning("Thông báo", "Vui lòng chọn ảnh trước!")
            return
        preview_w, preview_h = self.preview_size
        wm_resized = self.resize_watermark(self.wm_size)
        wm_w, wm_h = wm_resized.size
        new_x = preview_w - wm_w
        new_y = preview_h - wm_h
        self.wm_position = (new_x, new_y)
        self.show_preview()

if __name__ == "__main__":
    root = tk.Tk()
    app = WatermarkApp(root)
    root.mainloop()
