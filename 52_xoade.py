#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

# ==================== CẤU HÌNH MẶC ĐỊNH ====================

DEFAULT_FOLDER = Path(r"D:\zhangyao\pose-v-2\POSE-MORIAAA\missonary")
DEFAULT_UNWANTED_TAGS_FOLDER = Path(__file__).resolve().parent / "wantremove"

# ============================================================


def load_unwanted_tags(unwanted_tags_folder: Path) -> set[str]:
    if not unwanted_tags_folder.exists():
        raise FileNotFoundError(
            f"Không tìm thấy thư mục tag cần xóa: {unwanted_tags_folder}"
        )

    unwanted_tags: set[str] = set()
    for txt_file in sorted(unwanted_tags_folder.glob("*.txt")):
        with txt_file.open("r", encoding="utf-8-sig") as file:
            line = file.readline().strip()

        if not line:
            continue

        if "," in line:
            split_tags = [tag.strip() for tag in line.split(",") if tag.strip()]
            unwanted_tags.update(split_tags)
        else:
            unwanted_tags.add(line)

    return unwanted_tags


def process_folder(folder_to_process: Path, unwanted_tags: set[str]) -> tuple[int, int]:
    if not folder_to_process.exists():
        raise FileNotFoundError(f"Folder không tồn tại: {folder_to_process}")
    if not folder_to_process.is_dir():
        raise NotADirectoryError(f"Đây không phải folder: {folder_to_process}")

    processed_files = 0
    changed_files = 0

    for txt_file in sorted(folder_to_process.glob("*.txt")):
        processed_files += 1

        with txt_file.open("r", encoding="utf-8-sig") as file:
            line = file.readline().strip()

        if not line:
            continue

        tags = [tag.strip() for tag in line.split(",") if tag.strip()]
        filtered_tags = [tag for tag in tags if tag not in unwanted_tags]
        if filtered_tags != tags:
            changed_files += 1

        with txt_file.open("w", encoding="utf-8") as file:
            file.write(", ".join(filtered_tags))

    return processed_files, changed_files


def run_once(
    folder_to_process: Path,
    unwanted_tags_folder: Path = DEFAULT_UNWANTED_TAGS_FOLDER,
) -> tuple[int, int]:
    unwanted_tags = load_unwanted_tags(unwanted_tags_folder)
    return process_folder(folder_to_process, unwanted_tags)


class XoaDeApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("52 XoaDe UI")
        self.resizable(False, False)
        self.var_folder = tk.StringVar(value=str(DEFAULT_FOLDER))
        self.var_status = tk.StringVar(value="Nhập đường dẫn folder rồi bấm Run.")
        self._build_ui()

    def _build_ui(self):
        frame = ttk.Frame(self, padding=12)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Folder cần xử lý").grid(row=0, column=0, sticky="w")
        entry = ttk.Entry(frame, textvariable=self.var_folder, width=78)
        entry.grid(row=1, column=0, sticky="we", pady=(4, 0))
        entry.focus_set()
        entry.bind("<Return>", lambda _: self._run())

        ttk.Button(frame, text="Run", width=10, command=self._run).grid(
            row=1, column=1, padx=(8, 0), sticky="e"
        )

        ttk.Label(frame, textvariable=self.var_status).grid(
            row=2, column=0, columnspan=2, sticky="w", pady=(10, 0)
        )
        frame.columnconfigure(0, weight=1)

    def _run(self):
        folder_text = self.var_folder.get().strip().strip('"')
        if not folder_text:
            messagebox.showwarning("Thiếu đường dẫn", "Vui lòng nhập đường dẫn folder.")
            return

        folder = Path(folder_text)

        try:
            processed_files, changed_files = run_once(folder)
        except Exception as exc:
            self.var_status.set(f"Lỗi: {exc}")
            messagebox.showerror("Lỗi", str(exc))
            return

        summary = (
            f"Đã xử lý {processed_files} file .txt\n"
            f"Đã cập nhật {changed_files} file"
        )
        self.var_status.set(summary.replace("\n", " | "))
        messagebox.showinfo("Hoàn thành", summary)


def parse_args():
    parser = argparse.ArgumentParser(description="52 XoaDe - Tag Remover")
    parser.add_argument(
        "--folder",
        type=Path,
        help="Đường dẫn folder cần xử lý. Nếu bỏ trống sẽ mở UI.",
    )
    parser.add_argument(
        "--unwanted-folder",
        type=Path,
        default=DEFAULT_UNWANTED_TAGS_FOLDER,
        help="Folder chứa các file .txt tag cần xóa.",
    )
    parser.add_argument(
        "--ui",
        action="store_true",
        help="Bắt buộc mở giao diện UI.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if args.ui or args.folder is None:
        app = XoaDeApp()
        app.mainloop()
        return

    processed_files, changed_files = run_once(args.folder, args.unwanted_folder)
    print(f"Đã xử lý: {processed_files} file .txt")
    print(f"Đã cập nhật: {changed_files} file")
    print(f"✅ Hoàn thành việc lọc tag trong: {args.folder}")


if __name__ == "__main__":
    main()
