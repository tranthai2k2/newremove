#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Thu thập tất cả tag từ các file all_tag.txt trong các folder out_tags
Cấu trúc: folder_cap1 / folder_cap2 / out_tags / all_tag.txt
Tổng hợp tất cả tag unique vào 1 file all_tag.txt riêng
"""

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from pathlib import Path


def collect_tags_from_cap1(cap1_folder: Path):
    all_tags = set()
    found_files = []

    for cap2 in cap1_folder.iterdir():
        if not cap2.is_dir():
            continue
        out_tags_dir = cap2 / "out_tags"
        if not out_tags_dir.is_dir():
            continue
        tag_file = out_tags_dir / "all_tag.txt"
        if tag_file.is_file():
            found_files.append(tag_file)
            with open(tag_file, "r", encoding="utf-8") as f:
                for line in f:
                    tag = line.strip()
                    if tag:
                        all_tags.add(tag)

    return all_tags, found_files


def process(cap1_folders: list, log_func):
    all_tags = set()
    total_files = []

    for cap1 in cap1_folders:
        p = Path(cap1)
        if not p.is_dir():
            log_func(f"[SKIP] Không tìm thấy: {cap1}\n")
            continue
        log_func(f"[SCAN] {p.name}\n")
        tags, files = collect_tags_from_cap1(p)
        log_func(f"       {len(files)} file, {len(tags)} tag riêng\n")
        all_tags.update(tags)
        total_files.extend(files)

    if not all_tags:
        log_func("\nKhông tìm thấy tag nào.\n")
        return None

    parent_dir = Path(cap1_folders[0]).parent
    output_dir = parent_dir / "_all_tags_combined"
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / "all_tag.txt"

    sorted_tags = sorted(all_tags)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(sorted_tags))

    log_func(f"\n{'='*45}\n")
    log_func(f"Tổng file quét  : {len(total_files)}\n")
    log_func(f"Tổng tag unique : {len(sorted_tags)}\n")
    log_func(f"Output          : {output_file}\n")
    return output_file


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("All Tag Collector")
        self.resizable(True, True)
        self.folders = []
        self._build_ui()

    def _build_ui(self):
        # --- Folder list frame ---
        top = tk.Frame(self, padx=8, pady=6)
        top.pack(fill="x")

        tk.Label(top, text="Các folder cấp 1:", anchor="w").pack(fill="x")

        list_frame = tk.Frame(self)
        list_frame.pack(fill="both", expand=False, padx=8)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")

        self.listbox = tk.Listbox(list_frame, height=8, yscrollcommand=scrollbar.set,
                                   selectmode=tk.EXTENDED)
        self.listbox.pack(fill="both", expand=True)
        scrollbar.config(command=self.listbox.yview)

        # --- Buttons ---
        btn_frame = tk.Frame(self, padx=8, pady=4)
        btn_frame.pack(fill="x")

        tk.Button(btn_frame, text="+ Thêm folder", width=14, command=self.add_folder).pack(side="left", padx=2)
        tk.Button(btn_frame, text="- Xóa chọn", width=12, command=self.remove_selected).pack(side="left", padx=2)
        tk.Button(btn_frame, text="Xóa tất cả", width=12, command=self.clear_all).pack(side="left", padx=2)

        tk.Button(btn_frame, text="▶  CHẠY", width=14, bg="#2d7d46", fg="white",
                  font=("", 10, "bold"), command=self.run).pack(side="right", padx=2)

        # --- Log ---
        tk.Label(self, text="Log:", anchor="w", padx=8).pack(fill="x")
        self.log = scrolledtext.ScrolledText(self, height=12, state="disabled",
                                              bg="#1e1e1e", fg="#d4d4d4",
                                              font=("Consolas", 9))
        self.log.pack(fill="both", expand=True, padx=8, pady=(0, 8))

    def add_folder(self):
        folder = filedialog.askdirectory(title="Chọn folder cấp 1")
        if folder and folder not in self.folders:
            self.folders.append(folder)
            self.listbox.insert(tk.END, folder)

    def remove_selected(self):
        for i in reversed(self.listbox.curselection()):
            self.folders.pop(i)
            self.listbox.delete(i)

    def clear_all(self):
        self.folders.clear()
        self.listbox.delete(0, tk.END)

    def log_write(self, text):
        self.log.config(state="normal")
        self.log.insert(tk.END, text)
        self.log.see(tk.END)
        self.log.config(state="disabled")
        self.update_idletasks()

    def run(self):
        if not self.folders:
            messagebox.showwarning("Thiếu folder", "Vui lòng thêm ít nhất 1 folder cấp 1.")
            return
        self.log.config(state="normal")
        self.log.delete("1.0", tk.END)
        self.log.config(state="disabled")

        result = process(self.folders, self.log_write)
        if result:
            if messagebox.askyesno("Hoàn thành", f"Đã xong!\n\nMở thư mục output?"):
                import subprocess
                subprocess.Popen(f'explorer "{result.parent}"')


if __name__ == "__main__":
    app = App()
    app.mainloop()
