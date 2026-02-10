import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from PIL import Image, ImageTk
import os
import shutil
from pathlib import Path
from functools import lru_cache

class ImageOrganizer:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Organizer Pro - Optimized")
        self.root.geometry("1400x900")

        # Cache thumbnails
        self.thumbnail_cache = {}
        self.dataset_thumbnail_cache = {}

        # State
        self.folder1_path = None
        self.folder2_path = None
        self.current_images = []
        self.current_index = 0
        self.dataset_folders = []

        # Setup UI
        self.setup_ui()

    def setup_ui(self):
        # Top frame - Folder selection
        top_frame = tk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Button(top_frame, text="Load Folder 1", command=self.load_folder1, 
                 bg="#4CAF50", fg="white", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        self.label_folder1 = tk.Label(top_frame, text="No folder selected", fg="gray")
        self.label_folder1.pack(side=tk.LEFT, padx=10)

        tk.Button(top_frame, text="Load Folder 2", command=self.load_folder2,
                 bg="#2196F3", fg="white", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        self.label_folder2 = tk.Label(top_frame, text="No folder selected", fg="gray")
        self.label_folder2.pack(side=tk.LEFT, padx=10)

        # Main container
        main_container = tk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Left panel - Current image viewer
        left_panel = tk.Frame(main_container, relief=tk.SUNKEN, bd=2)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # Image display
        self.image_label = tk.Label(left_panel, bg="#f0f0f0")
        self.image_label.pack(fill=tk.BOTH, expand=True, pady=5)

        # Navigation
        nav_frame = tk.Frame(left_panel)
        nav_frame.pack(fill=tk.X, pady=5)

        tk.Button(nav_frame, text="← Previous", command=self.prev_image,
                 font=("Arial", 11, "bold")).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        self.image_counter = tk.Label(nav_frame, text="0/0", font=("Arial", 10))
        self.image_counter.pack(side=tk.LEFT, padx=10)
        tk.Button(nav_frame, text="Next →", command=self.next_image,
                 font=("Arial", 11, "bold")).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        # Right panel - Dataset folders
        right_panel = tk.Frame(main_container, relief=tk.SUNKEN, bd=2, width=300)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        right_panel.pack_propagate(False)

        tk.Label(right_panel, text="Dataset Folders", font=("Arial", 12, "bold"), 
                bg="#e3f2fd").pack(fill=tk.X, pady=5)

        # Add new folder button
        tk.Button(right_panel, text="+ Create New Dataset", command=self.create_new_dataset,
                 bg="#FF9800", fg="white", font=("Arial", 9, "bold")).pack(fill=tk.X, padx=5, pady=5)

        # Scrollable dataset list
        canvas_frame = tk.Frame(right_panel)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.dataset_canvas = tk.Canvas(canvas_frame, bg="white", highlightthickness=0)
        scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=self.dataset_canvas.yview)
        self.dataset_frame = tk.Frame(self.dataset_canvas, bg="white")

        self.dataset_canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.dataset_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas_window = self.dataset_canvas.create_window((0, 0), window=self.dataset_frame, 
                                                                anchor="nw", width=270)
        self.dataset_frame.bind("<Configure>", lambda e: self.dataset_canvas.configure(
            scrollregion=self.dataset_canvas.bbox("all")))

        # Keyboard shortcuts
        self.root.bind("<Left>", lambda e: self.prev_image())
        self.root.bind("<Right>", lambda e: self.next_image())

    def get_thumbnail(self, image_path, size=(250, 250), cache_dict=None):
        """Get thumbnail with caching"""
        if cache_dict is None:
            cache_dict = self.thumbnail_cache

        cache_key = f"{image_path}_{size[0]}x{size[1]}"

        if cache_key not in cache_dict:
            try:
                img = Image.open(image_path)
                img.thumbnail(size, Image.Resampling.LANCZOS)
                cache_dict[cache_key] = ImageTk.PhotoImage(img)
            except:
                cache_dict[cache_key] = None

        return cache_dict.get(cache_key)

    def load_folder1(self):
        path = filedialog.askdirectory(title="Select Folder 1")
        if path:
            self.folder1_path = Path(path)
            self.label_folder1.config(text=f"Folder 1: {self.folder1_path.name}")
            self.scan_images()

    def load_folder2(self):
        path = filedialog.askdirectory(title="Select Folder 2")
        if path:
            self.folder2_path = Path(path)
            self.label_folder2.config(text=f"Folder 2: {self.folder2_path.name}")
            self.scan_dataset_folders_optimized()

    def scan_images(self):
        """Scan images from folder 1"""
        if not self.folder1_path:
            return

        self.current_images = []
        for ext in ["*.jpg", "*.jpeg", "*.png", "*.webp", "*.gif"]:
            self.current_images.extend(list(self.folder1_path.glob(ext)))
            self.current_images.extend(list(self.folder1_path.glob(ext.upper())))

        self.current_images.sort()
        self.current_index = 0

        # Clear old cache for folder 1
        self.thumbnail_cache.clear()

        self.show_current_image()

    def scan_dataset_folders_optimized(self):
        """Optimized scan with lazy loading"""
        if not self.folder2_path:
            return

        # Clear old widgets efficiently
        for widget in self.dataset_frame.winfo_children():
            widget.destroy()

        self.dataset_folders.clear()
        self.dataset_thumbnail_cache.clear()

        # Scan folders
        for item in self.folder2_path.iterdir():
            if item.is_dir():
                dataset_path = item / "dataset"
                if dataset_path.exists():
                    # Find representative image
                    rep_image = None
                    for ext in ["*.jpg", "*.jpeg", "*.png", "*.webp"]:
                        images = list(item.glob(ext))
                        if images:
                            rep_image = images[0]
                            break

                    self.dataset_folders.append({
                        "name": item.name,
                        "path": item,
                        "dataset_path": dataset_path,
                        "thumbnail": rep_image
                    })

        # Render folders with lazy loading
        self.render_dataset_folders_lazy()

    def render_dataset_folders_lazy(self):
        """Render dataset folders one by one to avoid lag"""
        def render_next(index=0):
            if index >= len(self.dataset_folders):
                return

            folder = self.dataset_folders[index]
            self.create_dataset_item(folder, index)

            # Schedule next item
            if index + 1 < len(self.dataset_folders):
                self.root.after(10, lambda: render_next(index + 1))

        render_next(0)

    def create_dataset_item(self, folder, index):
        """Create a single dataset item"""
        item_frame = tk.Frame(self.dataset_frame, relief=tk.RAISED, bd=1, bg="white")
        item_frame.pack(fill=tk.X, pady=3)

        # Thumbnail
        if folder["thumbnail"]:
            thumb = self.get_thumbnail(folder["thumbnail"], size=(60, 60), 
                                      cache_dict=self.dataset_thumbnail_cache)
            if thumb:
                thumb_label = tk.Label(item_frame, image=thumb, bg="white")
                thumb_label.image = thumb  # Keep reference
                thumb_label.pack(side=tk.LEFT, padx=5, pady=5)

        # Info
        info_frame = tk.Frame(item_frame, bg="white")
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        tk.Label(info_frame, text=folder["name"], font=("Arial", 9, "bold"), 
                bg="white", anchor="w").pack(fill=tk.X)

        # Move button
        btn = tk.Button(info_frame, text="Move Here →", 
                       command=lambda f=folder: self.move_image_to_dataset(f),
                       bg="#4CAF50", fg="white", font=("Arial", 8))
        btn.pack(fill=tk.X, pady=2)

    def show_current_image(self):
        """Show current image without lag"""
        if not self.current_images or self.current_index >= len(self.current_images):
            self.image_label.config(image="", text="No images")
            self.image_counter.config(text="0/0")
            return

        image_path = self.current_images[self.current_index]

        # Load thumbnail from cache
        photo = self.get_thumbnail(image_path, size=(700, 700))

        if photo:
            self.image_label.config(image=photo, text="")
            self.image_label.image = photo  # Keep reference
        else:
            self.image_label.config(image="", text="Error loading image")

        self.image_counter.config(text=f"{self.current_index + 1}/{len(self.current_images)}")

    def prev_image(self):
        if self.current_images and self.current_index > 0:
            self.current_index -= 1
            self.show_current_image()

    def next_image(self):
        if self.current_images and self.current_index < len(self.current_images) - 1:
            self.current_index += 1
            self.show_current_image()

    def move_image_to_dataset(self, folder):
        """Move current image to dataset folder"""
        if not self.current_images or self.current_index >= len(self.current_images):
            messagebox.showwarning("Warning", "No image selected")
            return

        src_image = self.current_images[self.current_index]
        dest_path = folder["dataset_path"] / src_image.name

        try:
            # Move file
            shutil.move(str(src_image), str(dest_path))

            # Remove from list
            self.current_images.pop(self.current_index)

            # Adjust index
            if self.current_index >= len(self.current_images):
                self.current_index = max(0, len(self.current_images) - 1)

            # Refresh only affected parts
            self.show_current_image()
            self.refresh_single_dataset_folder(folder)

        except Exception as e:
            messagebox.showerror("Error", f"Cannot move image: {e}")

    def refresh_single_dataset_folder(self, folder):
        """Refresh only one dataset folder item (không lag)"""
        # Update thumbnail nếu folder chưa có ảnh đại diện
        if folder["thumbnail"] is None:
            for ext in ["*.jpg", "*.jpeg", "*.png", "*.webp"]:
                images = list(folder["path"].glob(ext))
                if images:
                    folder["thumbnail"] = images[0]
                    # Clear cache để load thumbnail mới
                    cache_key = f"{folder['thumbnail']}_60x60"
                    if cache_key in self.dataset_thumbnail_cache:
                        del self.dataset_thumbnail_cache[cache_key]
                    break

        # Tìm và update widget tương ứng (không rebuild toàn bộ)
        for i, child in enumerate(self.dataset_frame.winfo_children()):
            if i < len(self.dataset_folders) and self.dataset_folders[i] == folder:
                # Update thumbnail nếu cần
                if folder["thumbnail"]:
                    thumb = self.get_thumbnail(folder["thumbnail"], size=(60, 60),
                                              cache_dict=self.dataset_thumbnail_cache)
                    if thumb:
                        # Tìm label thumbnail trong frame
                        for widget in child.winfo_children():
                            if isinstance(widget, tk.Label) and hasattr(widget, 'image'):
                                widget.config(image=thumb)
                                widget.image = thumb
                                break
                break

    def create_new_dataset(self):
        """Create new dataset folder in Folder 2"""
        if not self.folder2_path:
            messagebox.showwarning("Warning", "Please load Folder 2 first")
            return

        folder_name = simpledialog.askstring("New Dataset", "Enter dataset folder name:")
        if not folder_name:
            return

        new_folder = self.folder2_path / folder_name
        dataset_folder = new_folder / "dataset"

        try:
            dataset_folder.mkdir(parents=True, exist_ok=True)
            messagebox.showinfo("Success", f"Created dataset: {folder_name}")

            # Chỉ thêm item mới thay vì scan lại toàn bộ
            new_dataset = {
                "name": folder_name,
                "path": new_folder,
                "dataset_path": dataset_folder,
                "thumbnail": None
            }
            self.dataset_folders.append(new_dataset)
            self.create_dataset_item(new_dataset, len(self.dataset_folders) - 1)

        except Exception as e:
            messagebox.showerror("Error", f"Cannot create folder: {e}")

# Run application
if __name__ == "__main__":
    root = tk.Tk()
    app = ImageOrganizer(root)
    root.mainloop()
