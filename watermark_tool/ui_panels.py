import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import ImageTk, Image

class UIPanels:
    def __init__(self, root, image_processor, config_manager):
        self.root = root
        self.image_processor = image_processor
        self.config_manager = config_manager

        # Khung chính 3 cột: Trái (panel watermark), Giữa (preview), Phải (danh sách ảnh)
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(side="top", fill="both", expand=True)
        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.rowconfigure(0, weight=1)

        # Panel trái
        self.init_left_panel(self.main_frame)
        # Panel giữa
        self.init_center_panel(self.main_frame)
        # Panel phải
        self.init_right_panel(self.main_frame)

    # --- (1a) Panel bên trái ---
    def init_left_panel(self, parent):
        self.left_frame = ttk.Frame(parent, padding=10)
        self.left_frame.grid(row=0, column=0, sticky="ns")

        ttk.Label(self.left_frame, text="(1) Watermark Controls",
                  font=("Helvetica", 12, "bold")).pack(pady=(0,10))
        
        # Các nút: Chọn, Đăng ký, Xóa watermark
        frame_select = ttk.Frame(self.left_frame)
        frame_select.pack(fill="x", pady=5)
        self.btn_select_wm = ttk.Button(frame_select, text="Chọn Ảnh Watermark",
                                        command=self.on_select_watermark)
        self.btn_select_wm.pack(side="left", expand=True, fill="x", padx=2)

        self.btn_register_wm = ttk.Button(frame_select, text="Đăng ký Watermark",
                                          command=self.on_register_watermark)
        self.btn_register_wm.pack(side="left", expand=True, fill="x", padx=2)

        self.btn_delete_wm = ttk.Button(frame_select, text="Xóa Watermark",
                                        command=self.on_delete_watermark)
        self.btn_delete_wm.pack(side="left", expand=True, fill="x", padx=2)
        
        # Preset vị trí watermark
        frame_preset = ttk.Frame(self.left_frame)
        frame_preset.pack(fill="x", pady=5)
        ttk.Label(frame_preset, text="Preset vị trí:").pack(side="left", padx=2)
        self.btn_center_wm = ttk.Button(frame_preset, text="Căn Giữa",
                                        command=self.on_set_center)
        self.btn_center_wm.pack(side="left", padx=2)
        self.btn_bottom_right_wm = ttk.Button(frame_preset, text="Góc Dưới Phải",
                                              command=self.on_set_bottom_right)
        self.btn_bottom_right_wm.pack(side="left", padx=2)
        
        # Thanh trượt kích thước watermark
        frame_slider = ttk.Frame(self.left_frame)
        frame_slider.pack(fill="x", pady=10)
        ttk.Label(frame_slider, text="Chỉnh kích thước watermark:").pack(anchor="w")
        self.size_slider = ttk.Scale(frame_slider, from_=10, to=300,
                                     orient=tk.HORIZONTAL,
                                     command=self.on_size_slider_change)
        self.size_slider.set(self.image_processor.wm_size)
        self.size_slider.pack(fill="x", pady=2)
        
        # Danh sách watermark đã đăng ký
        ttk.Label(self.left_frame, text="Watermark Đã đăng ký:",
                  anchor="w").pack(pady=(10,0), fill="x")
        self.wm_listbox = tk.Listbox(self.left_frame, height=8,
                                     font=("Helvetica", 10))
        self.wm_listbox.pack(fill="both", expand=True, pady=5)
        self.wm_listbox.bind("<<ListboxSelect>>", self.on_select_registered_watermark)
        
        # Canvas hiển thị watermark
        self.wm_canvas = tk.Canvas(self.left_frame, width=150, height=150,
                                   bg="white", bd=2, relief="sunken")
        self.wm_canvas.pack(pady=10)
        self.image_processor.wm_canvas = self.wm_canvas

    # --- (1b) Panel giữa: Preview & Folder chọn ---
    def init_center_panel(self, parent):
        self.center_frame = ttk.Frame(parent, padding=10)
        self.center_frame.grid(row=0, column=1, sticky="nsew")
        self.center_frame.columnconfigure(0, weight=1)
        self.center_frame.rowconfigure(1, weight=1)
        
        folder_frame = ttk.Frame(self.center_frame)
        folder_frame.grid(row=0, column=0, sticky="ew")
        self.btn_select_folder = ttk.Button(folder_frame, text="Chọn Folder Ảnh",
                                            command=self.on_select_folder)
        self.btn_select_folder.pack(side="left", padx=2)
        
        self.img_canvas = tk.Canvas(self.center_frame, bg="white", bd=2,
                                    relief="sunken")
        self.img_canvas.grid(row=1, column=0, sticky="nsew", pady=10)
        self.img_canvas.bind("<B1-Motion>", self.on_move_watermark)
        self.img_canvas.bind("<MouseWheel>", self.on_zoom_watermark)
        self.img_canvas.bind("<Button-4>", self.on_zoom_watermark)
        self.img_canvas.bind("<Button-5>", self.on_zoom_watermark)
        self.img_canvas.bind("<Configure>", self.on_canvas_resize)

    # --- (1c) Panel bên phải: Danh sách ảnh + (4) Lưu & Chọn Tất Cả ---
    def init_right_panel(self, parent):
        self.right_frame = ttk.Frame(parent, padding=10)
        self.right_frame.grid(row=0, column=2, sticky="ns")

        ttk.Label(self.right_frame, text="(3) Danh sách Ảnh",
                  font=("Helvetica", 12, "bold")).pack(pady=(0,10))
        
        # Canvas hiển thị list ảnh
        self.right_canvas = tk.Canvas(self.right_frame, bg="#e8f0fe")
        self.right_scrollbar = ttk.Scrollbar(self.right_frame,
                                             orient="vertical",
                                             command=self.right_canvas.yview)
        self.right_canvas.configure(yscrollcommand=self.right_scrollbar.set)
        self.right_scrollbar.pack(side="right", fill="y")
        self.image_check_frame = ttk.Frame(self.right_canvas)
        self.right_canvas.create_window((0,0), window=self.image_check_frame,
                                        anchor="nw")
        self.right_canvas.pack(fill="both", expand=True)
        self.image_check_frame.bind("<Configure>",
            lambda e: self.right_canvas.configure(
                scrollregion=self.right_canvas.bbox("all")))

        # Tạo label_total (hiển thị tổng số ảnh)
        self.label_total = ttk.Label(self.right_frame, text="Tổng: 0 ảnh",
                                     font=("Helvetica", 10, "bold"))
        self.label_total.pack(anchor="w", pady=(0,5))

        # Điền danh sách ảnh (gồm cột STT, Ảnh, Watermark, Blur)
        self.populate_image_checkbuttons()

        # Vùng trung gian hiển thị a,b + nút “Chọn Wm [a->b]”, “Chọn Blur [a->b]”
        gap2_frame = ttk.Frame(self.right_frame, padding=5, relief="groove")
        gap2_frame.pack(side="top", fill="x", pady=5)

        row_ab = ttk.Frame(gap2_frame)
        row_ab.pack(fill="x", pady=2)
        ttk.Label(row_ab, text="a:").pack(side="left", padx=2)
        self.entry_a = ttk.Entry(row_ab, width=5)
        self.entry_a.pack(side="left", padx=5)

        ttk.Label(row_ab, text="b:").pack(side="left", padx=2)
        self.entry_b = ttk.Entry(row_ab, width=5)
        self.entry_b.pack(side="left", padx=5)

        row_buttons = ttk.Frame(gap2_frame)
        row_buttons.pack(fill="x", pady=5)
        btn_range_wm = ttk.Button(row_buttons, text="Chọn Wm [a->b]",
                                  command=self.on_select_range_wm)
        btn_range_blur = ttk.Button(row_buttons, text="Chọn Blur [a->b]",
                                    command=self.on_select_range_blur)
        btn_range_wm.pack(side="left", padx=5)
        btn_range_blur.pack(side="left", padx=5)

        # Khoảng đệm
        gap_frame = ttk.Frame(self.right_frame, height=20)
        gap_frame.pack(side="top", fill="x", pady=(5,0))

        # (4) Lưu & Chọn Tất Cả (cỡ nhỏ)
        style = ttk.Style()
        style.configure("Small.TButton", font=("Helvetica", 9))
        style.configure("Small.TRadiobutton", font=("Helvetica", 9))

        bottom_4_frame = ttk.Frame(self.right_frame)
        bottom_4_frame.pack(side="top", fill="x", pady=5)

        ttk.Label(
            bottom_4_frame,
            text="(4) Lưu & Chọn Tất Cả",
            font=("Helvetica", 10, "bold")
        ).pack(side="top", anchor="w", pady=(0,5))

        # Hàng 1: 3 nút Lưu
        row1_frame = ttk.Frame(bottom_4_frame)
        row1_frame.pack(side="top", fill="x")
        
        self.btn_save_watermark = ttk.Button(row1_frame, text="Lưu Ảnh Watermark",
                                             style="Small.TButton",
                                             command=self.on_save_watermarked_images)
        self.btn_save_blur = ttk.Button(row1_frame, text="Lưu Ảnh Blur",
                                        style="Small.TButton",
                                        command=self.on_save_blurred_images)
        self.btn_save_blur_watermark = ttk.Button(row1_frame, text="Lưu Ảnh Blur & Watermark",
                                                  style="Small.TButton",
                                                  command=self.on_save_blur_watermarked_images)
        
        self.btn_save_watermark.pack(side="left", expand=True, fill="x", padx=2, pady=2)
        self.btn_save_blur.pack(side="left", expand=True, fill="x", padx=2, pady=2)
        self.btn_save_blur_watermark.pack(side="left", expand=True, fill="x", padx=2, pady=2)

        # Hàng 2: CHUYỂN 2 nút “Chọn Tất Cả Watermark”, “Chọn Tất Cả Blur”
        # thành 2 checkbox “Chọn Tất Cả Wm”, “Chọn Tất Cả Blur”.
        row2_frame = ttk.Frame(bottom_4_frame)
        row2_frame.pack(side="top", fill="x")

        # Checkbox: “Chọn Tất Cả Wm”
        self.cb_select_all_wm_var = tk.BooleanVar(value=False)
        self.cb_select_all_wm = ttk.Checkbutton(
            row2_frame,
            text="Chọn Tất Cả Wm",
            variable=self.cb_select_all_wm_var,
            command=self.on_cb_select_all_wm
        )
        self.cb_select_all_wm.pack(side="left", expand=True, fill="x", padx=2, pady=2)

        # Checkbox: “Chọn Tất Cả Blur”
        self.cb_select_all_blur_var = tk.BooleanVar(value=False)
        self.cb_select_all_blur = ttk.Checkbutton(
            row2_frame,
            text="Chọn Tất Cả Blur",
            variable=self.cb_select_all_blur_var,
            command=self.on_cb_select_all_blur
        )
        self.cb_select_all_blur.pack(side="left", expand=True, fill="x", padx=2, pady=2)

        # Nút “Chọn Tất Cả Ảnh” (vẫn là nút, set watermark=1, blur=1)
        self.btn_select_all = ttk.Button(row2_frame, text="Chọn Tất Cả Ảnh",
                                         style="Small.TButton",
                                         command=self.on_select_all_images)
        self.btn_select_all.pack(side="left", expand=True, fill="x", padx=2, pady=2)

        # Hàng 3: Radio “Lưu vào folder mới / Lưu đè file gốc”
        row3_frame = ttk.Frame(bottom_4_frame)
        row3_frame.pack(side="top", fill="x", pady=(5,0))
        
        self.save_mode = tk.StringVar(value="new")
        ttk.Radiobutton(row3_frame, text="Lưu vào folder mới",
                        style="Small.TRadiobutton",
                        variable=self.save_mode, value="new").pack(side="left", padx=5)
        ttk.Radiobutton(row3_frame, text="Lưu đè file gốc",
                        style="Small.TRadiobutton",
                        variable=self.save_mode, value="overwrite").pack(side="left", padx=5)

    # --- Danh sách ảnh (bên phải) ---
    def populate_image_checkbuttons(self):
        """
        Cột 0: STT
        Cột 1: Ảnh
        Cột 2: Watermark
        Cột 3: Blur

        Cập nhật label_total = “Tổng: X ảnh”
        """
        for widget in self.image_check_frame.winfo_children():
            widget.destroy()
        
        # Header
        header_stt = ttk.Label(self.image_check_frame, text="STT",
                               font=("Helvetica", 10, "bold"))
        header_stt.grid(row=0, column=0, padx=5, pady=2, sticky="w")

        header_lbl = ttk.Label(self.image_check_frame, text="Ảnh",
                               font=("Helvetica", 10, "bold"))
        header_lbl.grid(row=0, column=1, padx=5, pady=2, sticky="w")

        header_wm = ttk.Label(self.image_check_frame, text="Watermark",
                              font=("Helvetica", 10, "bold"))
        header_wm.grid(row=0, column=2, padx=5, pady=2)

        header_blur = ttk.Label(self.image_check_frame, text="Blur",
                                font=("Helvetica", 10, "bold"))
        header_blur.grid(row=0, column=3, padx=5, pady=2)
        
        if hasattr(self.image_processor, 'image_paths'):
            self.image_wm_vars = {}
            total_images = len(self.image_processor.image_paths)
            if total_images > 0:
                self.label_total.configure(text=f"Tổng: {total_images} ảnh")
            else:
                self.label_total.configure(text="Tổng: 0 ảnh")

            for i, img_path in enumerate(self.image_processor.image_paths, start=1):
                # STT
                lbl_stt = ttk.Label(self.image_check_frame, text=str(i),
                                    font=("Helvetica", 10))
                lbl_stt.grid(row=i, column=0, padx=5, pady=2, sticky="w")

                # Tên ảnh
                lbl = ttk.Label(self.image_check_frame,
                                text=os.path.basename(img_path),
                                font=("Helvetica", 10), cursor="hand2")
                lbl.grid(row=i, column=1, padx=5, pady=2, sticky="w")
                lbl.bind("<Button-1>", lambda e, p=img_path: self.on_select_single_image(p))
                
                # Watermark
                var_wm = tk.IntVar(value=1)
                cb_wm = ttk.Checkbutton(self.image_check_frame, variable=var_wm)
                cb_wm.grid(row=i, column=2, padx=5, pady=2)
                self.image_wm_vars[img_path] = var_wm

                # Blur
                var_blur = tk.IntVar(value=0)
                cb_blur = ttk.Checkbutton(self.image_check_frame, variable=var_blur)
                cb_blur.grid(row=i, column=3, padx=5, pady=2)
                self.image_processor.image_blur_vars[img_path] = var_blur

    # --- Sự kiện click vào tên ảnh (preview) ---
    def on_select_single_image(self, path):
        self.image_processor.set_preview_image(path)

    # --- Chọn watermark [a->b], bỏ hết watermark cũ trước khi set [a..b] ---
    def on_select_range_wm(self):
        try:
            a = int(self.entry_a.get())
            b = int(self.entry_b.get())
            total = len(self.image_processor.image_paths)
            if a < 1 or b < 1 or a > b or b > total:
                raise ValueError

            # Bỏ tích hết watermark trước
            for path in self.image_processor.image_paths:
                if path in self.image_wm_vars:
                    self.image_wm_vars[path].set(0)

            # Sau đó chỉ tích [a..b]
            for i in range(a, b + 1):
                path = self.image_processor.image_paths[i - 1]
                if path in self.image_wm_vars:
                    self.image_wm_vars[path].set(1)
        except:
            messagebox.showerror("Lỗi", "Vui lòng nhập a, b hợp lệ (1 <= a <= b <= tổng ảnh)")

    # --- Chọn blur [a->b], bỏ hết blur cũ trước khi set [a..b] ---
    def on_select_range_blur(self):
        """Tương tự on_select_range_wm, nhưng với blur."""
        try:
            a = int(self.entry_a.get())
            b = int(self.entry_b.get())
            total = len(self.image_processor.image_paths)
            if a < 1 or b < 1 or a > b or b > total:
                raise ValueError
            # Bỏ tích hết blur
            for path in self.image_processor.image_paths:
                self.image_processor.image_blur_vars[path].set(0)
            # Tích [a..b]
            for i in range(a, b+1):
                path = self.image_processor.image_paths[i-1]
                self.image_processor.image_blur_vars[path].set(1)
        except:
            messagebox.showerror("Lỗi",
                "Vui lòng nhập a, b hợp lệ (1 <= a <= b <= tổng ảnh)")

    # --- Các hàm xử lý sự kiện cũ ---
    def on_select_watermark(self):
        self.image_processor.load_watermark()
        self.refresh_ui()
    
    def on_register_watermark(self):
        self.image_processor.register_watermark()
        self.refresh_ui()
    
    def on_delete_watermark(self):
        selection = self.wm_listbox.curselection()
        if selection:
            index = selection[0]
            self.image_processor.delete_registered_watermark(index)
            self.refresh_ui()
        else:
            messagebox.showerror("Lỗi", "Vui lòng chọn watermark cần xóa.")
    
    def on_set_center(self):
        self.image_processor.set_watermark_position_center()
        self.refresh_ui()
    
    def on_set_bottom_right(self):
        self.image_processor.set_watermark_position_bottom_right()
        self.refresh_ui()
    
    def on_size_slider_change(self, value):
        self.image_processor.wm_size = int(float(value))
        self.image_processor.display_watermark()
        self.image_processor.show_preview()
    
    def on_select_folder(self):
        self.image_processor.load_images()
        self.populate_image_checkbuttons()
        self.image_processor.display_selected_image()
    
    def on_move_watermark(self, event):
        self.image_processor.move_watermark(event)
    
    def on_zoom_watermark(self, event):
        self.image_processor.zoom_watermark(event)

    # --- Chuyển 2 nút “Chọn Tất Cả Wm”, “Chọn Tất Cả Blur” thành checkbox ---
    def on_cb_select_all_wm(self):
        """Nếu tick => set watermark=1 cho tất cả, un-tick => set watermark=0 cho tất cả."""
        if self.cb_select_all_wm_var.get():
            # Tick
            for path in self.image_processor.image_paths:
                self.image_wm_vars[path].set(1)
        else:
            # Un-tick
            for path in self.image_processor.image_paths:
                self.image_wm_vars[path].set(0)

    def on_cb_select_all_blur(self):
        """Nếu tick => set blur=1 cho tất cả, un-tick => set blur=0 cho tất cả."""
        if self.cb_select_all_blur_var.get():
            for path in self.image_processor.image_paths:
                self.image_processor.image_blur_vars[path].set(1)
        else:
            for path in self.image_processor.image_paths:
                self.image_processor.image_blur_vars[path].set(0)

    # --- Nút “Chọn Tất Cả Ảnh” (áp dụng watermark + blur =1) ---
    def on_select_all_images(self):
        for path in self.image_processor.image_paths:
            self.image_wm_vars[path].set(1)
            self.image_processor.image_blur_vars[path].set(1)
    
    def on_save_watermarked_images(self):
        self.image_processor.save_watermarked_images_to_folder(self.save_mode.get())
    
    def on_save_blurred_images(self):
        self.image_processor.save_blurred_images_to_folder(self.save_mode.get())
    
    def on_save_blur_watermarked_images(self):
        self.image_processor.save_blurred_and_watermarked_images_to_folder(self.save_mode.get())
    
    def on_select_registered_watermark(self, event):
        selection = self.wm_listbox.curselection()
        if selection:
            index = selection[0]
            self.image_processor.select_registered_watermark(index)
            self.refresh_ui()
    
    def on_canvas_resize(self, event):
        self.image_processor.img_canvas = self.img_canvas
        self.image_processor.on_canvas_resize(event)
    
    def refresh_ui(self):
        self.image_processor.show_preview()
        self.image_processor.display_watermark()
        self.populate_image_checkbuttons()
        # Cập nhật listbox watermark
        self.wm_listbox.delete(0, tk.END)
        for wm in self.image_processor.registered_watermarks:
            self.wm_listbox.insert(tk.END, wm["filename"])

    def load_watermark(self):
        if self.image_processor.watermark_path:
            self.image_processor.load_watermark(self.image_processor.watermark_path)
            self.refresh_ui()
