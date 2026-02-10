import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
from pathlib import Path
import os
import json
import subprocess
import platform

CONFIG_FILE = "viewer_config.json"


class ImageViewer:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Image Viewer - Clean Start")
        self.root.geometry("1400x800")

        # State
        self.main_folder: str = ""
        self.subfolders: list = []
        self.current_folder_index: int = 0

        # Data
        self.thumbnail_images = {}
        self.main_images = []
        self.txt_files = []

        # Widgets
        self.thumb_canvas = None
        self.thumb_container = None
        self.image_labels = []
        self.txt_listbox = None
        self.txt_content = None
        self.folder_label = None
        self.path_label = None
        self.open_folder_btn = None

        # Load config rồi tạo UI
        self.load_config()
        self.create_widgets()

        # Keyboard
        self.root.bind("<Up>", lambda e: self.prev_folder())
        self.root.bind("<Down>", lambda e: self.next_folder())
        self.root.bind("<Left>", lambda e: self.prev_folder())
        self.root.bind("<Right>", lambda e: self.next_folder())

        # Nếu có folder cũ thì load
        if self.main_folder and os.path.isdir(self.main_folder):
            self.load_main_folder(self.main_folder)

    # ================== UI ==================

    def create_widgets(self):
        # Top bar
        top_bar = tk.Frame(self.root, bg="#34495e", height=60)
        top_bar.pack(fill=tk.X)
        top_bar.pack_propagate(False)

        btn_choose = tk.Button(
            top_bar,
            text="📁 Chọn Thư Mục Chính",
            command=self.select_main_folder,
            bg="#e74c3c",
            fg="white",
            font=("Arial", 12, "bold"),
            width=22,
            height=2,
            cursor="hand2",
        )
        btn_choose.pack(side=tk.LEFT, padx=15, pady=8)

        self.path_label = tk.Label(
            top_bar,
            text="Chưa chọn thư mục",
            bg="#34495e",
            fg="#ecf0f1",
            font=("Arial", 10),
            anchor="w",
        )
        self.path_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

        hint_label = tk.Label(
            top_bar,
            text="↑ ↓ ← → để chuyển folder | 🖱️ Cuộn để scroll thumbnail",
            bg="#34495e",
            fg="#bdc3c7",
            font=("Arial", 9, "italic"),
        )
        hint_label.pack(side=tk.RIGHT, padx=15)

        # Main container
        main = tk.Frame(self.root, bg="#ecf0f1")
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Panel 1: Thumbnails
        panel1 = tk.LabelFrame(
            main,
            text="📁 Thumbnails",
            font=("Arial", 12, "bold"),
            bg="#f8f9fa",
        )
        panel1.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Nút scroll lên/xuống
        btns_scroll = tk.Frame(panel1, bg="#f8f9fa")
        btns_scroll.pack(fill=tk.X, padx=5, pady=5)

        tk.Button(
            btns_scroll,
            text="▲ Lên",
            command=lambda: self.thumb_canvas.yview_scroll(-3, "units"),
            bg="#3498db",
            fg="white",
            font=("Arial", 10, "bold"),
        ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=3)

        tk.Button(
            btns_scroll,
            text="▼ Xuống",
            command=lambda: self.thumb_canvas.yview_scroll(3, "units"),
            bg="#3498db",
            fg="white",
            font=("Arial", 10, "bold"),
        ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=3)

        # Canvas + scrollbar cho thumbnails
        self.thumb_canvas = tk.Canvas(panel1, width=260, bg="white", highlightthickness=0)
        thumb_scroll = ttk.Scrollbar(panel1, orient="vertical", command=self.thumb_canvas.yview)
        self.thumb_container = tk.Frame(self.thumb_canvas, bg="white")

        self.thumb_canvas.create_window((0, 0), window=self.thumb_container, anchor="nw")
        self.thumb_canvas.configure(yscrollcommand=thumb_scroll.set)

        self.thumb_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        thumb_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.thumb_container.bind(
            "<Configure>",
            lambda e: self.thumb_canvas.configure(scrollregion=self.thumb_canvas.bbox("all")),
        )

        # Cuộn bằng chuột
        self.thumb_canvas.bind_all("<MouseWheel>", self.on_mouse_wheel)

        # Panel 2: 9 ảnh chính
        panel2 = tk.LabelFrame(
            main,
            text="🖼️ Xem Ảnh (9 ảnh)",
            font=("Arial", 12, "bold"),
        )
        panel2.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        nav = tk.Frame(panel2, bg="white")
        nav.pack(fill=tk.X, padx=5, pady=5)

        tk.Button(
            nav,
            text="⬆️ Folder Trước",
            command=self.prev_folder,
            bg="#27ae60",
            fg="white",
            font=("Arial", 10, "bold"),
            width=16,
        ).pack(side=tk.LEFT, padx=5, pady=5)

        self.folder_label = tk.Label(
            nav,
            text="Chưa chọn thư mục",
            bg="white",
            fg="#2980b9",
            font=("Arial", 11, "bold"),
        )
        self.folder_label.pack(side=tk.LEFT, padx=10, pady=5)

        tk.Button(
            nav,
            text="⬇️ Folder Sau",
            command=self.next_folder,
            bg="#2980b9",
            fg="white",
            font=("Arial", 10, "bold"),
            width=16,
        ).pack(side=tk.LEFT, padx=5, pady=5)

        # Nút mở folder
        self.open_folder_btn = tk.Button(
            nav,
            text="📂 Mở",
            command=self.open_current_folder,
            bg="#f39c12",
            fg="white",
            font=("Arial", 10, "bold"),
            width=6,
        )
        self.open_folder_btn.pack(side=tk.LEFT, padx=5, pady=5)

        grid_frame = tk.Frame(panel2, bg="#bdc3c7")
        grid_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.image_labels = []
        for i in range(3):
            for j in range(3):
                cell = tk.Frame(grid_frame, bg="white", bd=2, relief=tk.RIDGE)
                cell.grid(row=i, column=j, padx=4, pady=4, sticky="nsew")
                lbl = tk.Label(cell, bg="white", text="")
                lbl.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)
                self.image_labels.append(lbl)
                grid_frame.grid_rowconfigure(i, weight=1)
                grid_frame.grid_columnconfigure(j, weight=1)

        # Panel 3: Text (out_tags)
        panel3 = tk.LabelFrame(
            main,
            text="📝 Text Files (out_tags)",
            font=("Arial", 12, "bold"),
        )
        panel3.grid(row=0, column=2, sticky="nsew", padx=5, pady=5)

        list_frame = tk.Frame(panel3)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.txt_listbox = tk.Listbox(list_frame, font=("Arial", 10))
        scroll_txt_list = ttk.Scrollbar(list_frame, orient="vertical",
                                        command=self.txt_listbox.yview)
        self.txt_listbox.configure(yscrollcommand=scroll_txt_list.set)
        self.txt_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_txt_list.pack(side=tk.RIGHT, fill=tk.Y)

        self.txt_listbox.bind("<<ListboxSelect>>", self.show_txt_content)

        text_frame = tk.Frame(panel3)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.txt_content = tk.Text(text_frame, wrap=tk.WORD, font=("Arial", 10))
        scroll_txt = ttk.Scrollbar(text_frame, orient="vertical",
                                   command=self.txt_content.yview)
        self.txt_content.configure(yscrollcommand=scroll_txt.set)
        self.txt_content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_txt.pack(side=tk.RIGHT, fill=tk.Y)

        # Grid weights
        main.grid_columnconfigure(0, weight=1, minsize=280)
        main.grid_columnconfigure(1, weight=3, minsize=700)
        main.grid_columnconfigure(2, weight=2, minsize=350)
        main.grid_rowconfigure(0, weight=1)

    # ================== Mouse Wheel ==================

    def on_mouse_wheel(self, event):
        """Cuộn thumbnail bằng chuột"""
        # Kiểm tra xem chuột có ở trên canvas không
        x = self.root.winfo_pointerx() - self.root.winfo_rootx()
        y = self.root.winfo_pointery() - self.root.winfo_rooty()

        # Chỉ scroll khi chuột ở trên panel thumbnail
        if self.thumb_canvas.winfo_x() <= x <= self.thumb_canvas.winfo_x() + self.thumb_canvas.winfo_width():
            if self.thumb_canvas.winfo_y() <= y <= self.thumb_canvas.winfo_y() + self.thumb_canvas.winfo_height():
                direction = -1 if event.delta > 0 else 1
                self.thumb_canvas.yview_scroll(direction * 2, "units")

    # ================== Open Folder ==================

    def open_current_folder(self):
        """Mở folder con hiện tại trong File Explorer"""
        if not self.subfolders:
            messagebox.showwarning("Cảnh báo", "Chưa có folder nào được chọn!")
            return

        folder = self.subfolders[self.current_folder_index]
        folder_path = str(folder)

        try:
            if platform.system() == "Windows":
                os.startfile(folder_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.Popen(["open", folder_path])
            else:  # Linux
                subprocess.Popen(["xdg-open", folder_path])
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể mở folder: {e}")

    # ================== Folder / Thumbnail ==================

    def select_main_folder(self):
        folder = filedialog.askdirectory(title="Chọn thư mục chính")
        if not folder:
            return
        self.load_main_folder(folder)
        self.save_config()

    def load_main_folder(self, folder_path: str):
        self.main_folder = folder_path
        self.path_label.config(text=f"📂 {folder_path}")

        p = Path(folder_path)
        self.subfolders = sorted([f for f in p.iterdir() if f.is_dir()],
                                 key=lambda x: x.name)

        if not self.subfolders:
            messagebox.showwarning("Cảnh báo", "Không tìm thấy thư mục con cấp 1!")
            return

        self.current_folder_index = 0
        self.thumbnail_images.clear()
        self.main_images.clear()

        self.build_thumbnails()
        self.load_current_folder()

    def build_thumbnails(self):
        # Clear old
        for w in self.thumb_container.winfo_children():
            w.destroy()

        for idx, folder in enumerate(self.subfolders):
            frame = tk.Frame(self.thumb_container, bd=2, relief=tk.RAISED, bg="white", cursor="hand2")
            frame.pack(fill=tk.X, padx=5, pady=5)

            name_lbl = tk.Label(
                frame,
                text=folder.name,
                font=("Arial", 10, "bold"),
                bg="white",
                wraplength=220,
            )
            name_lbl.pack(pady=3)

            # Load 4 ảnh đầu tiên
            imgs = self.get_images_from_folder(folder, max_count=4)
            if imgs:
                thumb_img = self.create_thumbnail_grid(imgs)
                self.thumbnail_images[folder] = thumb_img
                img_lbl = tk.Label(frame, image=thumb_img, bg="white")
                img_lbl.pack(pady=3)
            else:
                img_lbl = tk.Label(frame, text="❌ Không có ảnh", bg="#ecf0f1",
                                   font=("Arial", 9))
                img_lbl.pack(pady=8, padx=5, fill=tk.X)

            # Click: đổi folder
            for widget in (frame, name_lbl, img_lbl):
                widget.bind("<Button-1>", lambda e, i=idx: self.goto_folder(i))

        self.highlight_current_thumbnail(scroll_to_current=True)

    def highlight_current_thumbnail(self, scroll_to_current: bool = False):
        children = self.thumb_container.winfo_children()
        for idx, w in enumerate(children):
            if idx == self.current_folder_index:
                w.config(bg="#d5f4e6", relief=tk.SUNKEN, bd=3)
                for c in w.winfo_children():
                    if isinstance(c, tk.Label):
                        c.config(bg="#d5f4e6")
            else:
                w.config(bg="white", relief=tk.RAISED, bd=2)
                for c in w.winfo_children():
                    if isinstance(c, tk.Label):
                        c.config(bg="white")

        if scroll_to_current and children:
            self.root.update_idletasks()
            target = children[self.current_folder_index]

            y_pos = target.winfo_y()
            target_height = target.winfo_height()
            canvas_top = self.thumb_canvas.canvasy(0)
            canvas_bottom = self.thumb_canvas.canvasy(self.thumb_canvas.winfo_height())

            # Nếu thumbnail nằm trên vùng nhìn thấy -> kéo lên
            if y_pos < canvas_top:
                self.thumb_canvas.yview_moveto(y_pos / max(self.thumb_container.winfo_height(), 1))

            # Nếu thumbnail nằm dưới vùng nhìn thấy -> kéo xuống
            elif y_pos + target_height > canvas_bottom:
                offset = (y_pos + target_height - self.thumb_canvas.winfo_height()) / \
                         max(self.thumb_container.winfo_height(), 1)
                self.thumb_canvas.yview_moveto(max(offset, 0.0))

    def create_thumbnail_grid(self, image_paths):
        """Tạo thumbnail 4 ảnh 2x2, mỗi ảnh ~120x120, tổng 240x240."""
        thumb_size = 120
        grid_img = Image.new("RGB", (thumb_size * 2, thumb_size * 2), "white")
        positions = [
            (0, 0),
            (thumb_size, 0),
            (0, thumb_size),
            (thumb_size, thumb_size),
        ]

        for i, path in enumerate(image_paths[:4]):
            try:
                img = Image.open(path)
                img.thumbnail((thumb_size, thumb_size), Image.Resampling.LANCZOS)
                x_off = (thumb_size - img.width) // 2
                y_off = (thumb_size - img.height) // 2
                grid_img.paste(img, (positions[i][0] + x_off, positions[i][1] + y_off))
            except Exception as e:
                print("Lỗi load ảnh thumbnail:", path, e)

        return ImageTk.PhotoImage(grid_img)

    def get_images_from_folder(self, folder: Path, max_count: int = 9):
        exts = (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp")
        result = []
        try:
            for f in sorted(folder.iterdir(), key=lambda x: x.name):
                if f.is_file() and f.suffix.lower() in exts:
                    result.append(f)
                    if len(result) >= max_count:
                        break
        except Exception as e:
            print("Lỗi đọc folder:", folder, e)
        return result

    # ================== Load folder hiện tại ==================

    def load_current_folder(self):
        if not self.subfolders:
            return
        folder = self.subfolders[self.current_folder_index]
        self.folder_label.config(
            text=f"📁 {folder.name} ({self.current_folder_index + 1}/{len(self.subfolders)})"
        )

        # 9 ảnh chính
        self.main_images.clear()
        images = self.get_images_from_folder(folder, max_count=9)

        for idx, lbl in enumerate(self.image_labels):
            if idx < len(images):
                try:
                    img = Image.open(images[idx])
                    img.thumbnail((320, 260), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    self.main_images.append(photo)
                    lbl.config(image=photo, text="")
                    lbl.image = photo
                except Exception as e:
                    lbl.config(image="", text=f"Lỗi\n{images[idx].name}")
                    lbl.image = None
                    print("Lỗi load ảnh chính:", images[idx], e)
            else:
                lbl.config(image="", text="")
                lbl.image = None

        # TXT out_tags
        self.load_text_files(folder)

        # Highlight thumbnail + auto scroll
        self.highlight_current_thumbnail(scroll_to_current=True)

    # ================== TXT ==================

    def load_text_files(self, folder: Path):
        self.txt_listbox.delete(0, tk.END)
        self.txt_content.delete("1.0", tk.END)
        self.txt_files = []

        out_tags = folder / "out_tags"
        if out_tags.exists() and out_tags.is_dir():
            files = sorted(out_tags.iterdir(), key=lambda x: x.name)
            for f in files:
                if f.is_file() and f.suffix.lower() == ".txt":
                    self.txt_files.append(f)
                    self.txt_listbox.insert(tk.END, f"📄 {f.name}")
            if not self.txt_files:
                self.txt_listbox.insert(tk.END, "⚠️ Không có file TXT trong out_tags")
        else:
            self.txt_listbox.insert(tk.END, "⚠️ Folder out_tags không tồn tại")

    def show_txt_content(self, event=None):
        sel = self.txt_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx >= len(self.txt_files):
            return
        try:
            with open(self.txt_files[idx], "r", encoding="utf-8") as f:
                content = f.read()
            self.txt_content.delete("1.0", tk.END)
            self.txt_content.insert("1.0", content)
        except Exception as e:
            self.txt_content.delete("1.0", tk.END)
            self.txt_content.insert("1.0", f"Lỗi đọc file: {e}")

    # ================== Navigation ==================

    def prev_folder(self):
        if not self.subfolders:
            messagebox.showinfo("Thông báo", "Vui lòng chọn thư mục chính trước!")
            return
        self.current_folder_index = (self.current_folder_index - 1) % len(self.subfolders)
        self.load_current_folder()
        self.save_config()

    def next_folder(self):
        if not self.subfolders:
            messagebox.showinfo("Thông báo", "Vui lòng chọn thư mục chính trước!")
            return
        self.current_folder_index = (self.current_folder_index + 1) % len(self.subfolders)
        self.load_current_folder()
        self.save_config()

    def goto_folder(self, index: int):
        if not self.subfolders:
            return
        self.current_folder_index = max(0, min(index, len(self.subfolders) - 1))
        self.load_current_folder()
        self.save_config()

    # ================== Config ==================

    def save_config(self):
        """Lưu folder chính và index hiện tại"""
        data = {
            "main_folder": self.main_folder,
            "current_index": self.current_folder_index,
        }
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print("Lỗi lưu config:", e)

    def load_config(self):
        """Load folder chính từ lần trước"""
        if not os.path.exists(CONFIG_FILE):
            return
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.main_folder = data.get("main_folder", "")
            self.current_folder_index = data.get("current_index", 0)
        except Exception as e:
            print("Lỗi load config:", e)


if __name__ == "__main__":
    root = tk.Tk()
    app = ImageViewer(root)
    root.mainloop()
