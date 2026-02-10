import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from PIL import Image, ImageTk
import os
import shutil
from pathlib import Path
import threading

class ImageOrganizer:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Organizer Pro")
        self.root.geometry("1400x900")
        self.root.configure(bg="#1a1a1a")
        
        # Variables
        self.source_folder1 = None
        self.source_folder2 = None
        self.current_images = []
        self.current_index = 0
        self.dataset_folders = []
        self.photo_image = None
        self.thumbnail_cache = {}
        self.image_cache = {}  # Cache cho ảnh chính
        self.loading = False
        
        self.setup_ui()
        self.bind_shortcuts()
        
    def setup_ui(self):
        # Main container
        main_container = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, bg="#1a1a1a")
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Left sidebar
        sidebar = tk.Frame(main_container, bg="#2a2a2a", width=350)
        main_container.add(sidebar)
        
        # Source folders section
        tk.Label(sidebar, text="FOLDER NGUỒN", bg="#2a2a2a", fg="white", 
                font=("Arial", 12, "bold")).pack(pady=10)
        
        # Folder 1
        btn_frame1 = tk.Frame(sidebar, bg="#2a2a2a")
        btn_frame1.pack(fill=tk.X, padx=10, pady=5)
        tk.Button(btn_frame1, text="Load Folder 1", command=lambda: self.load_folder(1),
                 bg="#2196F3", fg="white", font=("Arial", 10)).pack(fill=tk.X)
        
        self.folder1_label = tk.Label(sidebar, text="Chưa chọn", bg="#2a2a2a", 
                                     fg="#888", wraplength=320)
        self.folder1_label.pack(padx=10, pady=2)
        
        # Folder 2 with Create Folder button
        btn_frame2 = tk.Frame(sidebar, bg="#2a2a2a")
        btn_frame2.pack(fill=tk.X, padx=10, pady=5)
        
        folder2_btn = tk.Button(btn_frame2, text="Load Folder 2", command=lambda: self.load_folder(2),
                 bg="#2196F3", fg="white", font=("Arial", 10))
        folder2_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        create_folder_btn = tk.Button(btn_frame2, text="+ Folder", 
                                     command=self.create_folder_in_folder2,
                                     bg="#FF9800", fg="white", font=("Arial", 9, "bold"))
        create_folder_btn.pack(side=tk.LEFT, padx=(5,0))
        
        self.folder2_label = tk.Label(sidebar, text="Chưa chọn", bg="#2a2a2a", 
                                     fg="#888", wraplength=320)
        self.folder2_label.pack(padx=10, pady=2)
        
        # Dataset folders section
        tk.Label(sidebar, text="DATASET FOLDERS", bg="#2a2a2a", fg="white",
                font=("Arial", 12, "bold")).pack(pady=(20,10))
        
        dataset_btn_frame = tk.Frame(sidebar, bg="#2a2a2a")
        dataset_btn_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Button(dataset_btn_frame, text="+ Tạo Dataset Folder", 
                 command=self.create_dataset_folder,
                 bg="#4CAF50", fg="white", font=("Arial", 10, "bold")).pack(fill=tk.X)
        
        # Scrollable frame for dataset folders
        canvas_frame = tk.Frame(sidebar, bg="#2a2a2a")
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        canvas = tk.Canvas(canvas_frame, bg="#2a2a2a", highlightthickness=0)
        scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        self.dataset_list_frame = tk.Frame(canvas, bg="#2a2a2a")
        
        self.dataset_list_frame.bind("<Configure>", 
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        canvas.create_window((0, 0), window=self.dataset_list_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Info panel
        self.info_label = tk.Label(sidebar, text="0/0", bg="#2a2a2a", fg="white",
                                  font=("Arial", 11))
        self.info_label.pack(side=tk.BOTTOM, pady=10)
        
        # Right panel - Image viewer
        right_panel = tk.Frame(main_container, bg="#000")
        main_container.add(right_panel)
        
        # Toolbar
        toolbar = tk.Frame(right_panel, bg="#333", height=60)
        toolbar.pack(fill=tk.X, side=tk.TOP)
        
        tk.Label(toolbar, text="PHÍM TẮT:", bg="#333", fg="white",
                font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=10)
        
        shortcuts = [
            ("← →", "Prev/Next"), ("1-9", "Dataset"), 
            ("Ctrl+1-9", "Dataset 10-18"), ("Del", "Delete"), ("R", "Refresh")
        ]
        
        for key, desc in shortcuts:
            frame = tk.Frame(toolbar, bg="#444", relief=tk.RAISED, borderwidth=1)
            frame.pack(side=tk.LEFT, padx=5, pady=10)
            tk.Label(frame, text=key, bg="#555", fg="#FFD700", 
                    font=("Courier", 9, "bold"), padx=5).pack(side=tk.LEFT)
            tk.Label(frame, text=desc, bg="#444", fg="white",
                    font=("Arial", 9), padx=5).pack(side=tk.LEFT)
        
        # Image display area
        self.image_frame = tk.Frame(right_panel, bg="#000")
        self.image_frame.pack(fill=tk.BOTH, expand=True)
        
        self.image_label = tk.Label(self.image_frame, bg="#000")
        self.image_label.pack(expand=True)
        
        # Navigation buttons
        self.btn_prev = tk.Button(self.image_frame, text="◄", command=self.prev_image,
                                 font=("Arial", 32, "bold"), 
                                 bg="#555555", fg="white", 
                                 bd=2, padx=20, pady=20, 
                                 cursor="hand2", relief=tk.RAISED,
                                 activebackground="#666666")
        self.btn_prev.place(relx=0.05, rely=0.5, anchor="center")
        
        self.btn_next = tk.Button(self.image_frame, text="►", command=self.next_image,
                                 font=("Arial", 32, "bold"), 
                                 bg="#555555", fg="white", 
                                 bd=2, padx=20, pady=20, 
                                 cursor="hand2", relief=tk.RAISED,
                                 activebackground="#666666")
        self.btn_next.place(relx=0.95, rely=0.5, anchor="center")
        
        # Hover effects
        self.btn_prev.bind("<Enter>", lambda e: self.btn_prev.config(bg="#777777"))
        self.btn_prev.bind("<Leave>", lambda e: self.btn_prev.config(bg="#555555"))
        self.btn_next.bind("<Enter>", lambda e: self.btn_next.config(bg="#777777"))
        self.btn_next.bind("<Leave>", lambda e: self.btn_next.config(bg="#555555"))
        
        # Current filename display
        self.filename_label = tk.Label(right_panel, text="", bg="#333", fg="white",
                                      font=("Arial", 11), pady=5)
        self.filename_label.pack(fill=tk.X, side=tk.BOTTOM)
        
    def bind_shortcuts(self):
        """Bind keyboard shortcuts"""
        self.root.bind('<Left>', lambda e: self.prev_image())
        self.root.bind('<Right>', lambda e: self.next_image())
        self.root.bind('<Delete>', lambda e: self.delete_current_image())
        self.root.bind('r', lambda e: self.refresh_images())
        self.root.bind('R', lambda e: self.refresh_images())
        
        # Bind 1-9 cho dataset 1-9
        for i in range(1, 10):
            self.root.bind(str(i), lambda e, num=i: self.move_to_dataset(num-1))
        
        # Bind Ctrl+1-9 cho dataset 10-18
        for i in range(1, 10):
            self.root.bind(f'<Control-Key-{i}>', lambda e, num=i: self.move_to_dataset(num+8))
        
        # Bind Alt+1-9 cho dataset 19-27
        for i in range(1, 10):
            self.root.bind(f'<Alt-Key-{i}>', lambda e, num=i: self.move_to_dataset(num+17))
    
    def scan_folder2_for_datasets(self):
        """Auto-scan Folder 2 để tìm các dataset có cấu trúc data_name/dataset/"""
        if not self.source_folder2:
            return
        
        folder2_path = Path(self.source_folder2)
        found_datasets = []
        
        # Duyệt tất cả các folder con trong Folder 2
        for item in folder2_path.iterdir():
            if item.is_dir():
                # Kiểm tra xem có subfolder "dataset" không
                dataset_folder = item / "dataset"
                if dataset_folder.exists() and dataset_folder.is_dir():
                    # Tìm thấy dataset hợp lệ
                    found_datasets.append({
                        'name': item.name,
                        'path': str(item),
                        'dataset_folder': str(dataset_folder)
                    })
        
        # Thêm vào danh sách (tránh trùng lặp)
        for new_dataset in found_datasets:
            # Kiểm tra xem đã có chưa
            exists = any(d['path'] == new_dataset['path'] for d in self.dataset_folders)
            if not exists:
                self.dataset_folders.append(new_dataset)
        
        if found_datasets:
            self.update_dataset_list()
            self.root.title(f"✓ Tìm thấy {len(found_datasets)} dataset")
            self.root.after(2000, lambda: self.root.title("Image Organizer Pro"))
    
    def load_folder(self, folder_num):
        """Load source folder"""
        folder = filedialog.askdirectory(title=f"Chọn Folder {folder_num}")
        if folder:
            if folder_num == 1:
                self.source_folder1 = folder
                self.folder1_label.config(text=folder, fg="white")
            else:
                self.source_folder2 = folder
                self.folder2_label.config(text=folder, fg="white")
                # Auto-scan Folder 2 để tìm dataset
                self.scan_folder2_for_datasets()
            
            self.refresh_images()
    
    def create_folder_in_folder2(self):
        """Tạo folder mới trong folder 2"""
        if not self.source_folder2:
            messagebox.showwarning("Cảnh báo", "Vui lòng load Folder 2 trước!")
            return
        
        folder_name = simpledialog.askstring("Tạo Folder Mới", 
                                            "Nhập tên folder:",
                                            parent=self.root)
        if folder_name:
            new_folder_path = Path(self.source_folder2) / folder_name
            try:
                new_folder_path.mkdir(exist_ok=True)
                messagebox.showinfo("Thành công", f"Đã tạo folder: {folder_name}")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể tạo folder:\n{str(e)}")
    
    def refresh_images(self):
        """Refresh image list from both source folders - OPTIMIZED"""
        self.current_images = []
        
        for folder in [self.source_folder1, self.source_folder2]:
            if folder and os.path.exists(folder):
                folder_path = Path(folder)
                # Chỉ lấy ảnh ở root level của folder, không duyệt vào subfolder
                for item in folder_path.iterdir():
                    if item.is_file() and item.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
                        self.current_images.append(item)
        
        self.current_images = sorted(self.current_images)
        
        if self.current_index >= len(self.current_images):
            self.current_index = max(0, len(self.current_images) - 1)
        
        # Clear cache khi refresh
        self.image_cache.clear()
        
        self.display_image()
        # Preload next image
        self.preload_next_image()
    
    def preload_next_image(self):
        """Preload ảnh tiếp theo để tăng tốc độ chuyển ảnh"""
        if not self.current_images or self.loading:
            return
        
        next_index = (self.current_index + 1) % len(self.current_images)
        if next_index not in self.image_cache:
            threading.Thread(target=self._load_image_to_cache, args=(next_index,), daemon=True).start()
    
    def _load_image_to_cache(self, index):
        """Load ảnh vào cache (chạy trong background thread)"""
        if index >= len(self.current_images):
            return
        
        try:
            img_path = self.current_images[index]
            img = Image.open(img_path)
            
            # Resize để fit window
            max_width = 1000
            max_height = 700
            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
            # Lưu vào cache
            self.image_cache[index] = img.copy()
        except:
            pass
    
    def display_image(self):
        """Display current image - OPTIMIZED với cache"""
        if not self.current_images:
            self.image_label.config(image='', text="Không có ảnh nào\nVui lòng load folder",
                                   fg="white", font=("Arial", 16))
            self.filename_label.config(text="")
            self.info_label.config(text="0/0")
            return
        
        if self.current_index < 0:
            self.current_index = len(self.current_images) - 1
        elif self.current_index >= len(self.current_images):
            self.current_index = 0
        
        img_path = self.current_images[self.current_index]
        
        try:
            # Kiểm tra cache trước
            if self.current_index in self.image_cache:
                img = self.image_cache[self.current_index]
            else:
                img = Image.open(img_path)
                max_width = self.image_frame.winfo_width() - 200
                max_height = self.image_frame.winfo_height() - 100
                
                if max_width <= 0 or max_height <= 0:
                    max_width, max_height = 1000, 700
                
                img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                # Lưu vào cache
                self.image_cache[self.current_index] = img.copy()
            
            self.photo_image = ImageTk.PhotoImage(img)
            self.image_label.config(image=self.photo_image, text="")
            
            self.filename_label.config(text=img_path.name)
            self.info_label.config(text=f"{self.current_index + 1}/{len(self.current_images)}")
            
            # Preload next image
            self.preload_next_image()
            
        except Exception as e:
            self.image_label.config(image='', text=f"Lỗi load ảnh:\n{str(e)}",
                                   fg="red", font=("Arial", 12))
    
    def prev_image(self):
        """Go to previous image (circular) - FAST"""
        if self.current_images and not self.loading:
            self.current_index -= 1
            if self.current_index < 0:
                self.current_index = len(self.current_images) - 1
            self.display_image()
    
    def next_image(self):
        """Go to next image (circular) - FAST"""
        if self.current_images and not self.loading:
            self.current_index += 1
            if self.current_index >= len(self.current_images):
                self.current_index = 0
            self.display_image()
    
    def get_preview_image(self, dataset_path):
        """Lấy ảnh preview - BẤT KỲ ẢNH NÀO ở root level của data_name"""
        dataset_path = Path(dataset_path)
        
        if str(dataset_path) in self.thumbnail_cache:
            return self.thumbnail_cache[str(dataset_path)]
        
        # Tìm ảnh ở root level (ngoài folder dataset)
        image_files = []
        for item in dataset_path.iterdir():
            if item.is_file() and item.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
                image_files.append(item)
        
        if image_files:
            try:
                img = Image.open(image_files[0])
                img.thumbnail((80, 80), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.thumbnail_cache[str(dataset_path)] = photo
                return photo
            except:
                pass
        
        return None
    
    def create_dataset_folder(self):
        """Tạo dataset folder với cấu trúc data_name/dataset/"""
        if not self.source_folder2:
            messagebox.showwarning("Cảnh báo", 
                                 "Vui lòng load Folder 2 trước khi tạo dataset!")
            return
        
        dataset_name = simpledialog.askstring("Tạo Dataset Folder", 
                                             "Nhập tên dataset:",
                                             parent=self.root)
        
        if not dataset_name or not dataset_name.strip():
            return
        
        dataset_name = dataset_name.strip()
        
        try:
            dataset_root = Path(self.source_folder2) / dataset_name
            dataset_root.mkdir(exist_ok=True)
            
            dataset_folder = dataset_root / "dataset"
            dataset_folder.mkdir(exist_ok=True)
            
            self.dataset_folders.append({
                'name': dataset_name,
                'path': str(dataset_root),
                'dataset_folder': str(dataset_folder)
            })
            
            self.update_dataset_list()
            
            messagebox.showinfo("Thành công", 
                              f"Đã tạo dataset '{dataset_name}'\n\n" +
                              f"Cấu trúc:\n{dataset_name}/\n" +
                              f"  dataset/ (ảnh sẽ được chuyển vào đây)\n\n" +
                              f"Tip: Đặt 1 ảnh ở ngoài folder 'dataset' để làm thumbnail preview")
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tạo dataset:\n{str(e)}")
    
    def update_dataset_list(self):
        """Update dataset list với thumbnail preview"""
        for widget in self.dataset_list_frame.winfo_children():
            widget.destroy()
        
        for idx, dataset in enumerate(self.dataset_folders, 1):
            frame = tk.Frame(self.dataset_list_frame, bg="#333", relief=tk.RAISED, 
                           borderwidth=2)
            frame.pack(fill=tk.X, pady=5, padx=5)
            
            btn_frame = tk.Frame(frame, bg="#444", cursor="hand2")
            btn_frame.pack(fill=tk.X)
            btn_frame.bind("<Button-1>", lambda e, idx=idx: self.move_to_dataset(idx-1))
            
            # Thumbnail preview
            preview_img = self.get_preview_image(dataset['path'])
            if preview_img:
                thumb_label = tk.Label(btn_frame, image=preview_img, bg="#444", cursor="hand2")
                thumb_label.image = preview_img
                thumb_label.pack(side=tk.LEFT, padx=5, pady=5)
                thumb_label.bind("<Button-1>", lambda e, idx=idx: self.move_to_dataset(idx-1))
            
            info_frame = tk.Frame(btn_frame, bg="#444", cursor="hand2")
            info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            info_frame.bind("<Button-1>", lambda e, idx=idx: self.move_to_dataset(idx-1))
            
            # Hiển thị phím tắt
            if idx <= 9:
                shortcut_text = f"[{idx}]"
            elif idx <= 18:
                shortcut_text = f"[Ctrl+{idx-9}]"
            elif idx <= 27:
                shortcut_text = f"[Alt+{idx-18}]"
            else:
                shortcut_text = f"[{idx}]"
            
            shortcut_label = tk.Label(info_frame, text=shortcut_text, bg="#FFD700", fg="black",
                    font=("Arial", 9, "bold"), padx=5, cursor="hand2")
            shortcut_label.pack(anchor="w", pady=2)
            shortcut_label.bind("<Button-1>", lambda e, idx=idx: self.move_to_dataset(idx-1))
            
            name_label = tk.Label(info_frame, text=dataset['name'], bg="#444", fg="white",
                    font=("Arial", 10, "bold"), anchor="w", cursor="hand2")
            name_label.pack(anchor="w", padx=5)
            name_label.bind("<Button-1>", lambda e, idx=idx: self.move_to_dataset(idx-1))
            
            # Hover effect
            def on_enter(e, f=btn_frame):
                f.config(bg="#555")
                for child in f.winfo_children():
                    if isinstance(child, tk.Label) or isinstance(child, tk.Frame):
                        child.config(bg="#555")
                        if isinstance(child, tk.Frame):
                            for subchild in child.winfo_children():
                                if isinstance(subchild, tk.Label) and subchild['bg'] != "#FFD700":
                                    subchild.config(bg="#555")
            
            def on_leave(e, f=btn_frame):
                f.config(bg="#444")
                for child in f.winfo_children():
                    if isinstance(child, tk.Label) or isinstance(child, tk.Frame):
                        child.config(bg="#444")
                        if isinstance(child, tk.Frame):
                            for subchild in child.winfo_children():
                                if isinstance(subchild, tk.Label) and subchild['bg'] != "#FFD700":
                                    subchild.config(bg="#444")
            
            btn_frame.bind("<Enter>", on_enter)
            btn_frame.bind("<Leave>", on_leave)
    
    def move_to_dataset(self, dataset_index):
        """Move current image TRỰC TIẾP vào dataset folder - OPTIMIZED"""
        if not self.current_images or dataset_index >= len(self.dataset_folders):
            return
        
        dataset = self.dataset_folders[dataset_index]
        src_path = self.current_images[self.current_index]
        dest_folder = Path(dataset['dataset_folder'])
        dest_path = dest_folder / src_path.name
        
        try:
            counter = 1
            while dest_path.exists():
                stem = src_path.stem
                dest_path = dest_folder / f"{stem}_{counter}{src_path.suffix}"
                counter += 1
            
            shutil.move(str(src_path), str(dest_path))
            
            # Remove from list và cache
            if self.current_index in self.image_cache:
                del self.image_cache[self.current_index]
            
            self.current_images.pop(self.current_index)
            
            # Rebuild cache keys
            new_cache = {}
            for key, value in self.image_cache.items():
                if key > self.current_index:
                    new_cache[key - 1] = value
                elif key < self.current_index:
                    new_cache[key] = value
            self.image_cache = new_cache
            
            if self.current_index >= len(self.current_images) and self.current_images:
                self.current_index = len(self.current_images) - 1
            
            self.display_image()
            
            # Clear thumbnail cache
            if str(dataset['path']) in self.thumbnail_cache:
                del self.thumbnail_cache[str(dataset['path'])]
            
            self.root.title(f"✓ Đã chuyển vào {dataset['name']}/dataset/")
            self.root.after(1500, lambda: self.root.title("Image Organizer Pro"))
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể chuyển file:\n{str(e)}")
    
    def delete_current_image(self):
        """Delete current image - OPTIMIZED"""
        if not self.current_images:
            return
        
        result = messagebox.askyesno("Xác nhận", 
                                     f"Bạn có chắc muốn xóa ảnh này?\n\n{self.current_images[self.current_index].name}")
        if result:
            try:
                os.remove(self.current_images[self.current_index])
                
                # Remove from cache
                if self.current_index in self.image_cache:
                    del self.image_cache[self.current_index]
                
                self.current_images.pop(self.current_index)
                
                # Rebuild cache keys
                new_cache = {}
                for key, value in self.image_cache.items():
                    if key > self.current_index:
                        new_cache[key - 1] = value
                    elif key < self.current_index:
                        new_cache[key] = value
                self.image_cache = new_cache
                
                if self.current_index >= len(self.current_images) and self.current_images:
                    self.current_index = len(self.current_images) - 1
                
                self.display_image()
                
                self.root.title("✓ Đã xóa ảnh")
                self.root.after(1500, lambda: self.root.title("Image Organizer Pro"))
                
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể xóa file:\n{str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageOrganizer(root)
    root.mainloop()
