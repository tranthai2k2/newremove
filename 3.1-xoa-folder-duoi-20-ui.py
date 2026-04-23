import os
import shutil
import threading
import queue
import tkinter as tk
from tkinter import scrolledtext


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff"}
MIN_IMAGES = 20


def count_direct_images(file_names):
    return sum(1 for name in file_names if os.path.splitext(name)[1].lower() in IMAGE_EXTENSIONS)


def plan_folders_to_delete(root_folder, minimum_images):
    root_norm = os.path.normcase(os.path.normpath(root_folder))
    folder_info = {}

    for current_path, dir_names, file_names in os.walk(root_folder, topdown=False):
        direct_images = count_direct_images(file_names)
        total_images = direct_images

        for dir_name in dir_names:
            child_path = os.path.join(current_path, dir_name)
            child_info = folder_info.get(child_path)
            if child_info and not child_info["will_delete"]:
                total_images += child_info["total_images"]

        current_norm = os.path.normcase(os.path.normpath(current_path))
        will_delete = current_norm != root_norm and total_images < minimum_images
        folder_info[current_path] = {"total_images": total_images, "will_delete": will_delete}

    delete_candidates = [
        (path, info["total_images"])
        for path, info in folder_info.items()
        if info["will_delete"]
    ]
    delete_candidates.sort(key=lambda item: item[0].count(os.sep))

    pruned_delete_list = []
    kept_parent_norms = []
    for path, image_count in delete_candidates:
        norm_path = os.path.normcase(os.path.normpath(path))
        has_deleted_parent = any(
            norm_path == parent_norm or norm_path.startswith(parent_norm + os.sep)
            for parent_norm in kept_parent_norms
        )
        if has_deleted_parent:
            continue
        pruned_delete_list.append((path, image_count))
        kept_parent_norms.append(norm_path)

    pruned_delete_list.sort(key=lambda item: item[0].count(os.sep), reverse=True)
    return pruned_delete_list, len(folder_info)


def delete_folders(delete_list, log):
    deleted_count = 0
    failed_count = 0

    for index, (folder_path, image_count) in enumerate(delete_list, start=1):
        try:
            shutil.rmtree(folder_path)
            deleted_count += 1
            log(f"[{index}/{len(delete_list)}] Da xoa ({image_count} anh): {folder_path}")
        except Exception as e:
            failed_count += 1
            log(f"[{index}/{len(delete_list)}] Loi xoa folder {folder_path}: {e}")

    return deleted_count, failed_count


def run():
    root_folder = text_folder.get("1.0", tk.END).strip()
    if not root_folder or not os.path.isdir(root_folder):
        enqueue_log("Duong dan khong hop le.")
        return

    set_run_button(False)
    clear_log()
    enqueue_log(f"Bat dau quet de xoa folder co < {MIN_IMAGES} anh...")

    def task():
        try:
            delete_list, scanned_folders = plan_folders_to_delete(root_folder, MIN_IMAGES)
            enqueue_log(f"Da quet {scanned_folders} folder.")
            enqueue_log(f"Tim thay {len(delete_list)} folder can xoa.")

            if not delete_list:
                enqueue_log("Khong co folder nao can xoa.")
                return

            deleted_count, failed_count = delete_folders(delete_list, enqueue_log)
            enqueue_log(
                f"Xong. Da xoa: {deleted_count} folder. Loi: {failed_count} folder."
            )
        except Exception as e:
            enqueue_log(f"Loi: {e}")
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
root.title("3.1 - Xoa folder < 20 anh")
root.resizable(False, False)
log_queue = queue.Queue()

tk.Label(root, text="Duong dan folder:").pack(anchor="w", padx=10, pady=(10, 0))

text_folder = tk.Text(root, height=3, width=60, wrap=tk.WORD)
text_folder.pack(padx=10, pady=4)

btn_run = tk.Button(
    root,
    text="Chay",
    command=run,
    width=20,
    bg="#4CAF50",
    fg="white",
    font=("Arial", 10, "bold"),
)
btn_run.pack(pady=6)

tk.Label(root, text="Log:").pack(anchor="w", padx=10)
text_log = scrolledtext.ScrolledText(root, height=18, width=60, state=tk.DISABLED)
text_log.pack(padx=10, pady=(0, 10))

root.after(80, flush_log_queue)
root.mainloop()
