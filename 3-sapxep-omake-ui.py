import os
import tkinter as tk
from tkinter import scrolledtext
import threading


def rename_images_sequential(parent_folder, log):
    subfolders = sorted([
        f for f in os.listdir(parent_folder)
        if os.path.isdir(os.path.join(parent_folder, f))
    ])

    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff'}

    log("🔄 Bước 1: Đổi tên tạm thời...")
    file_list = []
    temp_counter = 1

    for folder_name in subfolders:
        folder_path = os.path.join(parent_folder, folder_name)
        files = sorted([
            f for f in os.listdir(folder_path)
            if os.path.splitext(f)[1].lower() in image_extensions
        ])
        for image_name in files:
            old_path = os.path.join(folder_path, image_name)
            ext = os.path.splitext(image_name)[1].lower()
            temp_name = f"__temp_{temp_counter:04d}{ext}"
            temp_path = os.path.join(folder_path, temp_name)
            os.rename(old_path, temp_path)
            file_list.append((folder_path, folder_name, image_name, temp_name, ext))
            temp_counter += 1

    log("📝 Bước 2: Đổi tên cuối cùng...\n")
    current_folder = None
    counter = 1

    for folder_path, folder_name, original_name, temp_name, ext in file_list:
        if folder_name != current_folder:
            if current_folder is not None:
                log("")
            log(f"📁 Folder: {folder_name}")
            current_folder = folder_name
        new_name = f"{counter:04d}{ext}"
        temp_path = os.path.join(folder_path, temp_name)
        new_path = os.path.join(folder_path, new_name)
        os.rename(temp_path, new_path)
        log(f"  {original_name} → {new_name}")
        counter += 1

    log(f"\n✅ Hoàn thành! Đã đổi tên {counter - 1} ảnh.")


def run():
    folder = text_folder.get("1.0", tk.END).strip()
    if not folder or not os.path.isdir(folder):
        log_output("❌ Đường dẫn không hợp lệ!")
        return

    btn_run.config(state=tk.DISABLED)
    text_log.config(state=tk.NORMAL)
    text_log.delete("1.0", tk.END)

    def task():
        try:
            rename_images_sequential(folder, log_output)
        except Exception as e:
            log_output(f"❌ Lỗi: {e}")
        finally:
            btn_run.config(state=tk.NORMAL)

    threading.Thread(target=task, daemon=True).start()


def log_output(msg):
    text_log.config(state=tk.NORMAL)
    text_log.insert(tk.END, msg + "\n")
    text_log.see(tk.END)
    text_log.config(state=tk.DISABLED)


root = tk.Tk()
root.title("Sắp xếp ảnh Omake")
root.resizable(False, False)

tk.Label(root, text="Đường dẫn folder:").pack(anchor="w", padx=10, pady=(10, 0))

text_folder = tk.Text(root, height=3, width=60, wrap=tk.WORD)
text_folder.pack(padx=10, pady=4)

btn_run = tk.Button(root, text="▶ Chạy", command=run, width=20, bg="#4CAF50", fg="white", font=("Arial", 10, "bold"))
btn_run.pack(pady=6)

tk.Label(root, text="Log:").pack(anchor="w", padx=10)
text_log = scrolledtext.ScrolledText(root, height=18, width=60, state=tk.DISABLED)
text_log.pack(padx=10, pady=(0, 10))

root.mainloop()
