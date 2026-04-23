from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import os
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText
import uuid

from PIL import Image

try:
    import pillow_avif  # noqa: F401
except ImportError:
    pass


CONVERT_EXTS = {".jpg", ".jpeg", ".webp", ".avif", ".bmp", ".tif", ".tiff", ".gif", ".jfif"}
SUPPORTED_EXTS = CONVERT_EXTS | {".png"}
PNG_SAVE_OPTIONS = {"format": "PNG", "compress_level": 1}
DEFAULT_WORKERS = min(64, max(4, (os.cpu_count() or 4) * 2))
PROGRESS_EVERY = 200


def collect_files(root: Path) -> list[Path]:
    return [
        file_path
        for file_path in root.rglob("*")
        if file_path.is_file()
        and file_path.suffix != ".png"
        and file_path.suffix.lower() in SUPPORTED_EXTS
    ]


def rename_png_extension_lowercase(file_path: Path) -> Path:
    target = file_path.with_suffix(".png")
    if file_path.suffix == ".png":
        return file_path

    temp_path = file_path.with_name(f"{file_path.stem}.__tmp_case__{uuid.uuid4().hex}{file_path.suffix}")
    file_path.rename(temp_path)
    temp_path.rename(target)
    return target


def process_file(index: int, total: int, file_path: Path) -> tuple[str, str]:
    try:
        if not file_path.exists():
            return "skipped", f"[{index}/{total}] SKIP: {file_path} (missing)"

        ext_lower = file_path.suffix.lower()
        png_path = file_path.with_suffix(".png")
        same_target = str(file_path).lower() == str(png_path).lower()

        if png_path.exists() and not same_target:
            return "error", f"[{index}/{total}] ERROR: target exists -> {png_path}"

        if ext_lower == ".png":
            renamed_path = rename_png_extension_lowercase(file_path)
            return "renamed", f"[{index}/{total}] RENAME: {file_path.name} -> {renamed_path.name}"

        with Image.open(file_path) as img:
            final_img = img if img.mode == "RGBA" else img.convert("RGBA")
            final_img.save(png_path, **PNG_SAVE_OPTIONS)
            if final_img is not img:
                final_img.close()

        file_path.unlink()
        return "converted", f"[{index}/{total}] OK: {file_path.name} -> {png_path.name}"
    except Exception as exc:
        return "error", f"[{index}/{total}] ERROR: {file_path} - {exc}"


def run_conversion(
    root: Path,
    workers: int,
    verbose: bool,
    event_queue: queue.Queue[tuple[str, object]],
) -> None:
    all_files = collect_files(root)
    total = len(all_files)

    if total == 0:
        event_queue.put(("log", "No supported image files found."))
        event_queue.put(
            (
                "done",
                {"processed": 0, "converted": 0, "renamed": 0, "skipped": 0, "errors": 0, "total": 0},
            )
        )
        return

    event_queue.put(("log", f"Root folder: {root}"))
    event_queue.put(("log", f"Found {total} file(s). Converting with {workers} workers..."))
    event_queue.put(("progress", {"processed": 0, "total": total, "converted": 0, "renamed": 0, "errors": 0}))

    converted = 0
    renamed = 0
    skipped = 0
    errors = 0
    processed = 0

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(process_file, i, total, file_path): file_path
            for i, file_path in enumerate(all_files, 1)
        }

        for future in as_completed(futures):
            status, message = future.result()
            processed += 1

            if status == "converted":
                converted += 1
            elif status == "renamed":
                renamed += 1
            elif status == "skipped":
                skipped += 1
            else:
                errors += 1
                event_queue.put(("log", message))

            if verbose and status != "error":
                event_queue.put(("log", message))

            if processed % PROGRESS_EVERY == 0 or processed == total:
                event_queue.put(
                    (
                        "progress",
                        {
                            "processed": processed,
                            "total": total,
                            "converted": converted,
                            "renamed": renamed,
                            "errors": errors,
                        },
                    )
                )

    event_queue.put(
        (
            "done",
            {
                "processed": processed,
                "converted": converted,
                "renamed": renamed,
                "skipped": skipped,
                "errors": errors,
                "total": total,
            },
        )
    )


class ConverterApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Multi Folder to PNG")
        self.root.geometry("860x620")

        self.event_queue: queue.Queue[tuple[str, object]] = queue.Queue()
        self.running = False

        self.folder_var = tk.StringVar()
        self.workers_var = tk.IntVar(value=DEFAULT_WORKERS)
        self.verbose_var = tk.BooleanVar(value=False)
        self.progress_var = tk.StringVar(value="Ready")

        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_ui(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(4, weight=1)

        frm_path = ttk.Frame(self.root, padding=(12, 12, 12, 6))
        frm_path.grid(row=0, column=0, sticky="ew")
        frm_path.columnconfigure(1, weight=1)

        ttk.Label(frm_path, text="Folder").grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.entry_folder = ttk.Entry(frm_path, textvariable=self.folder_var)
        self.entry_folder.grid(row=0, column=1, sticky="ew")
        self.entry_folder.bind("<Return>", self._on_enter_start)
        self.btn_browse = ttk.Button(frm_path, text="Browse", command=self.browse_folder)
        self.btn_browse.grid(row=0, column=2, padx=(8, 0))

        frm_opts = ttk.Frame(self.root, padding=(12, 0, 12, 6))
        frm_opts.grid(row=1, column=0, sticky="ew")

        ttk.Label(frm_opts, text="Workers").grid(row=0, column=0, sticky="w")
        self.spin_workers = ttk.Spinbox(frm_opts, from_=1, to=256, textvariable=self.workers_var, width=8)
        self.spin_workers.grid(row=0, column=1, padx=(8, 12), sticky="w")
        self.chk_verbose = ttk.Checkbutton(frm_opts, text="Verbose log", variable=self.verbose_var)
        self.chk_verbose.grid(row=0, column=2, sticky="w")

        frm_actions = ttk.Frame(self.root, padding=(12, 0, 12, 6))
        frm_actions.grid(row=2, column=0, sticky="ew")

        self.btn_start = ttk.Button(frm_actions, text="Start Convert", command=self.start_convert)
        self.btn_start.grid(row=0, column=0, sticky="w")
        self.btn_start.bind("<Return>", self._on_enter_start)

        frm_progress = ttk.Frame(self.root, padding=(12, 0, 12, 6))
        frm_progress.grid(row=3, column=0, sticky="ew")
        frm_progress.columnconfigure(0, weight=1)

        self.progress_bar = ttk.Progressbar(frm_progress, orient="horizontal", mode="determinate")
        self.progress_bar.grid(row=0, column=0, sticky="ew")
        ttk.Label(frm_progress, textvariable=self.progress_var).grid(row=1, column=0, sticky="w", pady=(4, 0))

        frm_log = ttk.Frame(self.root, padding=(12, 0, 12, 12))
        frm_log.grid(row=4, column=0, sticky="nsew")
        frm_log.columnconfigure(0, weight=1)
        frm_log.rowconfigure(0, weight=1)

        self.log_text = ScrolledText(frm_log, wrap="word", height=20)
        self.log_text.grid(row=0, column=0, sticky="nsew")
        self.log_text.configure(state="disabled")

    def browse_folder(self) -> None:
        folder = filedialog.askdirectory()
        if folder:
            self.folder_var.set(folder)

    def _on_enter_start(self, _event: object | None = None) -> None:
        if not self.running:
            self.start_convert()

    def start_convert(self) -> None:
        if self.running:
            return

        folder_text = self.folder_var.get().strip().strip('"').strip("'")
        if not folder_text:
            messagebox.showerror("Missing folder", "Please choose a root folder.")
            return

        root_path = Path(folder_text)
        if not root_path.exists() or not root_path.is_dir():
            messagebox.showerror("Invalid folder", f"Folder not found or not a directory:\n{root_path}")
            return

        workers = self.workers_var.get()
        if workers < 1:
            messagebox.showerror("Invalid workers", "Workers must be >= 1.")
            return

        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")
        self.progress_bar["value"] = 0
        self.progress_bar["maximum"] = 1
        self.progress_var.set("Starting...")

        self.set_running(True)
        threading.Thread(
            target=self._worker_thread,
            args=(root_path, workers, self.verbose_var.get()),
            daemon=True,
        ).start()
        self.root.after(100, self.poll_events)

    def _worker_thread(self, root_path: Path, workers: int, verbose: bool) -> None:
        try:
            run_conversion(root_path, workers, verbose, self.event_queue)
        except Exception as exc:
            self.event_queue.put(("log", f"Fatal error: {exc}"))
            self.event_queue.put(
                (
                    "done",
                    {"processed": 0, "converted": 0, "renamed": 0, "skipped": 0, "errors": 1, "total": 0},
                )
            )

    def poll_events(self) -> None:
        while True:
            try:
                event, payload = self.event_queue.get_nowait()
            except queue.Empty:
                break

            if event == "log":
                self.append_log(str(payload))
            elif event == "progress":
                data = payload
                if isinstance(data, dict):
                    processed = int(data.get("processed", 0))
                    total = max(1, int(data.get("total", 1)))
                    converted = int(data.get("converted", 0))
                    renamed = int(data.get("renamed", 0))
                    errors = int(data.get("errors", 0))
                    self.progress_bar["maximum"] = total
                    self.progress_bar["value"] = processed
                    self.progress_var.set(
                        f"Progress: {processed}/{total} "
                        f"(converted={converted}, renamed={renamed}, errors={errors})"
                    )
            elif event == "done":
                data = payload if isinstance(payload, dict) else {}
                converted = int(data.get("converted", 0))
                renamed = int(data.get("renamed", 0))
                skipped = int(data.get("skipped", 0))
                errors = int(data.get("errors", 0))
                total = int(data.get("total", 0))
                self.append_log("=" * 50)
                self.append_log(f"Total:     {total}")
                self.append_log(f"Converted: {converted}")
                self.append_log(f"Renamed:   {renamed}")
                self.append_log(f"Skipped:   {skipped}")
                self.append_log(f"Errors:    {errors}")
                self.append_log("Done.")
                self.progress_var.set(
                    f"Done - total={total}, converted={converted}, renamed={renamed}, skipped={skipped}, errors={errors}"
                )
                self.set_running(False)

        if self.running:
            self.root.after(100, self.poll_events)

    def append_log(self, message: str) -> None:
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"{message}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def set_running(self, running: bool) -> None:
        self.running = running
        state = "disabled" if running else "normal"
        self.entry_folder.configure(state=state)
        self.btn_browse.configure(state=state)
        self.spin_workers.configure(state=state)
        self.chk_verbose.configure(state=state)
        self.btn_start.configure(state=state)

    def on_close(self) -> None:
        if self.running:
            if not messagebox.askyesno("Exit", "Conversion is running. Exit anyway?"):
                return
        self.root.destroy()


def main() -> int:
    root = tk.Tk()
    app = ConverterApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
