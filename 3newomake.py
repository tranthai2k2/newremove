import os
import shutil
import tkinter as tk
from tkinter import scrolledtext
import threading

image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff'}


def rename_images_sequential(omake_path, log):
    """Đổi tên ảnh tuần tự trong các subfolder cấp 3 của omake folder."""
    subfolders = sorted([
        f for f in os.listdir(omake_path)
        if os.path.isdir(os.path.join(omake_path, f))
    ])

    file_list = []
    temp_counter = 1

    for folder_name in subfolders:
        folder_path = os.path.join(omake_path, folder_name)
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
            file_list.append((folder_path, image_name, temp_name, ext))
            temp_counter += 1

    counter = 1
    for folder_path, original_name, temp_name, ext in file_list:
        new_name = f"{counter:04d}{ext}"
        temp_path = os.path.join(folder_path, temp_name)
        new_path = os.path.join(folder_path, new_name)
        os.rename(temp_path, new_path)
        log(f"      {original_name} → {new_name}")
        counter += 1

    return counter - 1


def move_images_to_cap1(omake_path, cap1_path, log):
    """Cắt toàn bộ ảnh từ các subfolder cấp 3 ra folder cấp 1."""
    subfolders = sorted([
        f for f in os.listdir(omake_path)
        if os.path.isdir(os.path.join(omake_path, f))
    ])

    moved = 0
    for folder_name in subfolders:
        folder_path = os.path.join(omake_path, folder_name)
        files = sorted([
            f for f in os.listdir(folder_path)
            if os.path.splitext(f)[1].lower() in image_extensions
        ])
        for image_name in files:
            src = os.path.join(folder_path, image_name)
            dst = os.path.join(cap1_path, image_name)
            shutil.move(src, dst)
            moved += 1

    return moved


def move_direct_images(src_folder, dst_folder, log):
    """Cắt ảnh trực tiếp trong src_folder (không qua subfolder) lên dst_folder."""
    files = sorted([
        f for f in os.listdir(src_folder)
        if os.path.splitext(f)[1].lower() in image_extensions
        and os.path.isfile(os.path.join(src_folder, f))
    ])
    moved = 0
    for image_name in files:
        src = os.path.join(src_folder, image_name)
        dst = os.path.join(dst_folder, image_name)
        shutil.move(src, dst)
        moved += 1
    return moved


def process_all(parent_folder, log):
    cap1_list = sorted([
        f for f in os.listdir(parent_folder)
        if os.path.isdir(os.path.join(parent_folder, f))
    ])

    total_renamed = 0
    total_moved = 0

    for cap1_name in cap1_list:
        cap1_path = os.path.join(parent_folder, cap1_name)
        log(f"\n📂 {cap1_name}")

        # Phân loại folder cấp 2
        with_subfolders = []   # có cấp 3 → rename + cut
        direct_images = []     # chỉ có ảnh trực tiếp → cut thẳng

        for cap2_name in sorted(os.listdir(cap1_path)):
            cap2_path = os.path.join(cap1_path, cap2_name)
            if not os.path.isdir(cap2_path):
                continue
            if "omake" not in cap2_name.lower():
                continue
            has_subfolders = any(
                os.path.isdir(os.path.join(cap2_path, x))
                for x in os.listdir(cap2_path)
            )
            has_images = any(
                os.path.splitext(x)[1].lower() in image_extensions
                for x in os.listdir(cap2_path)
                if os.path.isfile(os.path.join(cap2_path, x))
            )
            if "upscaled" in cap2_name.lower():
                direct_images.append((cap2_name, cap2_path))
            elif has_subfolders:
                with_subfolders.append((cap2_name, cap2_path))
            elif has_images:
                direct_images.append((cap2_name, cap2_path))

        if not with_subfolders and not direct_images:
            log("  ⚠️  Không tìm thấy omake folder, bỏ qua.")
            continue

        # Xử lý folder có cấp 3 (rename + cut)
        for omake_name, omake_path in with_subfolders:
            log(f"  🗂  Omake (có subfolder): {omake_name}")
            log("    🔄 Đổi tên tuần tự...")
            count = rename_images_sequential(omake_path, log)
            log(f"    ✅ Đổi tên {count} ảnh xong.")

            log("    ✂️  Cắt ảnh → folder cấp 1...")
            moved = move_images_to_cap1(omake_path, cap1_path, log)
            log(f"    📦 Đã cắt {moved} ảnh vào [{cap1_name}]")

            total_renamed += count
            total_moved += moved

        # Xử lý folder chỉ có ảnh trực tiếp (cut thẳng)
        for omake_name, omake_path in direct_images:
            log(f"  🗂  Omake (ảnh trực tiếp): {omake_name}")
            log("    ✂️  Cắt ảnh → folder cấp 1...")
            moved = move_direct_images(omake_path, cap1_path, log)
            log(f"    📦 Đã cắt {moved} ảnh vào [{cap1_name}]")
            total_moved += moved

    log(f"\n🎉 Hoàn thành! Tổng: {total_renamed} ảnh đổi tên, {total_moved} ảnh cắt ra.")


# ─── UI ───────────────────────────────────────────────────────────────────────

def run():
    folder = text_folder.get("1.0", tk.END).strip()
    if not folder or not os.path.isdir(folder):
        log_output("❌ Đường dẫn không hợp lệ!")
        return

    btn_run.config(state=tk.DISABLED)
    text_log.config(state=tk.NORMAL)
    text_log.delete("1.0", tk.END)
    text_log.config(state=tk.DISABLED)

    def task():
        try:
            process_all(folder, log_output)
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
root.title("New Omake - Sắp xếp & Cắt ảnh")
root.resizable(False, False)

tk.Label(root, text="Đường dẫn folder chính:").pack(anchor="w", padx=10, pady=(10, 0))

text_folder = tk.Text(root, height=3, width=65, wrap=tk.WORD)
text_folder.pack(padx=10, pady=4)

btn_run = tk.Button(root, text="▶ Chạy", command=run, width=20,
                    bg="#4CAF50", fg="white", font=("Arial", 10, "bold"))
btn_run.pack(pady=6)

tk.Label(root, text="Log:").pack(anchor="w", padx=10)
text_log = scrolledtext.ScrolledText(root, height=20, width=65, state=tk.DISABLED)
text_log.pack(padx=10, pady=(0, 10))

root.mainloop()
