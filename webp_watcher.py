"""
webp_watcher.py — Auto WebP→JPG + Auto Tag + XoaDe
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Pipeline tự động khi phát hiện file .webp mới trong folder:
  1. Convert .webp → .jpg  (PIL/Pillow)
  2. Gọi Tagger Service (localhost:3067) → tạo .txt
     (General threshold: 0.25 | Chcharacter threshold: 1.0)
  3. Chạy D:/no/52_xoade.py --folder <folder> để lọc tags

UI: Grid ảnh — click ảnh → hiện nội dung .txt bên phải.
"""

import json
import http.client
import subprocess
import sys
import threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog

try:
    from PIL import Image, ImageTk
    PIL_OK = True
except ImportError:
    PIL_OK = False
    print("[webp_watcher] PIL not found — pip install Pillow")


# ══════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════

TAGGER_PORT         = 3067
GENERAL_THRESHOLD   = 0.25
CHARACTER_THRESHOLD = 1.0
MODEL               = "wd-eva02-large-tagger-v3"
XOADE_SCRIPT        = Path(r"D:\no\52_xoade.py")
XOADE_WORKDIR       = Path(r"D:\no")

THUMB_W    = 150
THUMB_H    = 150
THUMB_SIZE = (THUMB_W, THUMB_H)
GRID_COLS  = 4
POLL_MS    = 2000          # ms giữa mỗi lần kiểm tra webp mới

IMG_EXTS   = {".jpg", ".jpeg", ".png", ".webp"}
TAG_EXTS   = {".jpg", ".jpeg", ".png"}   # chỉ gửi tagger các loại này


# ══════════════════════════════════════════════════════
# COLORS / FONTS
# ══════════════════════════════════════════════════════

BG       = "#1d232a"
BG2      = "#252d38"
BG3      = "#181e26"
CARD     = "#2e3a4a"
CARD_SEL = "#89b4fa"
ACC      = "#89b4fa"
FG       = "#cdd6f4"
FG2      = "#6b7a8d"
GREEN    = "#a6e3a1"
RED      = "#f38ba8"
YEL      = "#fab387"
PURP     = "#cba6f7"

FN  = ("Segoe UI", 10)
FNB = ("Segoe UI", 10, "bold")
FS  = ("Segoe UI", 9)
FM  = ("Consolas", 9)
FT  = ("Segoe UI", 12, "bold")


# ══════════════════════════════════════════════════════
# HTTP HELPER
# ══════════════════════════════════════════════════════

def _post_json(path: str, body: dict):
    payload = json.dumps(body).encode("utf-8")
    conn = http.client.HTTPConnection("localhost", TAGGER_PORT, timeout=None)  # no timeout — batch có thể lâu
    conn.request("POST", path, body=payload, headers={
        "Content-Type":   "application/json",
        "Content-Length": str(len(payload)),
        "Connection":     "close",
    })
    res  = conn.getresponse()
    data = res.read().decode("utf-8")
    conn.close()
    if res.status < 200 or res.status >= 300:
        raise RuntimeError(f"HTTP {res.status}: {data[:200]}")
    return json.loads(data)


def _service_ok() -> bool:
    try:
        _post_json("/device", {})
        return True
    except Exception:
        return False


# ══════════════════════════════════════════════════════
# SCROLLABLE FRAME
# ══════════════════════════════════════════════════════

class ScrollFrame(tk.Frame):
    def __init__(self, parent, bg=BG, **kw):
        super().__init__(parent, bg=bg, **kw)
        self._cv = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)
        self._sb = ttk.Scrollbar(self, orient="vertical", command=self._cv.yview)
        self.inner = tk.Frame(self._cv, bg=bg)
        self._win = self._cv.create_window((0, 0), window=self.inner, anchor="nw")
        self._cv.configure(yscrollcommand=self._sb.set)
        self._sb.pack(side="right", fill="y")
        self._cv.pack(side="left", fill="both", expand=True)
        self.inner.bind("<Configure>", self._sync)
        self._cv.bind("<Configure>",  self._resize)
        self.bind("<Enter>", lambda _: self._cv.bind_all("<MouseWheel>", self._wheel))
        self.bind("<Leave>", lambda _: self._cv.unbind_all("<MouseWheel>"))

    def _sync(self,  _=None): self._cv.configure(scrollregion=self._cv.bbox("all"))
    def _resize(self, e):     self._cv.itemconfig(self._win, width=e.width)
    def _wheel(self, e):      self._cv.yview_scroll(-1 * (e.delta // 120), "units")

    def reset(self): self._cv.yview_moveto(0.0)


# ══════════════════════════════════════════════════════
# MAIN APP
# ══════════════════════════════════════════════════════

class WebpWatcher:

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("WebP Watcher — Auto Convert & Tag")
        self.root.geometry("1300x800")
        self.root.configure(bg=BG)
        self.root.resizable(True, True)

        # State
        self._folder:       Path | None  = None
        self._known_webps:  set[Path]    = set()
        self._watching:     bool         = False
        self._thumb_cache:  dict         = {}     # str(path) → PhotoImage
        self._all_images:   list[Path]   = []
        self._selected:     Path | None  = None
        self._cards:        dict         = {}     # str(path) → Frame
        self._prev_photo                 = None   # keep reference

        self._build_ui()
        self.root.after(300,   self._check_service)
        self.root.after(POLL_MS, self._poll)

    # ──────────────────────────────────────────────────
    # BUILD UI
    # ──────────────────────────────────────────────────

    def _build_ui(self):
        self.root.grid_columnconfigure(0, weight=3, minsize=700)
        self.root.grid_columnconfigure(1, weight=0, minsize=300)
        self.root.grid_rowconfigure(1, weight=1)

        self._build_topbar()
        self._build_grid_panel()
        self._build_right_panel()
        self._build_statusbar()

    # ── TOP BAR ───────────────────────────────────────

    def _build_topbar(self):
        top = tk.Frame(self.root, bg=BG2, pady=8)
        top.grid(row=0, column=0, columnspan=2, sticky="ew")

        # Service indicator
        svc = tk.Frame(top, bg=BG2)
        svc.pack(side="left", padx=14)
        tk.Label(svc, text="Tagger:", bg=BG2, fg=FG2, font=FS).pack(side="left")
        self._svc_dot = tk.Label(svc, text="●", bg=BG2, fg=RED, font=("Segoe UI", 14))
        self._svc_dot.pack(side="left", padx=3)
        self._svc_lbl = tk.Label(svc, text="Chưa kết nối", bg=BG2, fg=RED, font=FS)
        self._svc_lbl.pack(side="left")

        # Folder input
        fi = tk.Frame(top, bg=BG2)
        fi.pack(side="left", padx=16, fill="x", expand=True)
        tk.Label(fi, text="Folder:", bg=BG2, fg=FG, font=FN).pack(side="left")
        self._folder_var = tk.StringVar()
        self._entry_folder = tk.Entry(
            fi, textvariable=self._folder_var,
            bg=BG3, fg=FG, insertbackground=FG,
            relief="flat", font=FM, width=52,
        )
        self._entry_folder.pack(side="left", padx=8, ipady=4)
        self._entry_folder.bind("<Return>", lambda _: self._apply_folder())
        tk.Button(
            fi, text="Browse...", bg=CARD, fg=FG,
            relief="flat", padx=10, pady=4, cursor="hand2",
            font=FN, command=self._browse,
        ).pack(side="left", padx=(0, 4))

        tk.Button(
            fi, text="Load ↵", bg=BG2, fg=ACC,
            relief="flat", padx=8, pady=4, cursor="hand2",
            font=FN, command=self._apply_folder,
        ).pack(side="left")

        # Action buttons
        bf = tk.Frame(top, bg=BG2)
        bf.pack(side="right", padx=14)

        self._btn_watch = tk.Button(
            bf, text="▶  Watch", bg=GREEN, fg="#1e1e2e",
            relief="flat", padx=14, pady=6, cursor="hand2",
            font=FNB, command=self._toggle_watch,
        )
        self._btn_watch.pack(side="left", padx=4)

        tk.Button(
            bf, text="🏷  Tag All", bg=ACC, fg="#1e1e2e",
            relief="flat", padx=12, pady=6, cursor="hand2",
            font=FNB, command=self._manual_tag_all,
        ).pack(side="left", padx=4)

        tk.Button(
            bf, text="🗑  XoaDe", bg=CARD, fg=FG,
            relief="flat", padx=12, pady=6, cursor="hand2",
            font=FNB, command=self._manual_xoade,
        ).pack(side="left", padx=4)

        tk.Button(
            bf, text="⟳", bg=CARD, fg=FG,
            relief="flat", padx=10, pady=6, cursor="hand2",
            font=FNB, command=self._reload_grid,
        ).pack(side="left", padx=4)

    # ── GRID PANEL (left) ─────────────────────────────

    def _build_grid_panel(self):
        self._grid_scroll = ScrollFrame(self.root, bg=BG)
        self._grid_scroll.grid(row=1, column=0, sticky="nsew", padx=(8, 4), pady=8)
        self._grid_inner = self._grid_scroll.inner

    # ── RIGHT INFO PANEL ──────────────────────────────

    def _build_right_panel(self):
        right = tk.Frame(self.root, bg=BG2, width=300)
        right.grid(row=1, column=1, sticky="nsew", padx=(4, 8), pady=8)
        right.grid_propagate(False)
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(4, weight=1)

        # Title
        tk.Label(right, text="Thông tin ảnh", bg=BG2, fg=ACC, font=FNB
                 ).grid(row=0, column=0, sticky="w", padx=12, pady=(12, 6))

        # Preview image frame
        self._prev_frame = tk.Frame(right, bg=BG3, width=276, height=200)
        self._prev_frame.grid(row=1, column=0, padx=12, pady=(0, 6), sticky="ew")
        self._prev_frame.grid_propagate(False)
        self._prev_lbl = tk.Label(
            self._prev_frame, bg=BG3,
            text="Chọn ảnh để xem", fg=FG2, font=FS,
        )
        self._prev_lbl.place(relx=0.5, rely=0.5, anchor="center")

        # Filename
        self._fname_lbl = tk.Label(
            right, text="", bg=BG2, fg=FG, font=FS,
            wraplength=276, justify="left", anchor="w",
        )
        self._fname_lbl.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 4))

        # Tags header + reload button
        hdr = tk.Frame(right, bg=BG2)
        hdr.grid(row=3, column=0, sticky="ew", padx=12, pady=(0, 2))
        tk.Label(hdr, text="Tags (.txt):", bg=BG2, fg=FG2, font=FS).pack(side="left")
        tk.Button(
            hdr, text="↺", bg=BG2, fg=ACC,
            relief="flat", padx=4, pady=0, cursor="hand2",
            font=FS, command=self._refresh_txt_view,
        ).pack(side="right")

        # TXT text widget
        txt_outer = tk.Frame(right, bg=BG2)
        txt_outer.grid(row=4, column=0, sticky="nsew", padx=12, pady=(0, 12))
        txt_outer.grid_rowconfigure(0, weight=1)
        txt_outer.grid_columnconfigure(0, weight=1)

        self._txt_view = tk.Text(
            txt_outer, bg=BG3, fg=FG, font=FM,
            wrap="word", relief="flat", bd=0,
            insertbackground=FG, state="disabled",
            selectbackground=CARD, padx=6, pady=6,
        )
        sb = ttk.Scrollbar(txt_outer, orient="vertical", command=self._txt_view.yview)
        self._txt_view.configure(yscrollcommand=sb.set)
        self._txt_view.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")

    # ── STATUS BAR + LOG ──────────────────────────────

    def _build_statusbar(self):
        # Log panel (scrollable, 5 dòng)
        log_frame = tk.Frame(self.root, bg=BG3)
        log_frame.grid(row=2, column=0, columnspan=2, sticky="ew")
        log_frame.grid_columnconfigure(0, weight=1)

        # Header của log
        log_hdr = tk.Frame(log_frame, bg=BG3)
        log_hdr.grid(row=0, column=0, sticky="ew", padx=8, pady=(4, 0))
        self._count_var = tk.StringVar(value="")
        tk.Label(log_hdr, textvariable=self._count_var, bg=BG3, fg=FG2, font=FM
                 ).pack(side="left")
        tk.Button(log_hdr, text="Xóa log", bg=BG3, fg=FG2, relief="flat",
                  font=FS, cursor="hand2", pady=0,
                  command=self._clear_log).pack(side="right")

        # Text widget log
        log_inner = tk.Frame(log_frame, bg=BG3)
        log_inner.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 4))
        log_inner.grid_columnconfigure(0, weight=1)

        self._log_text = tk.Text(
            log_inner, bg=BG3, fg=FG2, font=FM,
            height=4, relief="flat", bd=0, state="disabled",
            wrap="word", selectbackground=CARD,
        )
        log_sb = ttk.Scrollbar(log_inner, orient="vertical", command=self._log_text.yview)
        self._log_text.configure(yscrollcommand=log_sb.set)
        self._log_text.grid(row=0, column=0, sticky="ew")
        log_sb.grid(row=0, column=1, sticky="ns")

        # Color tags
        self._log_text.tag_configure("green",  foreground=GREEN)
        self._log_text.tag_configure("red",    foreground=RED)
        self._log_text.tag_configure("yellow", foreground=YEL)
        self._log_text.tag_configure("acc",    foreground=ACC)
        self._log_text.tag_configure("purp",   foreground=PURP)
        self._log_text.tag_configure("dim",    foreground=FG2)

    # ──────────────────────────────────────────────────
    # FOLDER
    # ──────────────────────────────────────────────────

    def _browse(self):
        d = filedialog.askdirectory(title="Chọn folder theo dõi")
        if d:
            self._folder_var.set(d)
            self._apply_folder()

    def _apply_folder(self):
        p = Path(self._folder_var.get().strip())
        if not p.exists():
            self._log("Folder không tồn tại!", RED)
            return
        self._folder = p
        self._known_webps = set(p.glob("*.webp"))
        self._reload_grid()
        self._log(f"Folder: {p}", GREEN)

    # ──────────────────────────────────────────────────
    # IMAGE GRID
    # ──────────────────────────────────────────────────

    def _reload_grid(self):
        if not self._folder or not self._folder.exists():
            return

        imgs = sorted(
            f for f in self._folder.iterdir()
            if f.is_file() and f.suffix.lower() in IMG_EXTS
        )
        self._all_images = imgs
        self._cards.clear()
        self._thumb_cache.clear()
        self._selected = None

        for w in self._grid_inner.winfo_children():
            w.destroy()

        for col in range(GRID_COLS):
            self._grid_inner.grid_columnconfigure(col, weight=1)

        for i, path in enumerate(imgs):
            row, col = divmod(i, GRID_COLS)
            self._make_card(path, row, col)

        self._grid_scroll.reset()
        self._count_var.set(f"{len(imgs)} ảnh")

    def _make_card(self, path: Path, row: int, col: int):
        card = tk.Frame(self._grid_inner, bg=CARD, cursor="hand2", padx=3, pady=3)
        card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
        self._cards[str(path)] = card

        # Thumbnail
        thumb = self._get_thumb(path)

        if thumb:
            img_lbl = tk.Label(card, image=thumb, bg=CARD, cursor="hand2",
                               width=THUMB_W, height=THUMB_H)
        else:
            img_lbl = tk.Label(card, bg=CARD, fg=FG2, font=FS,
                               text="⏳" if not PIL_OK else path.suffix.upper(),
                               width=THUMB_W // 8, height=THUMB_H // 16)
        img_lbl.pack(pady=(4, 0))

        # Filename
        name = path.name
        short = (name[:18] + "…") if len(name) > 19 else name
        name_lbl = tk.Label(card, text=short, bg=CARD, fg=FG, font=FS,
                             wraplength=THUMB_W, justify="center")
        name_lbl.pack()

        # Tag indicator dot
        has_txt = path.with_suffix(".txt").exists()
        dot_lbl = tk.Label(card, text="● tagged" if has_txt else "○ no tag",
                           bg=CARD, fg=GREEN if has_txt else FG2, font=FS)
        dot_lbl.pack(pady=(0, 3))

        # Events
        def on_click(_, p=path, c=card):
            self._select(p, c)

        def on_enter(_, c=card, p=path):
            if p != self._selected:
                c.configure(bg="#3a4a5e")
                for w in c.winfo_children():
                    try: w.configure(bg="#3a4a5e")
                    except Exception: pass

        def on_leave(_, c=card, p=path):
            bg = CARD_SEL if p == self._selected else CARD
            c.configure(bg=bg)
            for w in c.winfo_children():
                try: w.configure(bg=bg)
                except Exception: pass

        for w in [card, img_lbl, name_lbl, dot_lbl]:
            w.bind("<Button-1>", on_click)
            w.bind("<Enter>",    on_enter)
            w.bind("<Leave>",    on_leave)

    def _get_thumb(self, path: Path):
        if not PIL_OK:
            return None
        key = str(path)
        if key in self._thumb_cache:
            return self._thumb_cache[key]
        try:
            img = Image.open(path).convert("RGB")
            img.thumbnail(THUMB_SIZE, Image.LANCZOS)
            canvas = Image.new("RGB", THUMB_SIZE, (46, 58, 74))   # CARD color
            ox = (THUMB_W - img.width)  // 2
            oy = (THUMB_H - img.height) // 2
            canvas.paste(img, (ox, oy))
            photo = ImageTk.PhotoImage(canvas)
            self._thumb_cache[key] = photo
            return photo
        except Exception:
            return None

    # ──────────────────────────────────────────────────
    # SELECT IMAGE → show info
    # ──────────────────────────────────────────────────

    def _select(self, path: Path, card: tk.Frame):
        # Deselect old
        if self._selected:
            old = self._cards.get(str(self._selected))
            if old and old.winfo_exists():
                old.configure(bg=CARD)
                for w in old.winfo_children():
                    try: w.configure(bg=CARD)
                    except Exception: pass

        self._selected = path
        card.configure(bg=CARD_SEL)
        for w in card.winfo_children():
            try: w.configure(bg=CARD_SEL)
            except Exception: pass

        self._fname_lbl.configure(text=path.name)
        self._show_preview(path)
        self._show_txt(path)

    def _show_preview(self, path: Path):
        self._prev_lbl.configure(image="", text="", bg=BG3)
        if not PIL_OK:
            self._prev_lbl.configure(text="PIL not installed", fg=FG2)
            return
        try:
            img = Image.open(path).convert("RGB")
            img.thumbnail((276, 196), Image.LANCZOS)
            self._prev_photo = ImageTk.PhotoImage(img)
            self._prev_lbl.configure(image=self._prev_photo)
            self._prev_lbl.place(relx=0.5, rely=0.5, anchor="center")
        except Exception as e:
            self._prev_lbl.configure(text=f"Lỗi: {e}", fg=RED, image="")

    def _show_txt(self, path: Path):
        txt_path = path.with_suffix(".txt")
        self._txt_view.configure(state="normal")
        self._txt_view.delete("1.0", "end")
        if txt_path.exists():
            try:
                content = txt_path.read_text(encoding="utf-8").strip()
                self._txt_view.insert("1.0", content if content else "(file .txt rỗng)")
            except Exception as e:
                self._txt_view.insert("1.0", f"[Lỗi đọc: {e}]")
        else:
            self._txt_view.insert("1.0", "(Chưa có file .txt)")
        self._txt_view.configure(state="disabled")

    def _refresh_txt_view(self):
        if self._selected:
            self._show_txt(self._selected)

    # ──────────────────────────────────────────────────
    # WATCH — POLL FOR NEW WEBP
    # ──────────────────────────────────────────────────

    def _toggle_watch(self):
        if not self._watching:
            self._apply_folder()
            if not self._folder:
                return
            self._watching = True
            self._btn_watch.configure(text="⏹  Stop", bg=RED, fg="white")
            self._log(f"Đang theo dõi: {self._folder.name}", GREEN)
            # Tự động tag ngay các ảnh chưa có .txt khi bật Watch
            threading.Thread(target=self._auto_tag_on_start, daemon=True).start()
        else:
            self._watching = False
            self._btn_watch.configure(text="▶  Watch", bg=GREEN, fg="#1e1e2e")
            self._log("Đã dừng theo dõi.", YEL)

    def _auto_tag_on_start(self):
        """Khi bật Watch: tag ngay ảnh chưa có .txt → xoade → reload grid."""
        untagged = [
            f for f in self._folder.iterdir()
            if f.is_file()
            and f.suffix.lower() in TAG_EXTS
            and not f.with_suffix(".txt").exists()
        ]
        if untagged:
            self._log_thread(f"Auto tag {len(untagged)} ảnh chưa có tag...", YEL)
            self._do_tag(untagged)
            self._do_xoade(self._folder)
            self.root.after(0, self._reload_grid)
        else:
            self._log_thread("Tất cả ảnh đã có tag. Đang theo dõi...", GREEN)

    def _poll(self):
        if self._watching and self._folder and self._folder.exists():
            current   = set(self._folder.glob("*.webp"))
            new_webps = current - self._known_webps
            if new_webps:
                self._known_webps |= new_webps
                self._log(f"Phát hiện {len(new_webps)} webp mới → xử lý...", YEL)
                threading.Thread(
                    target=self._pipeline,
                    args=(list(new_webps),),
                    daemon=True,
                ).start()
        self.root.after(POLL_MS, self._poll)

    # ──────────────────────────────────────────────────
    # PIPELINE
    # ──────────────────────────────────────────────────

    def _pipeline(self, webps: list):
        """Convert webp → jpg → tag → xoade (runs in background thread)."""
        converted = []
        for wp in webps:
            wp = Path(wp)
            try:
                jpg = wp.with_suffix(".jpg")
                img = Image.open(wp).convert("RGB")
                img.save(jpg, "JPEG", quality=95)
                converted.append(jpg)
                self._log_thread(f"Convert OK: {wp.name} → {jpg.name}", GREEN)
            except Exception as e:
                self._log_thread(f"Lỗi convert {wp.name}: {e}", RED)

        if converted:
            self._do_tag(converted)
            self._do_xoade(self._folder)
            self.root.after(0, self._reload_grid)

    def _do_tag(self, images: list):
        self._log_thread(f"Tagging {len(images)} ảnh...", ACC)
        try:
            result = _post_json("/tagger", {
                "images":              [str(p) for p in images],
                "model":               MODEL,
                "general_threshold":   GENERAL_THRESHOLD,
                "character_threshold": CHARACTER_THRESHOLD,
                "remove_underscores":  True,
                "tags_ignored":        [],
            })
            if isinstance(result, dict) and result.get("error"):
                raise RuntimeError(result["error"])
            count = 0
            for img_str, tags in result.items():
                Path(img_str).with_suffix(".txt").write_text(
                    ", ".join(tags), encoding="utf-8"
                )
                count += 1
            self._log_thread(f"Tag xong: {count} file .txt", GREEN)
        except Exception as e:
            self._log_thread(f"Lỗi tagger: {e}", RED)

    def _do_xoade(self, folder: Path):
        self._log_thread("Chạy 52_xoade.py...", PURP)
        try:
            r = subprocess.run(
                [sys.executable, str(XOADE_SCRIPT), "--folder", str(folder)],
                cwd=str(XOADE_WORKDIR),
                capture_output=True, text=True, timeout=120,
            )
            if r.returncode == 0:
                self._log_thread("XoaDe xong.", GREEN)
            else:
                self._log_thread(f"XoaDe lỗi: {r.stderr[:100]}", RED)
        except Exception as e:
            self._log_thread(f"Lỗi xoade: {e}", RED)

    # ── Manual buttons ─────────────────────────────────

    def _manual_tag_all(self):
        if not self._ensure_folder():
            return
        images = [f for f in self._folder.iterdir()
                  if f.is_file() and f.suffix.lower() in TAG_EXTS]
        if not images:
            self._log("Không có ảnh jpg/png.", YEL)
            return
        self._log(f"Tag thủ công {len(images)} ảnh...", ACC)

        def _run():
            self._do_tag(images)
            self._do_xoade(self._folder)
            self.root.after(0, self._reload_grid)

        threading.Thread(target=_run, daemon=True).start()

    def _manual_xoade(self):
        if not self._ensure_folder():
            return
        threading.Thread(target=self._do_xoade, args=(self._folder,), daemon=True).start()

    def _ensure_folder(self) -> bool:
        s = self._folder_var.get().strip()
        if s:
            self._folder = Path(s)
        if not self._folder or not self._folder.exists():
            self._log("Chưa chọn folder hợp lệ!", RED)
            return False
        return True

    # ──────────────────────────────────────────────────
    # SERVICE CHECK
    # ──────────────────────────────────────────────────

    def _check_service(self):
        def _do():
            ok = _service_ok()
            self.root.after(0, lambda: self._update_svc(ok))
        threading.Thread(target=_do, daemon=True).start()
        self.root.after(10_000, self._check_service)

    def _update_svc(self, ok: bool):
        if ok:
            self._svc_dot.configure(fg=GREEN)
            self._svc_lbl.configure(text="Đang chạy", fg=GREEN)
        else:
            self._svc_dot.configure(fg=RED)
            self._svc_lbl.configure(text="Chưa kết nối", fg=RED)

    # ──────────────────────────────────────────────────
    # LOG
    # ──────────────────────────────────────────────────

    _COLOR_TAG = {
        GREEN: "green", RED: "red", YEL: "yellow",
        ACC: "acc", PURP: "purp", FG2: "dim",
    }

    def _log(self, msg: str, color: str = FG2):
        tag = self._COLOR_TAG.get(color, "dim")
        self._log_text.configure(state="normal")
        self._log_text.insert("end", msg + "\n", tag)
        self._log_text.see("end")
        self._log_text.configure(state="disabled")

    def _clear_log(self):
        self._log_text.configure(state="normal")
        self._log_text.delete("1.0", "end")
        self._log_text.configure(state="disabled")

    def _log_thread(self, msg: str, color: str = FG2):
        self.root.after(0, lambda m=msg, c=color: self._log(m, c))

    # ──────────────────────────────────────────────────

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = WebpWatcher()
    app.run()
