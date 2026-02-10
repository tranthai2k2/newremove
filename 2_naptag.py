import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import json
from pathlib import Path
from datetime import datetime

class TextFileTabViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("Text File Tab Viewer & Tag Manager")
        self.root.geometry("1200x800")
        
        # File config để lưu settings
        self.config_file = "viewer_config.json"
        self.tag_output_file = r"D:\no\wantremove\trangphuc200.txt"
        
        # Tùy chỉnh style cho tabs
        style = ttk.Style()
        style.configure('TNotebook.Tab', 
                       font=('Arial', 12, 'bold'),
                       padding=[20, 10])
        
        # Container chính
        main_container = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashwidth=5)
        main_container.pack(fill=tk.BOTH, expand=1)
        
        # ===== PANEL TRÁI: File viewer =====
        left_panel = tk.Frame(main_container, bg='#f5f5f5')
        main_container.add(left_panel, width=750)
        
        # Frame trên cùng cho chọn folder
        top_frame = tk.Frame(left_panel, pady=10, bg='#f0f0f0')
        top_frame.pack(fill=tk.X, padx=10)
        
        tk.Label(top_frame, text="Địa chỉ folder:", 
                font=("Arial", 11, 'bold'), bg='#f0f0f0').pack(side=tk.LEFT, padx=5)
        
        self.folder_entry = tk.Entry(top_frame, width=45, font=("Arial", 10))
        self.folder_entry.pack(side=tk.LEFT, padx=5)
        
        tk.Button(top_frame, text="📁 Chọn Folder", command=self.select_folder, 
                 bg="#4CAF50", fg="white", font=("Arial", 10, 'bold'), 
                 padx=10, pady=5, cursor='hand2').pack(side=tk.LEFT, padx=5)
        
        tk.Button(top_frame, text="🔄 Load Files", command=self.load_files,
                 bg="#2196F3", fg="white", font=("Arial", 10, 'bold'),
                 padx=10, pady=5, cursor='hand2').pack(side=tk.LEFT, padx=5)
        
        # Tạo Notebook để chứa các tabs
        self.notebook = ttk.Notebook(left_panel)
        self.notebook.pack(expand=1, fill='both', padx=15, pady=15)
        
        self.tabs = {}
        
        # ===== PANEL PHẢI: Tag Manager =====
        right_panel = tk.Frame(main_container, bg='white')
        main_container.add(right_panel, width=430)
        
        # Header
        header_frame = tk.Frame(right_panel, bg='#1976D2', pady=15)
        header_frame.pack(fill=tk.X)
        
        tk.Label(header_frame, text="🏷️ TAG MANAGER", 
                font=("Arial", 16, 'bold'), bg='#1976D2', fg='white').pack()
        
        tk.Label(header_frame, text=f"Output: {self.tag_output_file}", 
                font=("Arial", 9), bg='#1976D2', fg='#E3F2FD').pack()
        
        # Tag input area
        input_frame = tk.Frame(right_panel, bg='white', pady=10)
        input_frame.pack(fill=tk.BOTH, expand=1, padx=15)
        
        tk.Label(input_frame, text="Nhập tags (có thể nhiều dòng):", 
                font=("Arial", 11, 'bold'), bg='white', fg='#333').pack(anchor=tk.W, pady=(5, 5))
        
        # Text widget với scrollbar cho nhập tags
        self.tag_input = scrolledtext.ScrolledText(input_frame, 
                                                   wrap=tk.WORD,
                                                   font=("Consolas", 10),
                                                   height=15,
                                                   padx=10, pady=10,
                                                   bg='#f9f9f9',
                                                   fg='#333',
                                                   relief=tk.SOLID,
                                                   borderwidth=1)
        self.tag_input.pack(fill=tk.BOTH, expand=1, pady=5)
        
        # Button frame
        button_frame = tk.Frame(input_frame, bg='white', pady=10)
        button_frame.pack(fill=tk.X)
        
        tk.Button(button_frame, text="💾 SAVE TAGS", command=self.save_tags,
                 bg="#4CAF50", fg="white", font=("Arial", 12, 'bold'),
                 padx=20, pady=10, cursor='hand2', width=15).pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="🗑️ Clear", command=self.clear_tags,
                 bg="#FF5722", fg="white", font=("Arial", 12, 'bold'),
                 padx=20, pady=10, cursor='hand2', width=15).pack(side=tk.LEFT, padx=5)
        
        # Preview area
        preview_frame = tk.Frame(right_panel, bg='white', pady=5)
        preview_frame.pack(fill=tk.X, padx=15)
        
        tk.Label(preview_frame, text="📝 Preview nội dung file:", 
                font=("Arial", 10, 'bold'), bg='white', fg='#555').pack(anchor=tk.W, pady=(5, 5))
        
        self.preview_text = tk.Text(preview_frame, 
                                   wrap=tk.WORD,
                                   font=("Consolas", 9),
                                   height=8,
                                   padx=8, pady=8,
                                   bg='#fafafa',
                                   fg='#666',
                                   relief=tk.SOLID,
                                   borderwidth=1,
                                   state=tk.DISABLED)
        self.preview_text.pack(fill=tk.X, pady=5)
        
        tk.Button(preview_frame, text="🔄 Refresh Preview", command=self.refresh_preview,
                 bg="#607D8B", fg="white", font=("Arial", 9),
                 padx=10, pady=5, cursor='hand2').pack(pady=5)
        
        # Load config và preview
        self.load_config()
        self.refresh_preview()
        
    def load_config(self):
        """Load địa chỉ folder từ file JSON"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    folder_path = config.get('last_folder_path', '')
                    if folder_path:
                        self.folder_entry.delete(0, tk.END)
                        self.folder_entry.insert(0, folder_path)
                        # Auto load files nếu folder tồn tại
                        if os.path.exists(folder_path):
                            self.load_files(auto=True)
        except Exception as e:
            print(f"Không thể load config: {e}")
    
    def save_config(self):
        """Lưu địa chỉ folder vào file JSON"""
        try:
            config = {
                'last_folder_path': self.folder_entry.get().strip(),
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Không thể lưu config: {e}")
    
    def select_folder(self):
        """Mở dialog chọn folder"""
        folder_path = filedialog.askdirectory(title="Chọn folder chứa thư mục out_tags")
        if folder_path:
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, folder_path)
            self.save_config()
    
    def load_files(self, auto=False):
        """Load các file txt từ thư mục out_tags"""
        folder_path = self.folder_entry.get().strip()
        
        if not folder_path:
            if not auto:
                messagebox.showwarning("⚠️ Cảnh báo", "Vui lòng nhập hoặc chọn địa chỉ folder!")
            return
        
        if not os.path.exists(folder_path):
            if not auto:
                messagebox.showerror("❌ Lỗi", "Đường dẫn folder không tồn tại!")
            return
        
        # Lưu config
        self.save_config()
        
        # Tìm thư mục out_tags
        out_tags_path = os.path.join(folder_path, "out_tags")
        
        if not os.path.exists(out_tags_path):
            if not auto:
                messagebox.showerror("❌ Lỗi", "Không tìm thấy thư mục 'out_tags' trong folder này!")
            return
        
        # Xóa tất cả tabs hiện tại
        for tab_id in self.notebook.tabs():
            self.notebook.forget(tab_id)
        self.tabs.clear()
        
        # Tìm tất cả file .txt
        txt_files = [f for f in os.listdir(out_tags_path) if f.endswith('.txt')]
        
        if not txt_files:
            if not auto:
                messagebox.showinfo("ℹ️ Thông báo", "Không tìm thấy file .txt nào trong thư mục out_tags!")
            return
        
        txt_files.sort()
        
        for txt_file in txt_files:
            file_path = os.path.join(out_tags_path, txt_file)
            self.create_tab(txt_file, file_path)
        
        if not auto:
            messagebox.showinfo("✅ Thành công", f"Đã load {len(txt_files)} file txt!")
    
    def create_tab(self, tab_name, file_path):
        """Tạo một tab mới với nội dung file"""
        tab_frame = ttk.Frame(self.notebook)
        
        # Info frame
        info_frame = tk.Frame(tab_frame, bg='#e8f4f8', pady=5)
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(info_frame, text=f"📄 {tab_name}", 
                font=("Arial", 10, 'bold'), bg='#e8f4f8', 
                fg='#1976D2').pack(side=tk.LEFT, padx=10)
        
        # Text area
        text_frame = tk.Frame(tab_frame)
        text_frame.pack(expand=1, fill='both', padx=5, pady=5)
        
        scrollbar_y = tk.Scrollbar(text_frame, width=18)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        text_widget = tk.Text(text_frame, 
                             wrap=tk.WORD,
                             yscrollcommand=scrollbar_y.set,
                             font=("Consolas", 11),
                             padx=10, pady=10,
                             bg='#ffffff',
                             fg='#333333',
                             relief=tk.FLAT,
                             borderwidth=2)
        text_widget.pack(expand=1, fill='both')
        
        scrollbar_y.config(command=text_widget.yview)
        
        # Đọc file
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                text_widget.insert('1.0', content)
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='windows-1252') as f:
                    content = f.read()
                    text_widget.insert('1.0', content)
            except Exception as e:
                text_widget.insert('1.0', f"⚠️ Lỗi đọc file: {str(e)}")
        except Exception as e:
            text_widget.insert('1.0', f"⚠️ Lỗi đọc file: {str(e)}")
        
        text_widget.config(state=tk.DISABLED)
        
        display_name = tab_name.replace('.txt', '')[:22]
        if len(tab_name) > 25:
            display_name += '...'
        
        self.notebook.add(tab_frame, text=f"  {display_name}  ")
        self.tabs[tab_name] = text_widget
    
    def save_tags(self):
        """Lưu tags vào file (append vào cuối dòng hiện tại)"""
        tags_content = self.tag_input.get("1.0", tk.END).strip()
        
        if not tags_content:
            return
        
        try:
            # Tạo thư mục nếu chưa tồn tại
            os.makedirs(os.path.dirname(self.tag_output_file), exist_ok=True)
            
            # Đọc nội dung hiện tại
            existing_content = ""
            if os.path.exists(self.tag_output_file):
                with open(self.tag_output_file, 'r', encoding='utf-8') as f:
                    existing_content = f.read()
            
            # Xóa các newline ở cuối (nếu có)
            existing_content = existing_content.rstrip('\n\r')
            
            # Ghi lại file với nội dung mới được append
            with open(self.tag_output_file, 'w', encoding='utf-8') as f:
                if existing_content:
                    # Nếu có nội dung cũ, thêm ", " trước nội dung mới
                    f.write(existing_content + ", " + tags_content)
                else:
                    # Nếu file trống, chỉ ghi nội dung mới
                    f.write(tags_content)
            
            # Refresh preview (không hiện popup)
            self.refresh_preview()
            
            # Flash button để báo đã save thành công
            self.flash_save_button()
            
        except Exception as e:
            # Chỉ hiện lỗi nếu thật sự có lỗi
            messagebox.showerror("❌ Lỗi", f"Không thể lưu tags:\n{str(e)}")
    
    def flash_save_button(self):
        """Flash button để báo hiệu đã save"""
        # Tìm button save
        for widget in self.root.winfo_children():
            self._flash_recursive(widget)
    
    def _flash_recursive(self, widget):
        """Đệ quy tìm button save và flash"""
        if isinstance(widget, tk.Button):
            if "SAVE" in widget.cget("text"):
                original_bg = widget.cget("bg")
                widget.config(bg="#66BB6A")  # Màu xanh sáng
                widget.update()
                widget.after(200, lambda: widget.config(bg=original_bg))
                return
        
        for child in widget.winfo_children():
            self._flash_recursive(child)
    
    def clear_tags(self):
        """Xóa nội dung trong tag input"""
        self.tag_input.delete("1.0", tk.END)
    
    def refresh_preview(self):
        """Refresh preview nội dung file"""
        try:
            self.preview_text.config(state=tk.NORMAL)
            self.preview_text.delete("1.0", tk.END)
            
            if os.path.exists(self.tag_output_file):
                with open(self.tag_output_file, 'r', encoding='utf-8') as f:
                    # Chỉ hiển thị 500 ký tự cuối
                    content = f.read()
                    if len(content) > 500:
                        preview = "...\n" + content[-500:]
                    else:
                        preview = content
                    
                    self.preview_text.insert("1.0", preview)
            else:
                self.preview_text.insert("1.0", "(File chưa tồn tại)")
            
            self.preview_text.config(state=tk.DISABLED)
        except Exception as e:
            self.preview_text.config(state=tk.NORMAL)
            self.preview_text.delete("1.0", tk.END)
            self.preview_text.insert("1.0", f"Lỗi: {str(e)}")
            self.preview_text.config(state=tk.DISABLED)

def main():
    root = tk.Tk()
    app = TextFileTabViewer(root)
    root.mainloop()

if __name__ == "__main__":
    main()
