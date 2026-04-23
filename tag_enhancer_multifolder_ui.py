#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tag Enhancer Multifolder UI Runner

- Chọn nhiều root folder
- Duyệt subfolder cấp 1 để chạy tag_enhancer_v12.6_FINAL.py
- Không tạo thư mục log riêng
- (Tùy chọn) gom out_tags/addfaceless.txt của từng folder về 1 thư mục output
"""

import subprocess
import shutil
import sys
import threading
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from datetime import datetime
from os import cpu_count
from pathlib import Path
from typing import Optional
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk


SKIP_DIR_NAMES = {"out_tags", "__pycache__", "_tag_enhancer_multifolder_logs"}
MAX_WORKERS = 16


def run_one_folder(base_script: Path, folder: Path):
    cmd = [sys.executable, str(base_script), "--folder", str(folder)]
    started = datetime.now()
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    elapsed = (datetime.now() - started).total_seconds()
    return result.returncode, elapsed, result.stdout or ""


def unique_dest_path(dest_dir: Path, filename: str) -> Path:
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


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Tag Enhancer Multifolder Runner")
        self.minsize(820, 620)
        self.resizable(True, True)

        self._roots = []
        self._running = False
        self._stop_flag = threading.Event()

        default_base = Path(__file__).with_name("tag_enhancer_v12.6_FINAL.py")
        self.var_base_script = tk.StringVar(value=str(default_base))
        self.var_root_input = tk.StringVar()
        self.var_include_root = tk.BooleanVar(value=False)
        self.var_addfaceless_output = tk.StringVar()
        default_workers = max(1, min(4, cpu_count() or 4))
        self.var_workers = tk.IntVar(value=default_workers)

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
        ttk.Button(row_add, text="Add", command=self._add_from_entry, width=8).pack(side="left")

        row_list = ttk.Frame(frm_roots)
        row_list.pack(fill="x", padx=6, pady=(2, 6))
        self.lst = tk.Listbox(
            row_list,
            height=7,
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

        frm_opts = ttk.LabelFrame(self, text="Options")
        frm_opts.pack(fill="x", **pad)
        ttk.Checkbutton(frm_opts, text="Include root folder itself", variable=self.var_include_root).pack(
            side="left", padx=6, pady=6
        )
        ttk.Label(frm_opts, text="Parallel jobs:").pack(side="left", padx=(16, 4), pady=6)
        ttk.Spinbox(
            frm_opts,
            from_=1,
            to=MAX_WORKERS,
            width=5,
            textvariable=self.var_workers,
            justify="center",
        ).pack(side="left", pady=6)

        frm_output = ttk.LabelFrame(self, text="Export addfaceless (tùy chọn)")
        frm_output.pack(fill="x", **pad)
        row_output = ttk.Frame(frm_output)
        row_output.pack(fill="x", padx=6, pady=6)
        ttk.Entry(row_output, textvariable=self.var_addfaceless_output).pack(
            side="left", fill="x", expand=True, padx=(0, 4)
        )
        ttk.Button(row_output, text="Browse", command=self._browse_addfaceless_output, width=10).pack(
            side="left", padx=(0, 4)
        )
        ttk.Button(row_output, text="Clear", command=lambda: self.var_addfaceless_output.set(""), width=8).pack(
            side="left"
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

    def _browse_addfaceless_output(self):
        p = filedialog.askdirectory(title="Chọn thư mục xuất addfaceless")
        if p:
            self.var_addfaceless_output.set(p)

    def _add_from_entry(self):
        txt = self.var_root_input.get().strip()
        if not txt:
            return
        paths = []
        for line in txt.splitlines():
            candidate = line.strip().strip('"').strip("'")
            if candidate:
                paths.append(candidate)
        if not paths:
            paths = [txt.strip().strip('"').strip("'")]
        for p in paths:
            self._add_root(Path(p))
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
        self._log(f"+ Root: {folder}\n", "info")

    def _remove_selected(self):
        for i in reversed(self.lst.curselection()):
            self.lst.delete(i)
            self._roots.pop(i)

    def _clear_all_roots(self):
        self._roots.clear()
        self.lst.delete(0, "end")

    def _collect_targets(self, root: Path, include_root: bool):
        targets = []
        if include_root:
            targets.append(root)
        for item in sorted(root.iterdir()):
            if not item.is_dir():
                continue
            if item.name in SKIP_DIR_NAMES:
                continue
            targets.append(item)
        return targets

    def _start(self):
        if self._running:
            return
        if not self._roots:
            messagebox.showwarning("Thiếu root", "Vui lòng thêm ít nhất 1 root folder.")
            return

        base_script = Path(self.var_base_script.get().strip().strip('"').strip("'"))
        if not base_script.is_file():
            messagebox.showerror("Lỗi", f"Không tìm thấy base script:\n{base_script}")
            return

        roots = list(self._roots)
        include_root = self.var_include_root.get()
        workers = self.var_workers.get()
        if workers < 1 or workers > MAX_WORKERS:
            messagebox.showerror("Lỗi", f"Parallel jobs phải trong khoảng 1..{MAX_WORKERS}")
            return

        output_txt = self.var_addfaceless_output.get().strip().strip('"').strip("'")
        output_dir = None
        if output_txt:
            output_dir = Path(output_txt)
            try:
                output_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                messagebox.showerror(
                    "Lỗi",
                    f"Không tạo được thư mục xuất addfaceless:\n{output_dir}\n\n{e}",
                )
                return

        self._stop_flag.clear()
        self._set_running(True)
        threading.Thread(
            target=self._run_all,
            args=(roots, base_script, include_root, workers, output_dir),
            daemon=True,
        ).start()

    def _stop(self):
        self._stop_flag.set()
        self._log("\n⏹  Đã yêu cầu dừng (không nhận job mới, chờ job đang chạy kết thúc)...\n", "warn")

    def _run_all(self, roots, base_script: Path, include_root: bool, workers: int, output_dir: Optional[Path]):
        started = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        jobs = []
        skipped = 0

        for root in roots:
            if not root.exists() or not root.is_dir():
                skipped += 1
                self._ui(self._log, f"⚠️  Bỏ qua root không hợp lệ: {root}\n", "warn")
                continue

            targets = self._collect_targets(root, include_root)
            if not targets:
                skipped += 1
                self._ui(self._log, f"⚠️  Root không có target: {root}\n", "warn")
                continue

            for t in targets:
                jobs.append(t)

        total = len(jobs)
        self._ui(self.progress.configure, maximum=total, value=0)
        self._ui(self._log, f"\n{'=' * 80}\n", "head")
        self._ui(self._log, f" START: {started}\n", "head")
        self._ui(self._log, f" Base script: {base_script}\n", "head")
        self._ui(self._log, f" Jobs: {total}\n", "head")
        self._ui(self._log, f" Parallel jobs: {workers}\n", "head")
        if output_dir is None:
            self._ui(self._log, " Export addfaceless: tắt\n", "head")
        else:
            self._ui(self._log, f" Export addfaceless: {output_dir}\n", "head")
        self._ui(self._log, f"{'=' * 80}\n", "head")

        if total == 0:
            ended = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self._ui(self._log, f" END: {ended}\n", "head")
            self._ui(self._log, "   ⚠️  Không có job để chạy.\n", "warn")
            self._ui(self.lbl_status.configure, text=f"Done — ✅0 ⚠️{skipped} ❌0")
            self._ui(self._set_running, False)
            return

        ok = fail = 0
        copied_addfaceless = missing_addfaceless = addfaceless_errors = 0
        completed = 0
        next_job = 0
        in_flight = {}

        with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="tag-enhancer") as ex:
            while next_job < total and len(in_flight) < workers:
                idx = next_job + 1
                target = jobs[next_job]
                self._ui(self._log, f"\n[{idx}/{total}] ▶ {target}\n", "info")
                fut = ex.submit(run_one_folder, base_script, target)
                in_flight[fut] = (idx, target)
                next_job += 1

            while in_flight:
                done, _ = wait(tuple(in_flight.keys()), timeout=0.2, return_when=FIRST_COMPLETED)
                if not done:
                    continue

                for fut in done:
                    idx, target = in_flight.pop(fut)
                    completed += 1
                    try:
                        returncode, elapsed, output = fut.result()
                        if returncode == 0:
                            ok += 1
                            self._ui(
                                self._log,
                                f"   ✅ OK ({elapsed:.1f}s)\n",
                                "ok",
                            )
                        else:
                            fail += 1
                            self._ui(
                                self._log,
                                f"   ❌ FAIL ({returncode}) ({elapsed:.1f}s)\n",
                                "err",
                            )
                            last_line = ""
                            for line in reversed(output.splitlines()):
                                line = line.strip()
                                if line:
                                    last_line = line
                                    break
                            if last_line:
                                self._ui(self._log, f"      ↳ {last_line}\n", "warn")
                    except Exception as e:
                        fail += 1
                        self._ui(self._log, f"   ❌ Exception: {e}\n", "err")
                        output = ""

                    if output_dir is not None:
                        src_addfaceless = target / "out_tags" / "addfaceless.txt"
                        if src_addfaceless.is_file():
                            try:
                                dest_name = f"{target.name}_addfaceless.txt"
                                dest_file = unique_dest_path(output_dir, dest_name)
                                shutil.copy2(src_addfaceless, dest_file)
                                copied_addfaceless += 1
                                self._ui(self._log, f"   📄 addfaceless -> {dest_file}\n", "info")
                            except Exception as e:
                                addfaceless_errors += 1
                                self._ui(self._log, f"   ❌ Export addfaceless lỗi: {e}\n", "err")
                        else:
                            missing_addfaceless += 1
                            self._ui(
                                self._log,
                                f"   ⚠️  Không có addfaceless.txt: {src_addfaceless}\n",
                                "warn",
                            )

                    self._ui(self.progress.configure, value=completed)
                    self._ui(
                        self.lbl_status.configure,
                        text=f"{completed}/{total} ✅{ok} ⚠️{skipped} ❌{fail} 📄{copied_addfaceless}",
                    )

                while (
                    not self._stop_flag.is_set()
                    and next_job < total
                    and len(in_flight) < workers
                ):
                    idx = next_job + 1
                    target = jobs[next_job]
                    self._ui(self._log, f"\n[{idx}/{total}] ▶ {target}\n", "info")
                    fut = ex.submit(run_one_folder, base_script, target)
                    in_flight[fut] = (idx, target)
                    next_job += 1

                if self._stop_flag.is_set() and next_job < total:
                    skipped_due_to_stop = total - next_job
                    skipped += skipped_due_to_stop
                    self._ui(
                        self._log,
                        f"⚠️  Dừng sớm, bỏ qua {skipped_due_to_stop} job chưa chạy.\n",
                        "warn",
                    )
                    next_job = total

        stopped = " (stopped)" if self._stop_flag.is_set() else ""
        ended = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._ui(self._log, f"\n{'=' * 80}\n", "head")
        self._ui(self._log, f" END{stopped}: {ended}\n", "head")
        self._ui(self._log, f"   ✅ Success: {ok}\n", "ok")
        self._ui(self._log, f"   ⚠️  Skipped: {skipped}\n", "warn")
        self._ui(self._log, f"   ❌ Failed : {fail}\n", "err" if fail else "head")
        if output_dir is not None:
            self._ui(self._log, f"   📄 Addfaceless copied : {copied_addfaceless}\n", "info")
            self._ui(self._log, f"   ⚠️  Addfaceless missing: {missing_addfaceless}\n", "warn")
            self._ui(
                self._log,
                f"   ❌ Addfaceless errors : {addfaceless_errors}\n",
                "err" if addfaceless_errors else "head",
            )
        self._ui(self._log, f"{'=' * 80}\n\n", "head")
        self._ui(
            self.lbl_status.configure,
            text=f"Done{stopped} — ✅{ok} ⚠️{skipped} ❌{fail} 📄{copied_addfaceless}",
        )
        self._ui(self._set_running, False)


if __name__ == "__main__":
    app = App()
    app.mainloop()
