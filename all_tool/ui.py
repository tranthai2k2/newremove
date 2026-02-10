"""
Giao diện UI cho Image & Tag Processing Tool với Tab Viewer
"""
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import json
from pathlib import Path
import threading
import os

# Import các module xử lý
from code1_convert_webp import convert_webp_to_jpg
from code2_process_tags import process_tags
from code3_tag_manager import save_tags_to_file, get_file_preview, load_text_files, remove_tags_from_folder

# ═══════════════════════════ CẤU HÌNH ═══════════════════════════
# Tạo folder config riêng
CONFIG_FOLDER = Path("tool_config")
CONFIG_FOLDER.mkdir(exist_ok=True)
CONFIG_FILE = CONFIG_FOLDER / "app_config.json"

# Output file cố định (tương đối từ vị trí tool)
DEFAULT_OUTPUT_FILE = Path(__file__).parent.parent / "wantremove" / "trangphuc200.txt"

# ═══════════════════════════ GHI NHỚ CẤU HÌNH ═══════════════════════════
def load_config():
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"last_folder": ""}
    return {"last_folder": ""}

def save_config(folder_path=None):
    config = load_config()
    if folder_path is not None:
        config["last_folder"] = folder_path

    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

# ═══════════════════════════ GUI ═══════════════════════════
class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image & Tag Processing Tool")
        self.root.geometry("1200x750")

        # Load cấu hình
        config = load_config()
        self.folder_path = tk.StringVar(value=config.get("last_folder", ""))
        self.search_text = tk.StringVar()

        # Output path cố định
        self.tag_output_file = str(DEFAULT_OUTPUT_FILE.resolve())

        # Container chính với PanedWindow
        main_paned = tk.PanedWindow(root, orient=tk.HORIZONTAL, sashwidth=5)
        main_paned.pack(fill=tk.BOTH, expand=1)

        # ═══════════════ PANEL TRÁI ═══════════════
        left_panel = tk.Frame(main_paned, bg='#f5f5f5')
        main_paned.add(left_panel, width=750)

        # Header
        header_frame = tk.Frame(left_panel, bg="#2c3e50", pady=10)
        header_frame.pack(fill=tk.X)

        title = tk.Label(header_frame, text="🛠️ ALL TOOLS", 
                        font=("Arial", 16, "bold"), bg="#2c3e50", fg="white")
        title.pack()

        # Folder selection
        folder_frame = tk.Frame(left_panel, pady=10, bg='#f5f5f5')
        folder_frame.pack(fill=tk.X, padx=15)

        tk.Label(folder_frame, text="📁 Folder:", 
                font=("Arial", 10, "bold"), bg='#f5f5f5').pack(side=tk.LEFT, padx=5)

        folder_entry = tk.Entry(folder_frame, textvariable=self.folder_path, 
                               font=("Arial", 10), width=40)
        folder_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        browse_btn = tk.Button(folder_frame, text="Browse", 
                              command=self.browse_folder, 
                              font=("Arial", 10), bg="#3498db", fg="white",
                              cursor='hand2', relief=tk.RAISED, bd=2)
        browse_btn.pack(side=tk.LEFT, padx=5)

        load_btn = tk.Button(folder_frame, text="🔄 Load", 
                            command=self.load_files,
                            font=("Arial", 10), bg="#2196F3", fg="white",
                            cursor='hand2', relief=tk.RAISED, bd=2)
        load_btn.pack(side=tk.LEFT, padx=5)

        # 3 NÚT CHÍNH (thêm shadow)
        btn_frame = tk.Frame(left_panel, pady=10, bg='#f5f5f5')
        btn_frame.pack()

        btn1 = tk.Button(btn_frame, text="🖼️ Convert WebP", 
                        command=self.run_convert_webp,
                        font=("Arial", 11, "bold"), 
                        bg="#27ae60", fg="white",
                        width=18, height=2, cursor='hand2',
                        relief=tk.RAISED, bd=3)
        btn1.grid(row=0, column=0, padx=5)

        btn2 = tk.Button(btn_frame, text="🏷️ Process Tags", 
                        command=self.run_process_tags,
                        font=("Arial", 11, "bold"),
                        bg="#e74c3c", fg="white",
                        width=18, height=2, cursor='hand2',
                        relief=tk.RAISED, bd=3)
        btn2.grid(row=0, column=1, padx=5)

        btn3 = tk.Button(btn_frame, text="🗑️ Xóa Đè Tags", 
                        command=self.run_remove_tags,
                        font=("Arial", 11, "bold"),
                        bg="#FF9800", fg="white",
                        width=18, height=2, cursor='hand2',
                        relief=tk.RAISED, bd=3)
        btn3.grid(row=0, column=2, padx=5)

        # Tab Notebook với shadow container
        tab_frame = tk.LabelFrame(left_panel, text="📄 File Viewer (out_tags)", 
                                 font=("Arial", 10, "bold"), bg='#f5f5f5',
                                 relief=tk.GROOVE, bd=2)
        tab_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        # ════════════ TÙY CHỈNH STYLE CHO TABS VỚI SHADOW ════════════
        style = ttk.Style()

        # Tạo theme riêng
        style.theme_create("shadow_theme", parent="alt", settings={
            "TNotebook": {
                "configure": {
                    "background": "#e0e0e0",
                    "borderwidth": 2,
                    "relief": "sunken"
                }
            },
            "TNotebook.Tab": {
                "configure": {
                    "padding": [15, 8],
                    "font": ('Arial', 10, 'bold'),
                    "background": "#c0c0c0",
                    "foreground": "#555555",
                    "borderwidth": 2,
                    "relief": "raised"
                },
                "map": {
                    "background": [
                        ("selected", "#ffffff"),
                        ("active", "#d8d8d8")
                    ],
                    "foreground": [
                        ("selected", "#1976D2"),
                        ("active", "#333333")
                    ],
                    "relief": [
                        ("selected", "solid"),
                        ("!selected", "raised")
                    ],
                    "borderwidth": [
                        ("selected", 3),
                        ("!selected", 1)
                    ],
                    "expand": [
                        ("selected", [2, 2, 2, 0])
                    ]
                }
            }
        })

        style.theme_use("shadow_theme")
        # ════════════════════════════════════════════════════════════════

        # Shadow container cho notebook
        shadow_container = tk.Frame(tab_frame, bg='#999999', relief=tk.SUNKEN, bd=2)
        shadow_container.pack(expand=1, fill='both', padx=5, pady=5)

        self.notebook = ttk.Notebook(shadow_container)
        self.notebook.pack(expand=1, fill='both', padx=2, pady=2)
        self.tabs = {}

        # Lưu thông tin file name cho mỗi tab
        self.tab_filenames = {}

        # ════════════ TOOLBAR DƯỚI TABS: SEARCH & COPY ════════════
        toolbar_frame = tk.Frame(tab_frame, bg='#e8f4f8', pady=8, relief=tk.RAISED, bd=2)
        toolbar_frame.pack(fill=tk.X, padx=5, pady=(0, 5))

        # Search section
        tk.Label(toolbar_frame, text="🔍 Search:", 
                font=("Arial", 9, "bold"), bg='#e8f4f8').pack(side=tk.LEFT, padx=5)

        search_entry = tk.Entry(toolbar_frame, textvariable=self.search_text,
                               font=("Arial", 9), width=25,
                               relief=tk.SUNKEN, bd=2)
        search_entry.pack(side=tk.LEFT, padx=5)
        search_entry.bind('<Return>', lambda e: self.highlight_text())

        find_btn = tk.Button(toolbar_frame, text="Find", 
                            command=self.highlight_text,
                            font=("Arial", 9, "bold"),
                            bg="#2196F3", fg="white",
                            width=8, cursor='hand2',
                            relief=tk.RAISED, bd=2)
        find_btn.pack(side=tk.LEFT, padx=2)

        clear_highlight_btn = tk.Button(toolbar_frame, text="Clear", 
                                        command=self.clear_highlight,
                                        font=("Arial", 9, "bold"),
                                        bg="#607D8B", fg="white",
                                        width=8, cursor='hand2',
                                        relief=tk.RAISED, bd=2)
        clear_highlight_btn.pack(side=tk.LEFT, padx=2)

        # Separator
        separator = tk.Frame(toolbar_frame, bg='#999999', width=2, relief=tk.SUNKEN)
        separator.pack(side=tk.LEFT, fill=tk.Y, padx=10)

        # Copy button với icon rõ ràng hơn
        copy_btn = tk.Button(toolbar_frame, text="📋 Copy All", 
                            command=self.copy_content,
                            font=("Arial", 9, "bold"),
                            bg="#9C27B0", fg="white",
                            width=12, cursor='hand2',
                            relief=tk.RAISED, bd=2)
        copy_btn.pack(side=tk.LEFT, padx=5)

        # Match count label
        self.match_label = tk.Label(toolbar_frame, text="",
                                    font=("Arial", 9, "italic"),
                                    bg='#e8f4f8', fg='#666')
        self.match_label.pack(side=tk.LEFT, padx=10)

        # Current file label (hiển thị file đang xem)
        self.current_file_label = tk.Label(toolbar_frame, text="",
                                          font=("Arial", 8, "italic"),
                                          bg='#e8f4f8', fg='#1976D2')
        self.current_file_label.pack(side=tk.RIGHT, padx=10)

        # ═══════════════ PANEL PHẢI: TAG MANAGER ═══════════════
        right_panel = tk.Frame(main_paned, bg='white')
        main_paned.add(right_panel, width=430)

        # Header với shadow
        tag_header = tk.Frame(right_panel, bg='#1976D2', pady=15, relief=tk.RAISED, bd=3)
        tag_header.pack(fill=tk.X)

        tk.Label(tag_header, text="🏷️ TAG MANAGER",
                font=("Arial", 16, 'bold'), bg='#1976D2', fg='white').pack()

        # Output file path (read-only, cố định)
        output_frame = tk.Frame(right_panel, bg='white', pady=10)
        output_frame.pack(fill=tk.X, padx=15)

        tk.Label(output_frame, text="📄 Output File (cố định):", 
                font=("Arial", 9, "bold"), bg="white", fg="#666").pack(anchor=tk.W, pady=2)

        output_display = tk.Entry(output_frame, 
                                 font=("Arial", 8), bg='#e8f4f8', fg='#1976D2',
                                 state='readonly', relief=tk.SUNKEN, bd=2)
        output_display.insert(0, self.tag_output_file)
        output_display.pack(fill=tk.X, pady=2)

        tk.Label(output_frame, text="💡 ../wantremove/trangphuc200.txt", 
                font=("Arial", 7, "italic"), bg="white", fg="#999").pack(anchor=tk.W)

        # Tag input area với shadow
        input_container = tk.Frame(right_panel, bg='white', pady=10)
        input_container.pack(fill=tk.BOTH, expand=True, padx=15)

        tk.Label(input_container, text="Nhập tags (có thể nhiều dòng):", 
                font=("Arial", 10, "bold"), bg="white", fg='#333').pack(anchor=tk.W, pady=2)

        # Shadow frame cho text input
        input_shadow_frame = tk.Frame(input_container, bg='#999999', relief=tk.SUNKEN, bd=2)
        input_shadow_frame.pack(fill=tk.BOTH, expand=True, pady=2)

        self.tag_input = scrolledtext.ScrolledText(input_shadow_frame,
                                                   wrap=tk.WORD,
                                                   font=("Consolas", 10),
                                                   height=10,
                                                   bg='#f9f9f9',
                                                   fg='#333',
                                                   padx=10, pady=10,
                                                   relief=tk.FLAT,
                                                   borderwidth=0)
        self.tag_input.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Button frame (2 nút với shadow)
        button_frame = tk.Frame(input_container, bg='white', pady=10)
        button_frame.pack(fill=tk.X)

        save_tag_btn = tk.Button(button_frame, text="💾 SAVE TAGS", 
                                command=self.save_tags,
                                font=("Arial", 11, "bold"),
                                bg="#4CAF50", fg="white",
                                width=18, height=1, cursor='hand2',
                                relief=tk.RAISED, bd=3)
        save_tag_btn.pack(side=tk.LEFT, padx=5)

        clear_tag_btn = tk.Button(button_frame, text="🗑️ Clear Input", 
                                 command=self.clear_tag_input,
                                 font=("Arial", 11, "bold"),
                                 bg="#FF5722", fg="white",
                                 width=18, height=1, cursor='hand2',
                                 relief=tk.RAISED, bd=3)
        clear_tag_btn.pack(side=tk.LEFT, padx=5)

        # Preview area với shadow
        preview_frame = tk.Frame(right_panel, bg='white', pady=5)
        preview_frame.pack(fill=tk.X, padx=15)

        tk.Label(preview_frame, text="📝 Preview nội dung file:",
                font=("Arial", 9, 'bold'), bg='white', fg='#555').pack(anchor=tk.W, pady=2)

        # Shadow frame cho preview
        preview_shadow_frame = tk.Frame(preview_frame, bg='#999999', relief=tk.SUNKEN, bd=2)
        preview_shadow_frame.pack(fill=tk.X, pady=2)

        self.preview_text = tk.Text(preview_shadow_frame,
                                   wrap=tk.WORD,
                                   font=("Consolas", 8),
                                   height=6,
                                   padx=8, pady=8,
                                   bg='#fafafa',
                                   fg='#666',
                                   relief=tk.FLAT,
                                   borderwidth=0,
                                   state=tk.DISABLED)
        self.preview_text.pack(fill=tk.X, padx=2, pady=2)

        refresh_preview_btn = tk.Button(preview_frame, text="🔄 Refresh Preview", 
                                       command=self.refresh_preview,
                                       font=("Arial", 8),
                                       bg="#607D8B", fg="white",
                                       cursor='hand2', relief=tk.RAISED, bd=2)
        refresh_preview_btn.pack(pady=3)

        # Log area với shadow
        log_frame = tk.LabelFrame(right_panel, text="📋 Log", 
                                 font=("Arial", 9, "bold"), bg='white',
                                 relief=tk.GROOVE, bd=2)
        log_frame.pack(fill=tk.BOTH, expand=False, padx=15, pady=5)

        log_shadow_frame = tk.Frame(log_frame, bg='#999999', relief=tk.SUNKEN, bd=2)
        log_shadow_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.log_text = scrolledtext.ScrolledText(log_shadow_frame, 
                                                  font=("Consolas", 8),
                                                  bg="#1e1e1e", fg="#00ff00",
                                                  height=5,
                                                  relief=tk.FLAT,
                                                  borderwidth=0)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        clear_log_btn = tk.Button(log_frame, text="🗑️ Clear Log", 
                                 command=self.clear_log,
                                 font=("Arial", 8), bg="#95a5a6", fg="white",
                                 cursor='hand2', relief=tk.RAISED, bd=2)
        clear_log_btn.pack(pady=3)

        # Bind event để update current file label khi đổi tab
        self.notebook.bind('<<NotebookTabChanged>>', self.on_tab_changed)

        # Auto load files nếu có folder
        if self.folder_path.get() and Path(self.folder_path.get()).exists():
            self.load_files(auto=True)

        # Auto refresh preview
        self.refresh_preview()

    def on_tab_changed(self, event):
        """Update label hiển thị file đang xem khi đổi tab"""
        try:
            current_tab = self.notebook.select()
            if current_tab:
                tab_index = self.notebook.index(current_tab)
                if tab_index in self.tab_filenames:
                    filename = self.tab_filenames[tab_index]
                    self.current_file_label.config(text=f"📄 {filename}")
        except:
            pass

    def get_current_text_widget(self):
        """Lấy text widget của tab đang active"""
        try:
            current_tab = self.notebook.select()
            if current_tab:
                tab_index = self.notebook.index(current_tab)
                if tab_index in self.tab_filenames:
                    filename = self.tab_filenames[tab_index]
                    return self.tabs.get(filename), filename
        except:
            pass
        return None, None

    def highlight_text(self):
        """Highlight tất cả từ khóa tìm thấy trong tab hiện tại"""
        search_term = self.search_text.get().strip()
        if not search_term:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập từ khóa tìm kiếm!")
            return

        text_widget, filename = self.get_current_text_widget()
        if not text_widget:
            messagebox.showwarning("Cảnh báo", "Không có tab nào được chọn!")
            return

        # Clear previous highlights
        text_widget.tag_remove("highlight", "1.0", tk.END)

        # Configure highlight tag
        text_widget.tag_config("highlight", background="#FFFF00", foreground="#000000")

        # Search and highlight
        text_widget.config(state=tk.NORMAL)
        content = text_widget.get("1.0", tk.END)
        start_pos = "1.0"
        count = 0

        while True:
            start_pos = text_widget.search(search_term, start_pos, tk.END, nocase=True)
            if not start_pos:
                break

            end_pos = f"{start_pos}+{len(search_term)}c"
            text_widget.tag_add("highlight", start_pos, end_pos)
            start_pos = end_pos
            count += 1

        text_widget.config(state=tk.DISABLED)

        # Update match count
        if count > 0:
            self.match_label.config(text=f"✓ Tìm thấy {count} kết quả", fg="#27ae60")
            # Scroll to first match
            first_match = text_widget.tag_ranges("highlight")
            if first_match:
                text_widget.see(first_match[0])
        else:
            self.match_label.config(text="✗ Không tìm thấy", fg="#e74c3c")
            messagebox.showinfo("Tìm kiếm", f"Không tìm thấy '{search_term}'")

    def clear_highlight(self):
        """Xóa tất cả highlight"""
        text_widget, _ = self.get_current_text_widget()
        if text_widget:
            text_widget.tag_remove("highlight", "1.0", tk.END)
        self.match_label.config(text="")
        self.search_text.set("")

    def copy_content(self):
        """Copy toàn bộ nội dung tab hiện tại - GIỐNG CTRL+A + CTRL+C"""
        text_widget, filename = self.get_current_text_widget()
        if not text_widget:
            messagebox.showwarning("Cảnh báo", "Không có tab nào được chọn!")
            return

        # Lấy toàn bộ nội dung từ đầu đến cuối (KHÔNG strip để giữ nguyên format)
        # get("1.0", "end-1c") để bỏ ký tự newline cuối cùng mà Tkinter tự thêm
        content = text_widget.get("1.0", "end-1c")

        if content:
            # Clear clipboard và copy nội dung mới
            self.root.clipboard_clear()
            self.root.clipboard_append(content)
            self.root.update()  # Đảm bảo clipboard được update

            # Đếm số dòng và ký tự
            lines = content.count('\n') + 1
            chars = len(content)

            # Show notification
            self.match_label.config(text=f"✓ Đã copy {filename}!", fg="#27ae60")
            self.root.after(3000, lambda: self.match_label.config(text=""))

            messagebox.showinfo("✅ Copy thành công", 
                              f"Đã copy toàn bộ nội dung:\n\n"
                              f"📄 File: {filename}\n"
                              f"📊 {lines:,} dòng\n"
                              f"📝 {chars:,} ký tự\n\n"
                              f"Giờ có thể Paste (Ctrl+V) ở bất kỳ đâu!")
        else:
            messagebox.showwarning("Cảnh báo", "Nội dung file rỗng!")

    def browse_folder(self):
        folder = filedialog.askdirectory(initialdir=self.folder_path.get())
        if folder:
            self.folder_path.set(folder)
            save_config(folder_path=folder)
            self.log(f"✓ Đã chọn folder: {folder}\n")

    def load_files(self, auto=False):
        """Load các file .txt từ thư mục out_tags"""
        folder = self.folder_path.get().strip()
        if not folder:
            if not auto:
                messagebox.showwarning("⚠️ Cảnh báo", "Vui lòng chọn folder!")
            return

        if not os.path.exists(folder):
            if not auto:
                messagebox.showerror("❌ Lỗi", "Folder không tồn tại!")
            return

        # Save config
        save_config(folder_path=folder)

        # Load files
        txt_files = load_text_files(folder)

        if txt_files is None:
            if not auto:
                messagebox.showerror("❌ Lỗi", "Không tìm thấy thư mục 'out_tags'!")
            return

        if not txt_files:
            if not auto:
                messagebox.showinfo("ℹ️ Thông báo", "Không có file .txt trong out_tags!")
            return

        # Xóa tabs cũ
        for tab_id in self.notebook.tabs():
            self.notebook.forget(tab_id)
        self.tabs.clear()
        self.tab_filenames.clear()

        # Tạo tabs mới
        all_tags_index = None
        for idx, (filename, content) in enumerate(txt_files.items()):
            self.create_tab(filename, content, idx)
            # Tìm index của all_tags.txt
            if filename.lower() == "all_tags.txt":
                all_tags_index = idx

        # Chọn tab all_tags.txt làm mặc định
        if all_tags_index is not None:
            self.notebook.select(all_tags_index)
            self.on_tab_changed(None)

        if not auto:
            messagebox.showinfo("✅ Thành công", f"Đã load {len(txt_files)} file!\n(Mặc định: all_tags.txt)")

    def create_tab(self, filename, content, tab_index):
        """Tạo tab mới với nội dung file"""
        tab_frame = ttk.Frame(self.notebook)

        # Info frame với shadow
        info_frame = tk.Frame(tab_frame, bg='#e8f4f8', pady=5, relief=tk.RAISED, bd=2)
        info_frame.pack(fill=tk.X, padx=5, pady=5)

        # Đếm số dòng
        line_count = content.count('\n') + 1
        char_count = len(content)

        tk.Label(info_frame, text=f"📄 {filename}  •  {line_count:,} dòng  •  {char_count:,} ký tự",
                font=("Arial", 9, 'bold'), bg='#e8f4f8',
                fg='#1976D2').pack(side=tk.LEFT, padx=10)

        # Text area với shadow
        text_frame = tk.Frame(tab_frame, bg='#999999', relief=tk.SUNKEN, bd=2)
        text_frame.pack(expand=1, fill='both', padx=5, pady=5)

        text_container = tk.Frame(text_frame)
        text_container.pack(expand=1, fill='both', padx=2, pady=2)

        scrollbar_y = tk.Scrollbar(text_container)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)

        text_widget = tk.Text(text_container,
                             wrap=tk.WORD,
                             yscrollcommand=scrollbar_y.set,
                             font=("Consolas", 10),
                             padx=10, pady=10,
                             bg='#ffffff',
                             fg='#333333',
                             relief=tk.FLAT,
                             borderwidth=0)
        text_widget.pack(expand=1, fill='both')
        scrollbar_y.config(command=text_widget.yview)

        text_widget.insert('1.0', content)
        text_widget.config(state=tk.DISABLED)

        # Display name
        display_name = filename.replace('.txt', '')[:20]
        if len(filename) > 23:
            display_name += '...'

        self.notebook.add(tab_frame, text=f" {display_name} ")
        self.tabs[filename] = text_widget
        self.tab_filenames[tab_index] = filename

    def log(self, message):
        self.log_text.insert(tk.END, message)
        self.log_text.see(tk.END)
        self.root.update()

    def clear_log(self):
        self.log_text.delete(1.0, tk.END)

    def clear_tag_input(self):
        """Xóa nội dung tag input"""
        self.tag_input.delete("1.0", tk.END)

    def refresh_preview(self):
        """Refresh preview nội dung file"""
        self.preview_text.config(state=tk.NORMAL)
        self.preview_text.delete("1.0", tk.END)

        preview = get_file_preview(self.tag_output_file)
        self.preview_text.insert("1.0", preview)

        self.preview_text.config(state=tk.DISABLED)

    def run_convert_webp(self):
        folder = self.folder_path.get()
        if not folder or not Path(folder).exists():
            messagebox.showerror("Lỗi", "Vui lòng chọn folder hợp lệ!")
            return

        self.clear_log()
        self.log("=== BẮT ĐẦU CONVERT WEBP TO JPG ===\n\n")

        def task():
            try:
                convert_webp_to_jpg(folder, self.log)
            except Exception as e:
                self.log(f"\n❌ LỖI: {str(e)}\n")

        thread = threading.Thread(target=task)
        thread.start()

    def run_process_tags(self):
        folder = self.folder_path.get()
        if not folder or not Path(folder).exists():
            messagebox.showerror("Lỗi", "Vui lòng chọn folder hợp lệ!")
            return

        self.clear_log()
        self.log("=== BẮT ĐẦU XỬ LÝ TAGS ===\n\n")

        def task():
            try:
                process_tags(folder, self.log)
                # Auto reload files sau khi xử lý xong
                self.root.after(1000, lambda: self.load_files(auto=True))
            except Exception as e:
                self.log(f"\n❌ LỖI: {str(e)}\n")

        thread = threading.Thread(target=task)
        thread.start()

    def run_remove_tags(self):
        """NÚT THỨ 3: Xóa đè tags không mong muốn, sau đó TỰ ĐỘNG chạy Process Tags"""
        folder = self.folder_path.get()
        if not folder or not Path(folder).exists():
            messagebox.showerror("Lỗi", "Vui lòng chọn folder hợp lệ!")
            return

        # Confirm
        confirm = messagebox.askyesno(
            "⚠️ Xác nhận", 
            "Xóa đè sẽ loại bỏ các tags không mong muốn khỏi TẤT CẢ file .txt trong folder!\n\nSau đó sẽ TỰ ĐỘNG chạy Process Tags.\n\nBạn có chắc chắn?"
        )
        if not confirm:
            return

        self.clear_log()
        self.log("=== BẮT ĐẦU XÓA ĐÈ TAGS ===\n\n")

        def task():
            try:
                # Bước 1: Xóa đè tags
                remove_tags_from_folder(folder, self.log)

                # Bước 2: Tự động chạy Process Tags
                self.log("\n" + "="*50 + "\n")
                self.log("🔄 TỰ ĐỘNG CHẠY PROCESS TAGS...\n")
                self.log("="*50 + "\n\n")

                process_tags(folder, self.log)

                # Auto reload files sau khi hoàn thành tất cả
                self.root.after(1000, lambda: self.load_files(auto=True))

                self.log("\n" + "="*50 + "\n")
                self.log("✅ HOÀN THÀNH: Xóa Đè + Process Tags\n")
                self.log("="*50 + "\n")

            except Exception as e:
                self.log(f"\n❌ LỖI: {str(e)}\n")

        thread = threading.Thread(target=task)
        thread.start()

    def save_tags(self):
        """Lưu tags (append) và XÓA nội dung sau khi save thành công"""
        tags_content = self.tag_input.get("1.0", tk.END).strip()
        if not tags_content:
            messagebox.showwarning("Cảnh báo", "Không có nội dung tags để lưu!")
            return

        self.clear_log()
        self.log("=== SAVE TAGS (APPEND) ===\n\n")

        # Save tags
        success = save_tags_to_file(self.tag_output_file, tags_content, 'append', self.log)

        if success:
            # XÓA NỘI DUNG trong tag input sau khi save thành công
            self.tag_input.delete("1.0", tk.END)
            self.log("\n🗑️ Đã xóa nội dung input\n")

            # Refresh preview
            self.refresh_preview()

            self.log("\n✅ Lưu tags thành công!\n")
