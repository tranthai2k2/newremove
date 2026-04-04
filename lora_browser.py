"""
lora_browser.py
─────────────────────────────────────────────────────────────────
LoRA Browser — Main GUI App

Panel 1 : Browse LoRAs (search + breast-size selector + image grid)
Panel 2 : Selected LoRAs + folder path inputs
Panel 3 : Combined output (copy-ready)

Processing pipeline per LoRA:
  folder/  → tag_enhancer_v12.6_FINAL.py  → out_tags/addfaceless.txt
           → lora_processor.process_character_txt → out_tags/<name>-character.txt
All <name>-character.txt files are concatenated (1 blank line separator)
and shown in Panel 3, with breast-size tags replaced on-the-fly.
"""

import tkinter as tk
from tkinter import ttk, filedialog
from pathlib import Path
import json
import threading
from typing import List, Dict, Any, Optional

try:
    from PIL import Image, ImageTk
    PIL_OK = True
except ImportError:
    PIL_OK = False
    print("[lora_browser] PIL not found — thumbnails disabled. pip install Pillow")

import lora_processor as lp

# ══════════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════════

LORA_ROOT   = Path(r"E:\webui_forge_cu121_torch231\webui\models\Lora")
LORA_EXTS   = {'.safetensors', '.pt', '.ckpt'}
IMG_EXTS    = ['.png', '.jpg', '.jpeg', '.webp']
THUMB_SIZE  = (112, 112)
GRID_COLS   = 3
THUMB_BATCH = 15          # thumbnails loaded per background batch
SEPARATOR   = '\n\n'      # between LoRA results in Panel 3

BREAST_CHOICES = [
    "huge breasts",
    "large breasts",
    "gigantic breasts",
    "medium breasts",
    "small breasts",
]

# ── Colour palette ───────────────────────────────────────────
C = {
    # ── Palette (% giảm dần): #091413 → #285A48 → #408A71 → #B0E4CC ──
    'root':      '#091413',   # bg chính — nhiều nhất
    'p1':        '#091413',
    'p2':        '#091413',
    'p3':        '#285A48',   # output panel
    'p3_text':   '#1d4035',   # text area trong output
    'search_bg': '#285A48',
    'card':      '#285A48',   # grid cell, p2 card
    'hdr':       '#408A71',   # tên lora (header nâu cũ → xanh vừa)
    'folder_bg': '#408A71',   # folder path bg
    'x_btn':     '#8B2020',   # xóa card (đỏ tối)
    'copy_btn':  '#408A71',
    'scroll_dn': '#285A48',
    'proc_btn':  '#408A71',
    'b_on':      '#408A71',   # breast btn selected
    'b_off':     '#285A48',   # breast btn normal
    'txt':       '#B0E4CC',   # text chính — ít nhất
    'txt_dim':   '#5da886',   # text mờ
    'txt_dark':  '#091413',   # text trên nền sáng
    'sep':       '#285A48',
    'ok':        '#B0E4CC',
    'err':       '#e05252',
    'info':      '#408A71',
    'hover':     '#408A71',   # hover trên card
}

FONT = {
    'title':  ('Arial', 12, 'bold'),
    'normal': ('Arial', 10),
    'small':  ('Arial', 9),
    'name':   ('Arial', 9, 'bold'),
    'mono':   ('Consolas', 9),
}


# ══════════════════════════════════════════════════════════════
# SCROLLABLE FRAME HELPER
# ══════════════════════════════════════════════════════════════

class ScrollFrame(tk.Frame):
    """Vertically scrollable container with debounced resize to avoid lag."""

    def __init__(self, parent, bg: str, **kw):
        super().__init__(parent, bg=bg, **kw)
        self._canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)
        self._sb     = ttk.Scrollbar(self, orient='vertical', command=self._canvas.yview)
        self.inner   = tk.Frame(self._canvas, bg=bg)
        self._win    = self._canvas.create_window((0, 0), window=self.inner, anchor='nw')

        self._canvas.configure(yscrollcommand=self._sb.set)
        self._sb.pack(side='right', fill='y')
        self._canvas.pack(side='left', fill='both', expand=True)

        self._sync_job   = None
        self._resize_job = None

        self.inner.bind('<Configure>', self._on_inner_configure)
        self._canvas.bind('<Configure>', self._on_canvas_configure)

        self.bind('<Enter>', self._activate_wheel)
        self.bind('<Leave>', self._deactivate_wheel)
        self._canvas.bind('<Enter>', self._activate_wheel)
        self._canvas.bind('<Leave>', self._deactivate_wheel)

    # Debounce: inner resize → update scrollregion
    def _on_inner_configure(self, _=None):
        if self._sync_job:
            self.after_cancel(self._sync_job)
        self._sync_job = self.after(25, self._do_sync)

    def _do_sync(self):
        self._sync_job = None
        self._canvas.configure(scrollregion=self._canvas.bbox('all'))

    # Debounce: canvas resize → update inner width (prevent resize lag)
    def _on_canvas_configure(self, e):
        w = e.width
        if self._resize_job:
            self.after_cancel(self._resize_job)
        self._resize_job = self.after(25, lambda: self._canvas.itemconfig(self._win, width=w))

    def _activate_wheel(self, _=None):
        self._canvas.bind_all('<MouseWheel>', self._on_wheel)

    def _deactivate_wheel(self, _=None):
        self._canvas.unbind_all('<MouseWheel>')

    def _on_wheel(self, e):
        self._canvas.yview_scroll(-1 * (e.delta // 120), 'units')

    def scroll_down(self, units: int = 4):
        self._canvas.yview_scroll(units, 'units')

    def scroll_bottom(self):
        self._canvas.yview_moveto(1.0)

    def reset_scroll(self):
        self._canvas.yview_moveto(0.0)

    def force_update_region(self):
        self.inner.update_idletasks()
        bbox = self._canvas.bbox('all')
        if bbox:
            self._canvas.configure(
                scrollregion=(bbox[0], bbox[1], bbox[2], bbox[3] + 12)
            )
        else:
            self._canvas.configure(scrollregion=(0, 0, 0, 0))


# ══════════════════════════════════════════════════════════════
# MAIN APP
# ══════════════════════════════════════════════════════════════

class LoRABrowser:

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("LoRA Browser")
        self.root.geometry("1240x740")
        self.root.configure(bg=C['root'])
        self.root.resizable(True, True)

        # Data
        self.script_dir      = Path(__file__).parent
        self.all_loras:       List[Dict] = []
        self.filtered_loras:  List[Dict] = []
        self.selected:        List[Dict] = []
        self._pil_cache:      Dict[str, Any] = {}   # PIL Images (bg thread)
        self.thumb_cache:     Dict[str, Any] = {}   # PhotoImages (main thread)
        self._image_labels:   Dict[str, tk.Label] = {}  # path → Label widget
        self._raw_output      = ""
        self._search_after    = None
        self._thumb_loading   = False

        # Tkinter vars
        self.search_var  = tk.StringVar()
        self.breast_var  = tk.StringVar(value=BREAST_CHOICES[0])
        self.status_var  = tk.StringVar(value="Scanning LoRA folder…")
        self._breast_btns: Dict[str, tk.Button] = {}

        self.search_var.trace_add('write', self._on_search)

        self._build_ui()
        threading.Thread(target=self._scan_loras, daemon=True).start()

    # ──────────────────────────────────────────────────────────
    # PHASE 1 — SCAN FILES  (background thread, fast)
    # ──────────────────────────────────────────────────────────

    def _scan_loras(self):
        loras: List[Dict] = []
        if not LORA_ROOT.exists():
            self._after_status(f"LoRA root not found: {LORA_ROOT}", 'err')
            return

        for f in LORA_ROOT.rglob('*'):
            if f.suffix.lower() not in LORA_EXTS:
                continue
            img = next((f.with_suffix(e) for e in IMG_EXTS if f.with_suffix(e).exists()), None)
            if img is None:
                continue
            jf = f.with_suffix('.json')
            if not jf.exists():
                continue
            try:
                data = json.loads(jf.read_text(encoding='utf-8'))
            except Exception:
                continue
            loras.append({
                'name':       f.stem,
                'file':       f,
                'image':      img,
                'activation': data.get('activation text', ''),
                'weight':     float(data.get('preferred weight', 0) or 0),
                'negative':   data.get('negative text', ''),
            })

        loras.sort(key=lambda x: x['name'].lower())

        self.all_loras = loras
        q = self.search_var.get().strip().lower()
        self.filtered_loras = [l for l in loras if q in l['name'].lower()] if q else loras[:]

        # Show grid immediately (placeholders, no images yet)
        self.root.after(0, self._refresh_grid)
        self._after_status(f"Found {len(loras)} LoRAs — loading thumbnails…", 'ok')

        # PHASE 2 — load PIL images in batches (still background)
        if PIL_OK:
            self._load_thumbs_in_batches(loras)

    # ──────────────────────────────────────────────────────────
    # PHASE 2 — LOAD THUMBNAILS IN BATCHES  (background thread)
    # ──────────────────────────────────────────────────────────

    def _load_thumbs_in_batches(self, loras: List[Dict]):
        self._thumb_loading = True
        for i in range(0, len(loras), THUMB_BATCH):
            batch = loras[i:i + THUMB_BATCH]
            batch_result: List[tuple] = []

            for lora in batch:
                key = str(lora['image'])
                if key in self._pil_cache or key in self.thumb_cache:
                    continue
                try:
                    img = Image.open(lora['image']).convert('RGB')
                    img.thumbnail(THUMB_SIZE, Image.LANCZOS)
                    bg = Image.new('RGB', THUMB_SIZE, tuple(int(C['card'].lstrip('#')[i*2:i*2+2], 16) for i in range(3)))
                    ox = (THUMB_SIZE[0] - img.width)  // 2
                    oy = (THUMB_SIZE[1] - img.height) // 2
                    bg.paste(img, (ox, oy))
                    batch_result.append((key, bg))
                except Exception:
                    pass

            # Push to main thread: convert PIL → PhotoImage and update labels
            self.root.after(0, lambda b=batch_result: self._apply_thumb_batch(b))

        self._thumb_loading = False
        self._after_status(f"Loaded {len(loras)} LoRAs", 'ok')

    def _apply_thumb_batch(self, batch: list):
        """Main thread: PIL → PhotoImage, update any visible label."""
        for key, pil_img in batch:
            try:
                photo = ImageTk.PhotoImage(pil_img)
                self.thumb_cache[key] = photo
                lbl = self._image_labels.get(key)
                if lbl and lbl.winfo_exists():
                    lbl.configure(image=photo, text='', width=0, height=0)
            except Exception:
                pass

    # ──────────────────────────────────────────────────────────
    # UI CONSTRUCTION
    # ──────────────────────────────────────────────────────────

    def _build_ui(self):
        self.root.grid_columnconfigure(0, weight=4, minsize=370)
        self.root.grid_columnconfigure(1, weight=3, minsize=270)
        self.root.grid_columnconfigure(2, weight=4, minsize=300)
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=0)

        f1 = tk.Frame(self.root, bg=C['p1'])
        f1.grid(row=0, column=0, sticky='nsew', padx=(8, 3), pady=(8, 3))
        self._build_panel1(f1)

        f2 = tk.Frame(self.root, bg=C['p2'])
        f2.grid(row=0, column=1, sticky='nsew', padx=3, pady=(8, 3))
        self._build_panel2(f2)

        f3 = tk.Frame(self.root, bg=C['p3'])
        f3.grid(row=0, column=2, sticky='nsew', padx=(3, 8), pady=(8, 3))
        self._build_panel3(f3)

        bar = tk.Frame(self.root, bg='#111122', height=22)
        bar.grid(row=1, column=0, columnspan=3, sticky='ew', padx=8, pady=(0, 4))
        bar.grid_propagate(False)
        self._status_lbl = tk.Label(bar, textvariable=self.status_var,
                                    bg='#111122', fg=C['txt_dim'],
                                    font=FONT['mono'], anchor='w')
        self._status_lbl.pack(side='left', padx=8, fill='x')

    # ── PANEL 1 ───────────────────────────────────────────────

    def _build_panel1(self, parent: tk.Frame):
        parent.grid_rowconfigure(2, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        # Search bar
        sb = tk.Frame(parent, bg=C['p1'])
        sb.grid(row=0, column=0, sticky='ew', padx=10, pady=(10, 4))
        wrap = tk.Frame(sb, bg=C['search_bg'], pady=2, padx=2)
        wrap.pack(fill='x')
        tk.Entry(wrap, textvariable=self.search_var,
                 bg=C['search_bg'], fg=C['txt'], insertbackground=C['txt'],
                 relief='flat', font=FONT['normal'], bd=6,
                 ).pack(side='left', fill='x', expand=True)
        tk.Label(wrap, text='🔍', bg=C['search_bg'],
                 fg=C['txt_dim'], font=FONT['normal']).pack(side='right', padx=6)

        # Breast size buttons
        bf = tk.Frame(parent, bg=C['p1'])
        bf.grid(row=1, column=0, sticky='ew', padx=10, pady=(0, 6))
        for ch in BREAST_CHOICES:
            btn = tk.Button(
                bf, text=ch, font=FONT['small'], relief='flat', bd=0,
                bg=C['b_on'] if ch == BREAST_CHOICES[0] else C['b_off'],
                fg='white', padx=8, pady=4, cursor='hand2',
                command=lambda c=ch: self._select_breast(c),
            )
            btn.pack(side='left', padx=3, pady=2)
            self._breast_btns[ch] = btn

        # Scrollable image grid
        self._grid_scroll = ScrollFrame(parent, bg=C['p1'])
        self._grid_scroll.grid(row=2, column=0, sticky='nsew', padx=6, pady=(0, 6))
        self._grid_inner = self._grid_scroll.inner

    def _refresh_grid(self):
        # Clear
        self._image_labels.clear()
        for w in self._grid_inner.winfo_children():
            w.destroy()
        self._grid_scroll.reset_scroll()

        loras = self.filtered_loras
        if not loras:
            tk.Label(self._grid_inner, text="No LoRAs found",
                     bg=C['p1'], fg=C['txt_dim'], font=FONT['normal']
                     ).grid(row=0, column=0, pady=30)
            self._grid_scroll.force_update_region()
            return

        for col in range(GRID_COLS):
            self._grid_inner.grid_columnconfigure(col, weight=1)

        for i, lora in enumerate(loras):
            row, col = divmod(i, GRID_COLS)
            self._make_grid_cell(self._grid_inner, lora, row, col)

        # Recalculate scrollregion immediately + again after layout settles
        self._grid_scroll.force_update_region()
        self.root.after(100, self._grid_scroll.force_update_region)

    def _make_grid_cell(self, parent, lora: dict, row: int, col: int):
        cell = tk.Frame(parent, bg=C['card'], cursor='hand2')
        cell.grid(row=row, column=col, padx=4, pady=4, sticky='nsew')

        key = str(lora['image'])

        # Fixed-size image container — ensures consistent row height
        img_box = tk.Frame(cell, bg=C['card'],
                           width=THUMB_SIZE[0], height=THUMB_SIZE[1])
        img_box.pack(pady=(4, 0))
        img_box.pack_propagate(False)

        photo = self.thumb_cache.get(key)
        if photo:
            img_lbl = tk.Label(img_box, image=photo, bg=C['card'], cursor='hand2')
        else:
            img_lbl = tk.Label(img_box, text='…', bg=C['card'],
                               fg=C['txt_dim'], font=FONT['small'])
            self._image_labels[key] = img_lbl   # register for later update
        img_lbl.pack(expand=True, fill='both')

        # Name label
        name_lbl = tk.Label(
            cell, text=lora['name'],
            bg=C['hdr'], fg='white', font=FONT['name'],
            wraplength=THUMB_SIZE[0] + 10, justify='center', padx=4, pady=3,
        )
        name_lbl.pack(fill='x', padx=2, pady=(2, 4))

        def on_click(_e, l=lora):
            self._add_to_panel2(l)

        def on_enter(_e, c=cell):
            c.configure(bg=C['hover'])

        def on_leave(_e, c=cell):
            c.configure(bg=C['card'])

        for w in (cell, img_lbl, name_lbl):
            w.bind('<Button-1>', on_click)
            w.bind('<Enter>', on_enter)
            w.bind('<Leave>', on_leave)

    def _on_search(self, *_):
        if self._search_after is not None:
            self.root.after_cancel(self._search_after)
        self._search_after = self.root.after(1000, self._do_search)

    def _do_search(self):
        self._search_after = None
        q = self.search_var.get().strip().lower()
        self.filtered_loras = (
            [l for l in self.all_loras if q in l['name'].lower()] if q
            else self.all_loras[:]
        )
        self._refresh_grid()

    def _select_breast(self, choice: str):
        self.breast_var.set(choice)
        for c, btn in self._breast_btns.items():
            btn.configure(bg=C['b_on'] if c == choice else C['b_off'])
        self._reapply_breast()

    # ── PANEL 2 ───────────────────────────────────────────────

    def _build_panel2(self, parent: tk.Frame):
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        tk.Label(parent, text="Selected LoRAs",
                 bg=C['p2'], fg=C['txt'], font=FONT['title']
                 ).grid(row=0, column=0, pady=(10, 4))

        self._p2_scroll = ScrollFrame(parent, bg=C['p2'])
        self._p2_scroll.grid(row=1, column=0, sticky='nsew', padx=6)
        self._p2_list = self._p2_scroll.inner

        btn_row = tk.Frame(parent, bg=C['p2'])
        btn_row.grid(row=2, column=0, sticky='ew', padx=6, pady=8)

        tk.Button(btn_row, text="▼", font=('Arial', 13, 'bold'),
                  bg=C['scroll_dn'], fg='white', relief='flat', bd=0,
                  padx=12, pady=4, cursor='hand2',
                  command=self._p2_scroll.scroll_down,
                  ).pack(side='left', padx=4)

        tk.Button(btn_row, text="Process All  ▶", font=FONT['normal'],
                  bg=C['proc_btn'], fg='white', relief='flat', bd=0,
                  padx=12, pady=6, cursor='hand2',
                  command=self._process_all,
                  ).pack(side='right', padx=4)

    # ── Card thumbnail (52×52) ─────────────────────────────────

    def _get_card_thumb(self, image_path: Path):
        if not PIL_OK:
            return None
        key = f"c52_{image_path}"
        if key in self.thumb_cache:
            return self.thumb_cache[key]
        try:
            SZ = (52, 52)
            img = Image.open(image_path).convert('RGB')
            img.thumbnail(SZ, Image.LANCZOS)
            canvas = Image.new('RGB', SZ, tuple(int(C['card'].lstrip('#')[i*2:i*2+2], 16) for i in range(3)))
            canvas.paste(img, ((SZ[0] - img.width) // 2, (SZ[1] - img.height) // 2))
            photo = ImageTk.PhotoImage(canvas)
            self.thumb_cache[key] = photo
            return photo
        except Exception:
            return None

    # ── Add card to Panel 2 ────────────────────────────────────

    def _add_to_panel2(self, lora: dict, after_card=None):
        """
        Thêm 1 card cho lora. after_card=Frame → chèn ngay sau card đó.
        Cùng 1 lora có thể có nhiều card (mỗi card = 1 folder + 1 prompt riêng).
        """
        folder_var     = tk.StringVar()
        line_count_var = tk.StringVar(value='')
        use_default    = tk.BooleanVar(value=True)

        # ── Outer card ────────────────────────────────────────
        card = tk.Frame(self._p2_list, bg=C['card'])
        if after_card is not None:
            card.pack(fill='x', padx=4, pady=(0, 6), after=after_card)
        else:
            card.pack(fill='x', padx=4, pady=(0, 6))

        entry = {
            'lora':           lora,
            'card':           card,
            'use_default':    use_default,
            'custom_widget':  None,
            'custom_frame':   None,
            'folder_var':     folder_var,
            'line_count_var': line_count_var,
        }

        # ── Header: ảnh + tên + weight + dòng + [+][✕] ────────
        hdr = tk.Frame(card, bg=C['hdr'])
        hdr.pack(fill='x')

        thumb = self._get_card_thumb(lora['image'])
        img_lbl = tk.Label(hdr, bg=C['hdr'], width=52, height=52)
        if thumb:
            img_lbl.configure(image=thumb)
            img_lbl._photo = thumb
        else:
            img_lbl.configure(text='?', fg=C['txt_dim'], font=FONT['small'])
        img_lbl.pack(side='left', padx=(6, 4), pady=4)

        # Tên + thông tin
        info = tk.Frame(hdr, bg=C['hdr'])
        info.pack(side='left', fill='x', expand=True, pady=4)
        tk.Label(info, text=lora['name'],
                 bg=C['hdr'], fg='white', font=FONT['name'],
                 anchor='w', wraplength=160, justify='left',
                 ).pack(fill='x')
        w_str = f"w: {int(lora['weight']) if lora['weight'] == int(lora['weight']) else lora['weight']}" if lora['weight'] else ""
        meta_var = tk.StringVar(value=w_str)
        tk.Label(info, textvariable=meta_var,
                 bg=C['hdr'], fg=C['txt_dim'], font=FONT['small'],
                 anchor='w').pack(fill='x')
        tk.Label(info, textvariable=line_count_var,
                 bg=C['hdr'], fg=C['ok'], font=FONT['small'],
                 anchor='w').pack(fill='x')

        # Nút [+] clone và [✕] xóa
        btn_col = tk.Frame(hdr, bg=C['hdr'])
        btn_col.pack(side='right', padx=4, pady=4, anchor='n')
        tk.Button(btn_col, text='+', font=('Arial', 11, 'bold'),
                  bg=C['hdr'], fg=C['ok'], relief='flat', bd=0,
                  padx=6, pady=2, cursor='hand2',
                  command=lambda e=entry: self._clone_card(e),
                  ).pack(fill='x')
        tk.Button(btn_col, text='✕', font=('Arial', 9, 'bold'),
                  bg=C['x_btn'], fg='white', relief='flat', bd=0,
                  padx=6, pady=2, cursor='hand2',
                  command=lambda e=entry: self._remove_card(e),
                  ).pack(fill='x', pady=(4, 0))

        # ── Body: prompt toggle + folder ──────────────────────
        body = tk.Frame(card, bg=C['card'])
        body.pack(fill='x', padx=6, pady=(4, 6))

        tk.Checkbutton(
            body, text='Dùng activation text mặc định',
            variable=use_default,
            bg=C['card'], fg=C['txt_dim'], font=FONT['small'],
            selectcolor=C['card'], activebackground=C['card'],
            command=lambda e=entry: self._toggle_custom_prompt(e),
        ).pack(anchor='w')

        # Custom prompt — ẩn mặc định, hiện khi bỏ check
        cframe = tk.Frame(body, bg=C['card'])
        ctxt = tk.Text(
            cframe, height=3,
            bg=C['p3_text'], fg=C['txt_dark'],
            insertbackground=C['txt_dark'], relief='flat',
            font=FONT['mono'], wrap='word', padx=4, pady=4,
        )
        ctxt.pack(fill='x')
        entry['custom_frame']  = cframe
        entry['custom_widget'] = ctxt

        # Folder row
        frow = tk.Frame(body, bg=C['folder_bg'])
        frow.pack(fill='x', pady=(4, 0))
        tk.Entry(frow, textvariable=folder_var,
                 bg=C['folder_bg'], fg='white', insertbackground='white',
                 relief='flat', font=FONT['small'], bd=4,
                 ).pack(side='left', fill='x', expand=True)
        tk.Button(frow, text='📂', bg=C['folder_bg'], fg='white',
                  relief='flat', bd=0, cursor='hand2', font=('Arial', 10),
                  command=lambda v=folder_var: self._browse_folder(v),
                  ).pack(side='right', padx=2)

        # Dải phân cách đáy
        tk.Frame(card, bg=C['sep'], height=1).pack(fill='x', side='bottom')

        self.selected.append(entry)
        self._p2_scroll.scroll_bottom()
        self._set_status(f"Added: {lora['name']}", 'ok')

    def _clone_card(self, entry: dict):
        """Chèn thêm 1 card cùng lora ngay bên dưới card này."""
        self._add_to_panel2(entry['lora'], after_card=entry['card'])

    def _toggle_custom_prompt(self, entry: dict):
        if entry['use_default'].get():
            entry['custom_frame'].pack_forget()
        else:
            entry['custom_frame'].pack(fill='x', pady=(4, 0))

    def _remove_card(self, entry: dict):
        entry['card'].destroy()
        self.selected = [s for s in self.selected if s is not entry]

    @staticmethod
    def _browse_folder(var: tk.StringVar):
        path = filedialog.askdirectory()
        if path:
            var.set(path)

    # ── PANEL 3 ───────────────────────────────────────────────

    def _build_panel3(self, parent: tk.Frame):
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        hdr = tk.Frame(parent, bg=C['p3'])
        hdr.grid(row=0, column=0, sticky='ew', padx=6, pady=(8, 2))
        tk.Label(hdr, text="Output", bg=C['p3'],
                 fg=C['txt_dark'], font=FONT['title']).pack(side='left', padx=8)
        tk.Button(hdr, text="  Copy  ", font=FONT['normal'],
                  bg=C['copy_btn'], fg='white', relief='flat', bd=0,
                  padx=10, pady=4, cursor='hand2',
                  command=self._copy_output,
                  ).pack(side='right', padx=6)

        tf = tk.Frame(parent, bg=C['p3'])
        tf.grid(row=1, column=0, sticky='nsew', padx=6, pady=(0, 6))
        tf.grid_rowconfigure(0, weight=1)
        tf.grid_columnconfigure(0, weight=1)

        self._out_text = tk.Text(
            tf, wrap='word', state='disabled',
            bg=C['p3_text'], fg=C['txt_dark'],
            insertbackground=C['txt_dark'],
            relief='flat', font=FONT['mono'], bd=6,
            selectbackground='#8B5E3C', selectforeground='white',
        )
        sb = ttk.Scrollbar(tf, orient='vertical', command=self._out_text.yview)
        self._out_text.configure(yscrollcommand=sb.set)
        self._out_text.grid(row=0, column=0, sticky='nsew')
        sb.grid(row=0, column=1, sticky='ns')

    def _set_output(self, raw: str):
        self._raw_output = raw
        self._reapply_breast()

    def _reapply_breast(self):
        if not self._raw_output:
            return
        text = lp.replace_breast_size(self._raw_output, self.breast_var.get())
        self._out_text.configure(state='normal')
        self._out_text.delete('1.0', 'end')
        self._out_text.insert('1.0', text)
        self._out_text.configure(state='disabled')

    def _copy_output(self):
        content = self._out_text.get('1.0', 'end').strip()
        if content:
            self.root.clipboard_clear()
            self.root.clipboard_append(content)
            self._set_status("Copied to clipboard", 'ok')

    # ──────────────────────────────────────────────────────────
    # PIPELINE PROCESSING
    # ──────────────────────────────────────────────────────────

    def _process_all(self):
        valid = [s for s in self.selected if s['folder_var'].get().strip()]
        if not valid:
            self._set_status("No LoRAs have folder paths entered", 'err')
            return
        self._set_status(f"Processing {len(valid)} entry…", 'info')
        # Đọc custom text trong main thread trước khi tạo background thread
        for s in valid:
            if not s['use_default'].get():
                w = s.get('custom_widget')
                s['_custom_cache'] = w.get('1.0', 'end').strip() if w else ''
        threading.Thread(target=self._run_pipeline, args=(valid,), daemon=True).start()

    def _run_pipeline(self, entries: list):
        all_results: List[str] = []
        total = len(entries)

        for idx, entry in enumerate(entries, 1):
            lora = entry['lora']
            name = lora['name']
            self._after_status(f"[{idx}/{total}] {name}…", 'info')

            # Xác định prompt
            if entry['use_default'].get():
                prompt = lp.build_lora_prompt(name, lora['weight'], lora['activation'])
            else:
                custom = entry.get('_custom_cache', '').strip()
                if not custom:
                    self._after_status(f"[{idx}/{total}] {name}: custom prompt rỗng — bỏ qua", 'err')
                    continue
                prompt = lp.build_lora_prompt(name, lora['weight'], custom)

            folder = Path(entry['folder_var'].get().strip())
            if not folder.exists():
                self._after_status(f"[{idx}/{total}] {name}: folder not found", 'err')
                continue

            ok, msg = lp.run_tag_enhancer(folder)
            self._after_status(f"[{idx}/{total}] {name}: tag_enhancer — {msg}", 'ok' if ok else 'err')
            if not ok:
                continue

            ok, msg, char_file = lp.process_character_txt(folder, prompt)
            self._after_status(f"[{idx}/{total}] {name}: {msg}", 'ok' if ok else 'err')
            if not ok or char_file is None:
                continue

            try:
                content = char_file.read_text(encoding='utf-8').strip()
                if content:
                    n = len([l for l in content.splitlines() if l.strip()])
                    self.root.after(0, lambda e=entry, n=n: e['line_count_var'].set(f"{n} dòng"))
                    all_results.append(content)
            except Exception as e:
                self._after_status(f"[{idx}/{total}] read error: {e}", 'err')

        final = SEPARATOR.join(all_results)
        self.root.after(0, lambda: self._set_output(final))
        self._after_status(f"Done — {len(all_results)}/{total} → Panel 3", 'ok')

    # ──────────────────────────────────────────────────────────
    # HELPERS
    # ──────────────────────────────────────────────────────────

    def _set_status(self, msg: str, level: str = 'info'):
        colour = {'ok': C['ok'], 'err': C['err'], 'info': C['info']}.get(level, C['txt_dim'])
        self.status_var.set(msg)
        self._status_lbl.configure(fg=colour)

    def _after_status(self, msg: str, level: str = 'info'):
        self.root.after(0, lambda m=msg, lv=level: self._set_status(m, lv))

    # ──────────────────────────────────────────────────────────
    def run(self):
        self.root.mainloop()


if __name__ == '__main__':
    app = LoRABrowser()
    app.run()
