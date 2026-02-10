import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import os

class ImageGalleryViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Gallery Viewer")
        self.root.geometry("900x700")
        
        # Variables
        self.base_folder = ""
        self.folders = []
        self.current_folder_index = 0
        self.images = []
        self.current_page = 0
        self.images_per_page = 9
        
        # UI Setup
        self.setup_ui()
        
        # Bind keyboard events
        self.root.bind('<Left>', lambda e: self.prev_folder())
        self.root.bind('<Right>', lambda e: self.next_folder())
        self.root.bind('<Up>', lambda e: self.prev_page())
        self.root.bind('<Down>', lambda e: self.next_page())
        
    def setup_ui(self):
        # Top frame for folder selection and info
        top_frame = tk.Frame(self.root)
        top_frame.pack(pady=10)
        
        tk.Button(top_frame, text="Chọn Folder Gốc", command=self.select_base_folder, 
                 font=("Arial", 12), bg="#4CAF50", fg="white", padx=20).pack(side=tk.LEFT, padx=5)
        
        self.folder_label = tk.Label(top_frame, text="Chưa chọn folder", 
                                     font=("Arial", 11), fg="blue")
        self.folder_label.pack(side=tk.LEFT, padx=10)
        
        # Keyboard hint
        hint_label = tk.Label(top_frame, text="(← → để đổi folder | ↑ ↓ để đổi trang)", 
                             font=("Arial", 9), fg="gray")
        hint_label.pack(side=tk.LEFT, padx=10)
        
        # Navigation frame for folders
        nav_frame = tk.Frame(self.root)
        nav_frame.pack(pady=10)
        
        tk.Button(nav_frame, text="< Folder Trước (←)", command=self.prev_folder,
                 font=("Arial", 12), padx=20, pady=5).pack(side=tk.LEFT, padx=10)
        
        self.folder_info_label = tk.Label(nav_frame, text="", font=("Arial", 11, "bold"))
        self.folder_info_label.pack(side=tk.LEFT, padx=20)
        
        tk.Button(nav_frame, text="Folder Sau (→) >", command=self.next_folder,
                 font=("Arial", 12), padx=20, pady=5).pack(side=tk.LEFT, padx=10)
        
        # Image grid frame (3x3)
        self.grid_frame = tk.Frame(self.root)
        self.grid_frame.pack(pady=20)
        
        # Create 3x3 grid of labels for images
        self.image_labels = []
        for i in range(3):
            row = []
            for j in range(3):
                label = tk.Label(self.grid_frame, bg="gray", width=250, height=200)
                label.grid(row=i, column=j, padx=5, pady=5)
                row.append(label)
            self.image_labels.append(row)
        
        # Page navigation
        page_frame = tk.Frame(self.root)
        page_frame.pack(pady=10)
        
        tk.Button(page_frame, text="< 9 Ảnh Trước (↑)", command=self.prev_page,
                 font=("Arial", 11), padx=15).pack(side=tk.LEFT, padx=10)
        
        self.page_info_label = tk.Label(page_frame, text="", font=("Arial", 10))
        self.page_info_label.pack(side=tk.LEFT, padx=20)
        
        tk.Button(page_frame, text="9 Ảnh Sau (↓) >", command=self.next_page,
                 font=("Arial", 11), padx=15).pack(side=tk.LEFT, padx=10)
    
    def select_base_folder(self):
        folder = filedialog.askdirectory(title="Chọn folder chứa các folder con")
        if folder:
            self.base_folder = folder
            self.load_folders()
            
    def load_folders(self):
        self.folders = []
        try:
            for item in os.listdir(self.base_folder):
                item_path = os.path.join(self.base_folder, item)
                if os.path.isdir(item_path):
                    self.folders.append(item_path)
            
            self.folders.sort()
            
            if self.folders:
                self.current_folder_index = 0
                self.load_current_folder()
            else:
                messagebox.showwarning("Cảnh báo", "Không tìm thấy folder con nào!")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể đọc folder: {e}")
    
    def load_current_folder(self):
        if not self.folders:
            return
        
        current_folder = self.folders[self.current_folder_index]
        folder_name = os.path.basename(current_folder)
        
        self.folder_label.config(text=f"Folder: {folder_name}")
        self.folder_info_label.config(text=f"Folder {self.current_folder_index + 1}/{len(self.folders)}")
        
        # Load images from current folder
        self.images = []
        supported_formats = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')
        
        try:
            for file in os.listdir(current_folder):
                if file.lower().endswith(supported_formats):
                    self.images.append(os.path.join(current_folder, file))
            
            self.images.sort()
            self.current_page = 0
            self.display_images()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể đọc ảnh: {e}")
    
    def display_images(self):
        # Clear all image labels
        for i in range(3):
            for j in range(3):
                self.image_labels[i][j].config(image="", text="", bg="gray")
        
        start_idx = self.current_page * self.images_per_page
        end_idx = min(start_idx + self.images_per_page, len(self.images))
        
        idx = 0
        for i in range(3):
            for j in range(3):
                if start_idx + idx < end_idx:
                    img_path = self.images[start_idx + idx]
                    try:
                        # Load and resize image
                        img = Image.open(img_path)
                        img.thumbnail((240, 190), Image.Resampling.LANCZOS)
                        
                        photo = ImageTk.PhotoImage(img)
                        self.image_labels[i][j].config(image=photo, bg="black")
                        self.image_labels[i][j].image = photo  # Keep reference
                        
                    except Exception as e:
                        self.image_labels[i][j].config(text=f"Error\n{os.path.basename(img_path)}", 
                                                       bg="red", fg="white")
                else:
                    self.image_labels[i][j].config(image="", text="", bg="gray")
                idx += 1
        
        # Update page info
        total_pages = (len(self.images) + self.images_per_page - 1) // self.images_per_page
        if total_pages == 0:
            total_pages = 1
        self.page_info_label.config(text=f"Trang {self.current_page + 1}/{total_pages} | Tổng: {len(self.images)} ảnh")
    
    def prev_folder(self):
        if not self.folders:
            return
        self.current_folder_index = (self.current_folder_index - 1) % len(self.folders)
        self.load_current_folder()
    
    def next_folder(self):
        if not self.folders:
            return
        self.current_folder_index = (self.current_folder_index + 1) % len(self.folders)
        self.load_current_folder()
    
    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.display_images()
    
    def next_page(self):
        max_page = (len(self.images) - 1) // self.images_per_page
        if self.current_page < max_page:
            self.current_page += 1
            self.display_images()

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageGalleryViewer(root)
    root.mainloop()
