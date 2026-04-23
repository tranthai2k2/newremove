#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tag Enhancer Multifolder Runner (UI)

- Nhập hoặc browse root folder
- Bấm + Add để thêm vào danh sách
- Duyệt subfolder cấp 1 và chạy tag_enhancer_v12.6_FINAL.py cho từng folder
"""

import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk


SKIP_DIR_NAMES = {"out_tags", "__pycache__", "_tag_enhancer_multifolder_logs"}
DEFAULT_BASE_SCRIPT = Path(__file__).with_name("tag_enhancer_v12.6_FINAL.py")


def list_target_folders(root: Path, include_root: bool) -> list[Path]:
    targets: list[Path] = []
    if include_root:
        targets.append(root)
    for item in sorted(root.iterdir()):
        if not item.is_dir():
            continue
        if item.name in SKIP_DIR_NAMES:
            continue
        targets.append(item)
    return targets


def run_one_folder(base_script: Path, folder: Path) -> subprocess.CompletedProcess:
    cmd = [sys.executable, str(base_script), "--folder", str(folder)]
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Tag Enhancer Multifolder")
        self.minsize(840, 620)
        self.resizable(True, True)

        self._roots: list[Path] = []
        self._running = False
        self._stop_flag = threading.Event()

        self.var_base_script = tk.StringVar(value=str(DEFAULT_BASE_SCRIPT))
        self.var_root_input = tk.StringVar()
        self.var_include_root = tk.BooleanVar(value=False)

        self._build_ui()

    def _build_ui(self):
        pad = dict(padx=10, pady=6)

        frm_base = ttk.LabelFrame(self, text="Base script")
        frm_base.pack(fill="x", **pad)
        ttk.Entry(frm_base, textvariable=self.var_base_script).pack(
            side="left", fill="x", expand=True, padx=6, pady=6
        )
        ttk.Button(frm_base, text="Browse", command=self._browse_base_script, width=10).pack(
            side="left", padx=(0, 6), pady=6
        )

        frm_roots = ttk.LabelFrame(self, text="Root folders")
        frm_roots.pack(fill="x", **pad)

        row_add = ttk.Frame(frm_roots)
        row_add.pack(fill="x", padx=6, pady=(6, 2))
        ent = ttk.Entry(row_add, textvariable=self.var_root_input)
        ent.pack(side="left", fill="x", expand=True, padx=(0, 4))
        ent.bind("<Return>", lambda _: self._add_from_entry())
        ttk.Button(row_add, text="Browse", command=self._browse_add_root).pack(side="left", padx=(0, 4))
        ttk.Button(row_add, text="+ Add", command=self._add_from_entry, width=10).pack(side="left")

        row_list = ttk.Frame(frm_roots)
        row_list.pack(fill="x", padx=6, pady=(2, 6))
        self.lst = tk.Listbox(
            row_list,
            height=8,
            selectmode="extended",
            activestyle="none",
            exportselection=False,
        )
        sb = ttk.Scrollbar(row_list, orient="vertical", command=self.lst.yview)
        self.lst.configure(yscrollcommand=sb.set)
        self.lst.pack(side="left", fill="x", expand=True)
        sb.pack(side="left", fill="y")

        btn_col = ttk.Frame(row_list)
        btn_col.pack(side="left", fill="y", padx=(6, 0))
        ttk.Button(btn_col, text="Remove", command=self._remove_selected, width=10).pack(pady=(0, 3))
        ttk.Button(btn_col, text="Clear all", command=self._clear_all_roots, width=10).pack()

        frm_opt = ttk.LabelFrame(self, text="Options")
        frm_opt.pack(fill="x", **pad)
        ttk.Checkbutton(frm_opt, text="Include root folder itself", variable=self.var_include_root).pack(
            side="left", padx=6, pady=6
        )

        frm_ctrl = ttk.Frame(self)
        frm_ctrl.pack(fill="x", **pad)
        self.btn_run = ttk.Button(frm_ctrl, text="Run", command=self._start, width=14)
        self.btn_run.pack(side="left")
        self.btn_stop = ttk.Button(frm_ctrl, text="Stop", command=self._stop, state="disabled", width=12)
        self.btn_stop.pack(side="left", padx=(6, 6))
        ttk.Button(frm_ctrl, text="Clear log", command=self._clear_log).pack(side="left")
        self.lbl_status = ttk.Label(frm_ctrl, text="")
        self.lbl_status.pack(side="right", padx=6)

        self.progress = ttk.Progressbar(self, mode="determinate")
        self.progress.pack(fill="x", padx=10, pady=(0, 4))

        frm_log = ttk.LabelFrame(self, text="Log")
        frm_log.pack(fill="both", expand=True, **pad)
        self.log = scrolledtext.ScrolledText(
            frm_log,
            wrap="word",
            state="disabled",
            font=("Consolas", 9),
            bg="#1e1e1e",
            fg="#d4d4d4",
        )
        self.log.pack(fill="both", expand=True, padx=6, pady=6)
        self.log.tag_config("ok", foreground="#4ec9b0")
        self.log.tag_config("err", foreground="#f44747")
        self.log.tag_config("warn", foreground="#ce9178")
        self.log.tag_config("info", foreground="#9cdcfe")
        self.log.tag_config("head", foreground="#dcdcaa")

    def _ui(self, fn, *args, **kwargs):
        self.after(0, lambda: fn(*args, **kwargs))

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

    def _browse_base_script(self):
        p = filedialog.askopenfilename(
            title="Chọn file base script",
            filetypes=[("Python files", "*.py"), ("All files", "*.*")],
        )
        if p:
            self.var_base_script.set(p)

    def _browse_add_root(self):
        p = filedialog.askdirectory(title="Chọn root folder")
        if p:
            self._add_root(Path(p))

    def _add_from_entry(self):
        txt = self.var_root_input.get().strip()
        if not txt:
            return
        self._add_root(Path(txt))
        self.var_root_input.set("")

    def _add_root(self, folder: Path):
        if not folder.exists():
            self._log(f"❌ Không tồn tại: {folder}\n", "err")
            return
        if not folder.is_dir():
            self._log(f"❌ Không phải folder: {folder}\n", "err")
            return
        if folder in self._roots:
            self._log(f"⚠️  Đã có: {folder}\n", "warn")
            return
        self._roots.append(folder)
        self.lst.insert("end", str(folder))
        self._log(f"+ Added: {folder}\n", "info")

    def _remove_selected(self):
        for i in reversed(self.lst.curselection()):
            self.lst.delete(i)
            self._roots.pop(i)

    def _clear_all_roots(self):
        self._roots.clear()
        self.lst.delete(0, "end")

    def _start(self):
        if self._running:
            return
        if not self._roots:
            messagebox.showwarning("Thiếu root", "Vui lòng nhập/browse và bấm + Add ít nhất 1 root folder.")
            return

        base_script = Path(self.var_base_script.get().strip())
        if not base_script.is_file():
            messagebox.showerror("Lỗi", f"Không tìm thấy base script:\n{base_script}")
            return

        roots = list(self._roots)
        include_root = self.var_include_root.get()

        self._stop_flag.clear()
        self._set_running(True)
        threading.Thread(
            target=self._run_all,
            args=(roots, base_script, include_root),
            daemon=True,
        ).start()

    def _stop(self):
        self._stop_flag.set()
        self._log("\n⏹  Đã yêu cầu dừng...\n", "warn")

    def _run_all(self, roots: list[Path], base_script: Path, include_root: bool):
        started = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        jobs: list[Path] = []
        skipped = 0

        for root in roots:
            if not root.exists() or not root.is_dir():
                skipped += 1
                self._ui(self._log, f"⚠️  Root không hợp lệ: {root}\n", "warn")
                continue
            targets = list_target_folders(root, include_root)
            if not targets:
                skipped += 1
                self._ui(self._log, f"⚠️  Root không có subfolder hợp lệ: {root}\n", "warn")
                continue
            for target in targets:
                jobs.append(target)

        total = len(jobs)
        self._ui(self.progress.configure, maximum=total, value=0)
        self._ui(self._log, f"\n{'=' * 80}\n", "head")
        self._ui(self._log, f" START: {started}\n", "head")
        self._ui(self._log, f" Base script: {base_script}\n", "head")
        self._ui(self._log, f" Jobs: {total}\n", "head")
        self._ui(self._log, f"{'=' * 80}\n", "head")

        ok = fail = 0

        for idx, target in enumerate(jobs, start=1):
            if self._stop_flag.is_set():
                break

            self._ui(self._log, f"\n[{idx}/{total}] ▶ {target}\n", "info")
            try:
                result = run_one_folder(base_script=base_script, folder=target)
                merged = (result.stdout or "") + (result.stderr or "")

                if result.returncode == 0:
                    ok += 1
                    self._ui(self._log, "   ✅ OK\n", "ok")
                else:
                    fail += 1
                    self._ui(self._log, f"   ❌ FAIL ({result.returncode})\n", "err")
                    detail = merged.strip()
                    if detail:
                        last_line = detail.splitlines()[-1]
                        self._ui(self._log, f"      ↳ {last_line}\n", "warn")
            except Exception as e:
                fail += 1
                self._ui(self._log, f"   ❌ Exception: {e}\n", "err")

            self._ui(self.progress.configure, value=idx)
            self._ui(self.lbl_status.configure, text=f"{idx}/{total} ✅{ok} ⚠️{skipped} ❌{fail}")

        stopped = " (stopped)" if self._stop_flag.is_set() else ""
        ended = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._ui(self._log, f"\n{'=' * 80}\n", "head")
        self._ui(self._log, f" END{stopped}: {ended}\n", "head")
        self._ui(self._log, f"   ✅ Success: {ok}\n", "ok")
        self._ui(self._log, f"   ⚠️  Skipped: {skipped}\n", "warn")
        self._ui(self._log, f"   ❌ Failed : {fail}\n", "err" if fail else "head")
        self._ui(self._log, f"{'=' * 80}\n\n", "head")
        self._ui(self.lbl_status.configure, text=f"Done{stopped} — ✅{ok} ⚠️{skipped} ❌{fail}")
        self._ui(self._set_running, False)


if __name__ == "__main__":
    app = App()
    app.mainloop()
