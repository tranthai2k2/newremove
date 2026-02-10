import tkinter as tk
from tkinter import messagebox
import re
import os

FILE_PATH = './wantremove/name2.txt'

def normalize_whitespace(text):
    """Rút gọn nhiều khoảng trắng thành 1, bỏ khoảng trắng dư"""
    return re.sub(r'\s+', ' ', text).strip()

def escape_parentheses(text):
    """Thêm escape vào dấu ()"""
    return re.sub(r'([\(\)])', r'\\\1', text)

def unescape_parentheses(text):
    """Bỏ escape khỏi dấu ()"""
    return text.replace(r'\(', '(').replace(r'\)', ')')

def add_character_tag():
    raw_input = entry.get()
    character_name = normalize_whitespace(raw_input)

    if not character_name:
        messagebox.showwarning("Lỗi", "Vui lòng nhập tên nhân vật.")
        return

    escaped_name = escape_parentheses(character_name)
    unescaped_name = unescape_parentheses(character_name)

    # Đọc nội dung file
    if not os.path.exists(FILE_PATH):
        open(FILE_PATH, 'w', encoding='utf-8').close()

    with open(FILE_PATH, 'r', encoding='utf-8') as f:
        content = f.read().strip()

    tag_list = [tag.strip() for tag in content.split(',') if tag.strip()]

    if character_name in tag_list or escaped_name in tag_list or unescaped_name in tag_list:
        messagebox.showinfo("Thông báo", "Tag đã tồn tại.")
        return

    # Thêm cả 2 phiên bản nếu chưa có
    new_tags = [character_name, escaped_name] if character_name != escaped_name else [character_name]

    if content and not content.endswith(','):
        content += ','

    content += ' ' + ', '.join(new_tags)

    with open(FILE_PATH, 'w', encoding='utf-8') as f:
        f.write(content.strip())

    messagebox.showinfo("Thành công", "Đã thêm:\n- " + '\n- '.join(new_tags))
    entry.delete(0, tk.END)

# UI setup
root = tk.Tk()
root.title("Thêm Tag Nhân Vật")

tk.Label(root, text="Nhập tên nhân vật:").pack(pady=5)
entry = tk.Entry(root, width=50)
entry.pack(padx=10, pady=5)

btn = tk.Button(root, text="Thêm vào file", command=add_character_tag)
btn.pack(pady=10)

root.mainloop()
