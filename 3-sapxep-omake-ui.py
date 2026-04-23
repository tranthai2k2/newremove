import os
import tkinter as tk
from tkinter import scrolledtext
import threading
import queue
import shutil


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff"}


def list_image_files(folder_path):
    return sorted([
        f for f in os.listdir(folder_path)
        if os.path.isfile(os.path.join(folder_path, f))
        and os.path.splitext(f)[1].lower() in IMAGE_EXTENSIONS
    ])


def rename_images_sequential(omake_folder, log):
    subfolders = sorted([
        f for f in os.listdir(omake_folder)
        if os.path.isdir(os.path.join(omake_folder, f))
    ])

    folder_groups = []
    root_files = list_image_files(omake_folder)
    if root_files:
        folder_groups.append((omake_folder, "Omake", root_files))

    for folder_name in subfolders:
        folder_path = os.path.join(omake_folder, folder_name)
        files = list_image_files(folder_path)
        if files:
            folder_groups.append((folder_path, folder_name, files))

    if not folder_groups:
        log("⚠️ Không có ảnh trong thư mục Omake này.")
        return 0

    log("🔄 Bước 1: Đổi tên tạm thời...")
    file_list = []
    temp_counter = 1

    for folder_path, folder_name, files in folder_groups:
        log(f"📂 {folder_name}: {len(files)} ảnh")
        for image_name in files:
            old_path = os.path.join(folder_path, image_name)
            ext = os.path.splitext(image_name)[1].lower()
            temp_name = f"__temp_{temp_counter:04d}{ext}"
            temp_path = os.path.join(folder_path, temp_name)
            os.rename(old_path, temp_path)
            file_list.append((folder_path, folder_name, temp_name, ext))
            if temp_counter % 300 == 0:
                log(f"   ...đã đổi tạm {temp_counter} ảnh")
            temp_counter += 1

    log("📝 Bước 2: Đổi tên cuối cùng...\n")
    current_folder = None
    folder_counter = 0
    counter = 1

    for folder_path, folder_name, temp_name, ext in file_list:
        if folder_name != current_folder:
            if current_folder is not None:
                log(f"  ✅ {folder_counter} ảnh")
                log("")
            log(f"📁 Folder: {folder_name}")
            current_folder = folder_name
            folder_counter = 0
        new_name = f"{counter:04d}{ext}"
        temp_path = os.path.join(folder_path, temp_name)
        new_path = os.path.join(folder_path, new_name)
        os.rename(temp_path, new_path)
        folder_counter += 1
        if counter % 300 == 0:
            log(f"   ...đã đổi tên xong {counter} ảnh")
        counter += 1

    if current_folder is not None:
        log(f"  ✅ {folder_counter} ảnh")

    log(f"\n✅ Hoàn thành! Đã đổi tên {counter - 1} ảnh.")
    return counter - 1


def find_omake_folders(path):
    normalized = os.path.normpath(path)
    if os.path.basename(normalized).lower() == "omake":
        return [normalized]

    omake_folders = []
    for root_path, dir_names, _ in os.walk(path):
        for dir_name in dir_names:
            if dir_name.lower() == "omake":
                omake_folders.append(os.path.join(root_path, dir_name))

    omake_folders.sort(key=lambda p: p.lower())
    return omake_folders


def list_image_paths_recursive(folder_path):
    image_paths = []
    for root_path, dir_names, file_names in os.walk(folder_path):
        dir_names.sort(key=str.lower)
        for file_name in sorted(file_names, key=str.lower):
            if os.path.splitext(file_name)[1].lower() in IMAGE_EXTENSIONS:
                image_paths.append(os.path.join(root_path, file_name))
    return image_paths


def unique_destination_path(target_folder, file_name):
    target_path = os.path.join(target_folder, file_name)
    if not os.path.exists(target_path):
        return target_path

    base_name, ext = os.path.splitext(file_name)
    duplicate_index = 1
    while True:
        candidate_name = f"{base_name}_{duplicate_index:02d}{ext}"
        candidate_path = os.path.join(target_folder, candidate_name)
        if not os.path.exists(candidate_path):
            return candidate_path
        duplicate_index += 1


def move_omake_images_to_set(omake_folder, log):
    set_folder = os.path.dirname(os.path.normpath(omake_folder))
    image_paths = list_image_paths_recursive(omake_folder)
    if not image_paths:
        log("⚠️ Không có ảnh để chuyển từ Omake.")
        return 0

    log(f"📤 Chuyển {len(image_paths)} ảnh từ Omake ra bộ...")
    moved_count = 0
    for source_path in image_paths:
        target_path = unique_destination_path(set_folder, os.path.basename(source_path))
        os.rename(source_path, target_path)
        moved_count += 1
        if moved_count % 300 == 0:
            log(f"   ...đã chuyển {moved_count} ảnh")

    log(f"✅ Đã chuyển {moved_count} ảnh vào bộ: {set_folder}")
    return moved_count


def delete_main_and_omake_folders(set_folder, log):
    removed = []
    failed = []

    for entry in os.listdir(set_folder):
        target_path = os.path.join(set_folder, entry)
        if not os.path.isdir(target_path):
            continue
        if entry.lower() not in {"main", "omake"}:
            continue
        try:
            shutil.rmtree(target_path)
            removed.append(entry)
        except Exception as e:
            failed.append((entry, str(e)))

    if removed:
        log(f"🗑️ Đã xóa thư mục: {', '.join(sorted(removed, key=str.lower))}")
    else:
        log("⚠️ Không có thư mục Main/Omake để xóa.")

    for folder_name, error_msg in failed:
        log(f"❌ Không thể xóa {folder_name}: {error_msg}")

    return len(removed)


def count_images_recursive(folder_path):
    image_count = 0
    for _, _, file_names in os.walk(folder_path):
        for file_name in file_names:
            if os.path.splitext(file_name)[1].lower() in IMAGE_EXTENSIONS:
                image_count += 1
    return image_count


def delete_folder_if_too_few_images(folder_path, minimum_images, log):
    if not os.path.isdir(folder_path):
        return False

    image_count = count_images_recursive(folder_path)
    if image_count >= minimum_images:
        return False

    try:
        shutil.rmtree(folder_path)
        log(f"🗑️ Xóa folder < {minimum_images} ảnh ({image_count} ảnh): {folder_path}")
        return True
    except Exception as e:
        log(f"❌ Không thể xóa folder ít ảnh {folder_path}: {e}")
        return False


def delete_empty_folders(root_folder, log):
    if not os.path.isdir(root_folder):
        return 0

    root_norm = os.path.normcase(os.path.normpath(root_folder))
    removed_count = 0

    for current_path, _, _ in os.walk(root_folder, topdown=False):
        current_norm = os.path.normcase(os.path.normpath(current_path))
        if current_norm == root_norm:
            continue
        try:
            if not os.listdir(current_path):
                os.rmdir(current_path)
                removed_count += 1
        except Exception:
            continue

    if removed_count:
        log(f"🧹 Đã xóa {removed_count} folder rỗng.")
    else:
        log("ℹ️ Không có folder rỗng để xóa.")

    return removed_count


def run():
    folder = text_folder.get("1.0", tk.END).strip()
    if not folder or not os.path.isdir(folder):
        enqueue_log("❌ Đường dẫn không hợp lệ!")
        return

    omake_folders = find_omake_folders(folder)
    if not omake_folders:
        enqueue_log("❌ Không tìm thấy thư mục Omake!")
        return

    set_run_button(False)
    clear_log()
    enqueue_log(f"🎯 Tìm thấy {len(omake_folders)} thư mục Omake.")

    def task():
        total_renamed = 0
        total_moved = 0
        total_deleted_folders = 0
        total_deleted_small_folders = 0
        total_deleted_empty_folders = 0
        try:
            for index, omake_folder in enumerate(omake_folders, start=1):
                enqueue_log("")
                enqueue_log(f"===== Omake {index}/{len(omake_folders)} =====")
                enqueue_log(omake_folder)
                try:
                    total_renamed += rename_images_sequential(omake_folder, enqueue_log)
                    total_moved += move_omake_images_to_set(omake_folder, enqueue_log)
                    set_folder = os.path.dirname(os.path.normpath(omake_folder))
                    total_deleted_folders += delete_main_and_omake_folders(set_folder, enqueue_log)
                    if delete_folder_if_too_few_images(set_folder, 10, enqueue_log):
                        total_deleted_small_folders += 1
                except Exception as e:
                    enqueue_log(f"❌ Lỗi ở {omake_folder}: {e}")

            cleanup_root = folder if os.path.isdir(folder) else os.path.dirname(folder)
            total_deleted_empty_folders = delete_empty_folders(cleanup_root, enqueue_log)

            enqueue_log(
                f"\n🎉 Xong toàn bộ Omake. Tổng ảnh đã đổi: {total_renamed}. "
                f"Tổng ảnh đã đưa ra bộ: {total_moved}. "
                f"Tổng thư mục Main/Omake đã xóa: {total_deleted_folders}. "
                f"Folder < 10 ảnh đã xóa: {total_deleted_small_folders}. "
                f"Folder rỗng đã xóa: {total_deleted_empty_folders}"
            )
        finally:
            set_run_button(True)

    threading.Thread(target=task, daemon=True).start()


def enqueue_log(msg):
    log_queue.put(str(msg))


def flush_log_queue():
    text_log.config(state=tk.NORMAL)
    flushed = 0
    while flushed < 200:
        try:
            msg = log_queue.get_nowait()
        except queue.Empty:
            break
        text_log.insert(tk.END, msg + "\n")
        flushed += 1
    if flushed:
        text_log.see(tk.END)
    text_log.config(state=tk.DISABLED)
    root.after(80, flush_log_queue)


def clear_log():
    text_log.config(state=tk.NORMAL)
    text_log.delete("1.0", tk.END)
    text_log.config(state=tk.DISABLED)


def set_run_button(is_enabled):
    state = tk.NORMAL if is_enabled else tk.DISABLED
    if threading.current_thread() is threading.main_thread():
        btn_run.config(state=state)
    else:
        root.after(0, lambda: btn_run.config(state=state))


root = tk.Tk()
root.title("Sắp xếp ảnh Omake")
root.resizable(False, False)
log_queue = queue.Queue()

tk.Label(root, text="Đường dẫn folder:").pack(anchor="w", padx=10, pady=(10, 0))

text_folder = tk.Text(root, height=3, width=60, wrap=tk.WORD)
text_folder.pack(padx=10, pady=4)

btn_run = tk.Button(root, text="▶ Chạy", command=run, width=20, bg="#4CAF50", fg="white", font=("Arial", 10, "bold"))
btn_run.pack(pady=6)

tk.Label(root, text="Log:").pack(anchor="w", padx=10)
text_log = scrolledtext.ScrolledText(root, height=18, width=60, state=tk.DISABLED)
text_log.pack(padx=10, pady=(0, 10))

root.after(80, flush_log_queue)
root.mainloop()
