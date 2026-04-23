#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tag Enchancer AllTag - UI (multi root folder)
"""

import shutil
import threading
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext


def _unique_dest_path(dest_dir: Path, filename: str) -> Path:
    """Tạo path đích không đè file đã có."""
    dest = dest_dir / filename
    if not dest.exists():
        return dest

    stem = dest.stem
    suffix = dest.suffix
    idx = 2
    while True:
        candidate = dest_dir / f"{stem}_{idx}{suffix}"
        if not candidate.exists():
            return candidate
        idx += 1


def process_root(root_path: Path, output_dir: Path, log_fn, stop_flag: threading.Event):
    """Xử lý một root_path, trả về (copied, skipped, errors)."""
    if not root_path.exists():
        log_fn(f"❌ Không tồn tại: {root_path}\n", "err")
        return 0, 0, 1

    log_fn(f"📁 Output: {output_dir}\n", "info")

    subfolders = sorted([f for f in root_path.iterdir() if f.is_dir()])

    copied = skipped = errors = 0

    for subfolder in subfolders:
        if stop_flag.is_set():
            break
        addfaceless_file = subfolder / "out_tags" / "addfaceless.txt"
        if not (subfolder / "out_tags").is_dir():
            log_fn(f"⏭️  {subfolder.name}: Không có folder out_tags\n", "warn")
            skipped += 1
            continue
        if not addfaceless_file.exists():
            log_fn(f"⚠️  {subfolder.name}: Không có addfaceless.txt\n", "warn")
            skipped += 1
            continue
        try:
            # Khi xuất chung nhiều root, thêm prefix root để tránh trùng tên.
            is_shared_output = output_dir.resolve() != root_path.resolve()
            if is_shared_output:
                filename = f"{root_path.name}__{subfolder.name}_addfaceless.txt"
            else:
                filename = f"{subfolder.name}_addfaceless.txt"

            dest = _unique_dest_path(output_dir, filename)
            shutil.copy2(addfaceless_file, dest)
            log_fn(f"✅ {dest.name}\n", "ok")
            copied += 1
        except Exception as e:
            log_fn(f"❌ Lỗi {subfolder.name}: {e}\n", "err")
            errors += 1

    return copied, skipped, errors


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AllTag Collector — multi root folder")
        self.minsize(680, 520)
        self.resizable(True, True)
        self._roots: list[Path] = []
        self._running = False
        self._stop_flag = threading.Event()
        self.var_output_folder = tk.StringVar()
        self._build_ui()

    # ── UI ──────────────────────────────────────────────────────────
    def _build_ui(self):
        pad = dict(padx=10, pady=5)

        # ── Root folders ──
        frm1 = ttk.LabelFrame(self, text="Root folders (cấp 1)")
        frm1.pack(fill="x", **pad)

        inp = ttk.Frame(frm1)
        inp.pack(fill="x", padx=6, pady=(4, 2))
        self.var_folder = tk.StringVar()
        ent = ttk.Entry(inp, textvariable=self.var_folder)
        ent.pack(side="left", fill="x", expand=True, padx=(0, 4))
        ent.bind("<Return>", lambda _: self._add_from_entry())
        ttk.Button(inp, text="Browse", command=self._browse_add).pack(side="left", padx=(0, 4))
        ttk.Button(inp, text="Add",    command=self._add_from_entry).pack(side="left")

        lst_frm = ttk.Frame(frm1)
        lst_frm.pack(fill="x", padx=6, pady=(2, 4))
        self.lst = tk.Listbox(lst_frm, height=5, selectmode="extended",
                              activestyle="none", exportselection=False)
        sb = ttk.Scrollbar(lst_frm, orient="vertical", command=self.lst.yview)
        self.lst.configure(yscrollcommand=sb.set)
        self.lst.pack(side="left", fill="x", expand=True)
        sb.pack(side="left", fill="y")

        btn_col = ttk.Frame(lst_frm)
        btn_col.pack(side="left", fill="y", padx=(6, 0))
        ttk.Button(btn_col, text="Remove",    command=self._remove_sel, width=10).pack(pady=(0, 3))
        ttk.Button(btn_col, text="Clear all", command=self._clear_all,  width=10).pack()

        # ── Output folder ──
        frm2 = ttk.LabelFrame(self, text="Output folder (chung, tùy chọn)")
        frm2.pack(fill="x", **pad)
        out_inp = ttk.Frame(frm2)
        out_inp.pack(fill="x", padx=6, pady=4)
        ttk.Entry(out_inp, textvariable=self.var_output_folder).pack(
            side="left", fill="x", expand=True, padx=(0, 4)
        )
        ttk.Button(out_inp, text="Browse", command=self._browse_output).pack(side="left", padx=(0, 4))
        ttk.Button(out_inp, text="Use root", command=lambda: self.var_output_folder.set("")).pack(side="left")

        # ── Controls ──
        frm3 = ttk.Frame(self)
        frm3.pack(fill="x", **pad)
        self.btn_run  = ttk.Button(frm3, text="▶  Run", command=self._start, width=14)
        self.btn_run.pack(side="left")
        self.btn_stop = ttk.Button(frm3, text="⏹  Stop", command=self._stop, width=12, state="disabled")
        self.btn_stop.pack(side="left", padx=6)
        ttk.Button(frm3, text="Clear log", command=self._clear_log).pack(side="left")
        self.lbl_status = ttk.Label(frm3, text="")
        self.lbl_status.pack(side="right", padx=6)

        # ── Progress ──
        self.progress = ttk.Progressbar(self, mode="determinate")
        self.progress.pack(fill="x", padx=10, pady=(0, 4))

        # ── Log ──
        frm4 = ttk.LabelFrame(self, text="Log")
        frm4.pack(fill="both", expand=True, **pad)
        self.log = scrolledtext.ScrolledText(frm4, wrap="word", state="disabled",
                                             font=("Consolas", 9),
                                             bg="#1e1e1e", fg="#d4d4d4")
        self.log.pack(fill="both", expand=True, padx=6, pady=4)
        self.log.tag_config("ok",   foreground="#4ec9b0")
        self.log.tag_config("err",  foreground="#f44747")
        self.log.tag_config("info", foreground="#9cdcfe")
        self.log.tag_config("warn", foreground="#ce9178")
        self.log.tag_config("head", foreground="#dcdcaa")

    # ── Folder management ────────────────────────────────────────────
    def _browse_add(self):
        p = filedialog.askdirectory(title="Chọn root folder")
        if p:
            self._add_folder(Path(p))

    def _browse_output(self):
        p = filedialog.askdirectory(title="Chọn output folder")
        if p:
            self.var_output_folder.set(p)

    def _add_from_entry(self):
        txt = self.var_folder.get().strip()
        if txt:
            self._add_folder(Path(txt))
            self.var_folder.set("")

    def _add_folder(self, folder: Path):
        if not folder.exists():
            self._log(f"❌ Không tồn tại: {folder}\n", "err")
            return
        if folder in self._roots:
            self._log(f"⚠️  Đã có: {folder}\n", "warn")
            return
        self._roots.append(folder)
        self.lst.insert("end", str(folder))
        self._log(f"+ Thêm: {folder}\n", "info")

    def _remove_sel(self):
        for i in reversed(self.lst.curselection()):
            self.lst.delete(i)
            self._roots.pop(i)

    def _clear_all(self):
        self._roots.clear()
        self.lst.delete(0, "end")

    # ── Log helpers ──────────────────────────────────────────────────
    def _log(self, msg: str, tag: str = ""):
        self.log.configure(state="normal")
        self.log.insert("end", msg, tag or ())
        self.log.see("end")
        self.log.configure(state="disabled")

    def _clear_log(self):
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    def _set_running(self, running: bool):
        self._running = running
        self.btn_run.configure(state="disabled" if running else "normal")
        self.btn_stop.configure(state="normal" if running else "disabled")

    # ── Run logic ────────────────────────────────────────────────────
    def _start(self):
        if not self._roots:
            self._log("⚠️  Chưa thêm root folder nào.\n", "warn")
            return

        output_txt = self.var_output_folder.get().strip()
        if output_txt:
            output_dir = Path(output_txt)
        else:
            output_dir = None

        if output_dir is not None:
            try:
                output_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                self._log(f"❌ Không tạo được output folder: {output_dir}\n   {e}\n", "err")
                return

        self._stop_flag.clear()
        self._set_running(True)
        threading.Thread(target=self._run_all, args=(output_dir,), daemon=True).start()

    def _stop(self):
        self._stop_flag.set()
        self._log("\n⏹  Yêu cầu dừng...\n", "warn")

    def _run_all(self, output_dir: Path | None):
        roots = list(self._roots)
        total_roots = len(roots)
        self.progress["maximum"] = total_roots
        self.progress["value"] = 0

        total_copied = total_skipped = total_errors = 0

        self._log(f"\n{'='*56}\n", "head")
        self._log(f" START — {datetime.now():%Y-%m-%d %H:%M:%S}\n", "head")
        self._log(f" {total_roots} root folder(s)\n", "head")
        if output_dir is None:
            self._log(" Output mode: từng root (mặc định)\n", "head")
        else:
            self._log(f" Output chung: {output_dir}\n", "head")
        self._log(f"{'='*56}\n", "head")

        for idx, root in enumerate(roots, 1):
            if self._stop_flag.is_set():
                break
            self._log(f"\n[{idx}/{total_roots}] {root}\n", "info")
            target_output = output_dir if output_dir is not None else root
            copied, skipped, errors = process_root(root, target_output, self._log, self._stop_flag)
            total_copied  += copied
            total_skipped += skipped
            total_errors  += errors
            self._log(f"   → copied={copied}  skipped={skipped}  errors={errors}\n", "info")
            self.progress["value"] = idx
            self.lbl_status.configure(
                text=f"{idx}/{total_roots}  ✅{total_copied} ⏭️{total_skipped} ❌{total_errors}"
            )

        stopped = " (đã dừng)" if self._stop_flag.is_set() else ""
        self._log(f"\n{'='*56}\n", "head")
        self._log(f" KẾT QUẢ{stopped}:\n", "head")
        self._log(f"   ✅ Copied : {total_copied}\n",  "ok")
        self._log(f"   ⏭️  Skipped: {total_skipped}\n", "warn")
        self._log(f"   ❌ Errors : {total_errors}\n",   "err" if total_errors else "head")
        self._log(f" End: {datetime.now():%Y-%m-%d %H:%M:%S}\n", "head")
        self._log(f"{'='*56}\n\n", "head")

        self.lbl_status.configure(
            text=f"Done{stopped} — ✅{total_copied} ⏭️{total_skipped} ❌{total_errors}"
        )
        self._set_running(False)


if __name__ == "__main__":
    app = App()
    app.mainloop()
