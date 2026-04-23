#!/usr/bin/env python3
"""
Merge many images into one contact sheet image.

Examples:
  python merge_thumbnails.py "D:\\images" "D:\\images\\merged_square.jpg" --layout square
  python merge_thumbnails.py "D:\\images" "D:\\images\\merged_portrait.jpg" --layout portrait --only-vertical
  python merge_thumbnails.py "D:\\images" "D:\\images\\merged_landscape.jpg" --layout landscape --orientation horizontal
"""

from __future__ import annotations

import argparse
import math
import re
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
from typing import Iterable, List, Sequence

from PIL import Image, ImageColor


SUPPORTED_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
ORIENTATION_CHOICES = {"all", "vertical", "horizontal"}


def natural_key(path: Path) -> List[object]:
    parts = re.split(r"(\d+)", path.name.lower())
    key: List[object] = []
    for p in parts:
        if p.isdigit():
            key.append(int(p))
        else:
            key.append(p)
    return key


def list_images(folder: Path, recursive: bool) -> List[Path]:
    iterator: Iterable[Path] = folder.rglob("*") if recursive else folder.glob("*")
    return sorted(
        (p for p in iterator if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS),
        key=natural_key,
    )


def calc_best_columns(
    count: int,
    avg_aspect_ratio: float,
    layout: str,
) -> int:
    if count <= 1:
        return 1

    target_ratio = {"square": 1.0, "portrait": 1.5, "landscape": 0.67}[layout]
    best_cols = 1
    best_score = float("inf")

    for cols in range(1, count + 1):
        rows = math.ceil(count / cols)
        estimated_ratio = (rows * avg_aspect_ratio) / cols
        score = abs(estimated_ratio - target_ratio)

        if layout == "portrait" and estimated_ratio < 1.0:
            score += 100.0

        if layout == "landscape" and estimated_ratio > 1.0:
            score += 100.0

        if score < best_score:
            best_score = score
            best_cols = cols

    return best_cols


def resolve_orientation_filter(
    orientation_filter: str,
    only_vertical: bool = False,
    only_horizontal: bool = False,
) -> str:
    resolved = orientation_filter.strip().lower()
    if resolved not in ORIENTATION_CHOICES:
        raise ValueError(
            "--orientation must be one of: all, vertical, horizontal"
        )

    if only_vertical and only_horizontal:
        raise ValueError("Cannot use both --only-vertical and --only-horizontal.")

    if only_vertical and resolved == "horizontal":
        raise ValueError(
            "Conflicting filters: --orientation horizontal with --only-vertical."
        )
    if only_horizontal and resolved == "vertical":
        raise ValueError(
            "Conflicting filters: --orientation vertical with --only-horizontal."
        )

    if only_vertical:
        return "vertical"
    if only_horizontal:
        return "horizontal"
    return resolved


def load_and_resize(
    image_paths: Sequence[Path],
    thumb_width: int,
    orientation_filter: str,
) -> List[Image.Image]:
    loaded: List[tuple[Image.Image, int, int]] = []

    for path in image_paths:
        with Image.open(path) as im:
            w, h = im.size
            if orientation_filter == "vertical" and h <= w:
                continue
            if orientation_filter == "horizontal" and w <= h:
                continue
            loaded.append((im.convert("RGB"), w, h))

    if not loaded:
        return []

    target_width = thumb_width if thumb_width > 0 else max(w for _, w, _ in loaded)
    resized: List[Image.Image] = []
    for rgb, w, h in loaded:
        # Keep original size if already within limit to avoid blur from upscaling.
        if w <= target_width:
            resized.append(rgb)
            continue
        new_h = max(1, round((h / w) * target_width))
        resized.append(rgb.resize((target_width, new_h), Image.Resampling.LANCZOS))

    return resized


def build_contact_sheet(
    thumbs: Sequence[Image.Image],
    columns: int,
    padding: int,
    bg_color: str,
) -> Image.Image:
    if not thumbs:
        raise ValueError("No images available to build contact sheet.")

    columns = max(1, min(columns, len(thumbs)))
    rows = math.ceil(len(thumbs) / columns)
    thumb_width = max(img.width for img in thumbs)
    bg_rgb = ImageColor.getrgb(bg_color)

    row_heights: List[int] = []
    for row in range(rows):
        start = row * columns
        row_items = thumbs[start : start + columns]
        row_heights.append(max(img.height for img in row_items))

    canvas_w = columns * thumb_width + padding * (columns + 1)
    canvas_h = sum(row_heights) + padding * (rows + 1)
    canvas = Image.new("RGB", (canvas_w, canvas_h), bg_rgb)

    y = padding
    for row in range(rows):
        row_h = row_heights[row]
        start = row * columns
        row_items = thumbs[start : start + columns]

        for col, img in enumerate(row_items):
            x = padding + col * (thumb_width + padding)
            paste_x = x + (thumb_width - img.width) // 2
            paste_y = y + (row_h - img.height) // 2
            canvas.paste(img, (paste_x, paste_y))

        y += row_h + padding

    return canvas


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Merge many images into one square/portrait/landscape contact sheet."
    )
    parser.add_argument(
        "input_dir",
        type=Path,
        nargs="?",
        help="Folder containing input images.",
    )
    parser.add_argument(
        "output",
        type=Path,
        nargs="?",
        help="Output image path, e.g. output.jpg",
    )
    parser.add_argument(
        "--layout",
        choices=["square", "portrait", "landscape"],
        default="square",
        help="square: near 1:1, portrait: taller than wide, landscape: wider than tall",
    )
    parser.add_argument(
        "--columns",
        type=int,
        default=0,
        help="Number of columns. 0 = auto-calculate from layout.",
    )
    parser.add_argument(
        "--thumb-width",
        type=int,
        default=0,
        help="Max width for each image tile. 0 = keep original size (no downscale).",
    )
    parser.add_argument(
        "--padding",
        type=int,
        default=8,
        help="Space between images and outer edge.",
    )
    parser.add_argument(
        "--bg-color",
        default="#111111",
        help="Background color (hex or color name).",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Include images from subfolders.",
    )
    parser.add_argument(
        "--only-vertical",
        action="store_true",
        help="Use only vertical images (legacy shortcut for --orientation vertical).",
    )
    parser.add_argument(
        "--only-horizontal",
        action="store_true",
        help="Use only horizontal images (legacy shortcut for --orientation horizontal).",
    )
    parser.add_argument(
        "--orientation",
        choices=["all", "vertical", "horizontal"],
        default="all",
        help="Filter input images by orientation.",
    )
    parser.add_argument(
        "--quality",
        type=int,
        default=95,
        help="JPEG quality (used when output is .jpg/.jpeg).",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Open UI mode.",
    )
    return parser.parse_args()


def merge_images(
    input_dir: Path,
    output: Path,
    layout: str = "square",
    columns: int = 0,
    thumb_width: int = 0,
    padding: int = 8,
    bg_color: str = "#111111",
    recursive: bool = False,
    orientation_filter: str = "all",
    only_vertical: bool = False,
    only_horizontal: bool = False,
    quality: int = 95,
) -> dict:
    if not input_dir.exists() or not input_dir.is_dir():
        raise ValueError(f"Input directory not found: {input_dir}")
    if thumb_width < 0:
        raise ValueError("--thumb-width must be >= 0")
    if 0 < thumb_width < 8:
        raise ValueError("--thumb-width must be 0 or >= 8")
    if padding < 0:
        raise ValueError("--padding must be >= 0")

    resolved_orientation = resolve_orientation_filter(
        orientation_filter=orientation_filter,
        only_vertical=only_vertical,
        only_horizontal=only_horizontal,
    )

    image_paths = list_images(input_dir, recursive)
    if not image_paths:
        raise ValueError("No image files found in input directory.")

    thumbs = load_and_resize(image_paths, thumb_width, resolved_orientation)
    if not thumbs:
        if resolved_orientation == "vertical":
            raise ValueError("No vertical images found (height > width).")
        if resolved_orientation == "horizontal":
            raise ValueError("No horizontal images found (width > height).")
        raise ValueError("No images available after processing.")

    avg_aspect = sum(img.height / img.width for img in thumbs) / len(thumbs)
    actual_columns = columns if columns > 0 else calc_best_columns(
        count=len(thumbs),
        avg_aspect_ratio=avg_aspect,
        layout=layout,
    )

    sheet = build_contact_sheet(
        thumbs=thumbs,
        columns=actual_columns,
        padding=padding,
        bg_color=bg_color,
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    ext = output.suffix.lower()

    if ext in {".jpg", ".jpeg"}:
        sheet.save(
            output,
            quality=max(1, min(quality, 100)),
            optimize=True,
            subsampling=0,
        )
    else:
        sheet.save(output)

    rows = math.ceil(len(thumbs) / max(1, actual_columns))
    return {
        "output": output,
        "images": len(thumbs),
        "layout": layout,
        "orientation": resolved_orientation,
        "columns": actual_columns,
        "rows": rows,
        "width": sheet.width,
        "height": sheet.height,
    }


def run_gui() -> int:
    root = tk.Tk()
    root.title("Merge Thumbnails")
    root.geometry("620x280")
    root.resizable(False, False)

    folder_var = tk.StringVar()
    layout_var = tk.StringVar(value="square")
    orientation_var = tk.StringVar(value="vertical")
    recursive_var = tk.BooleanVar(value=False)

    def browse_folder() -> None:
        folder = filedialog.askdirectory(title="Chon folder chua anh")
        if folder:
            folder_var.set(folder)

    def create_thumbnail() -> None:
        folder_text = folder_var.get().strip()
        if not folder_text:
            messagebox.showwarning("Thieu thong tin", "Hay nhap duong dan folder anh.")
            return

        input_dir = Path(folder_text)
        output = input_dir / "thumbnail.jpg"

        try:
            result = merge_images(
                input_dir=input_dir,
                output=output,
                layout=layout_var.get(),
                columns=0,
                thumb_width=0,
                padding=8,
                bg_color="#111111",
                recursive=recursive_var.get(),
                orientation_filter=orientation_var.get(),
                quality=95,
            )
        except Exception as e:
            messagebox.showerror("Loi", str(e))
            return

        status = (
            f"Tao xong: {result['output']}\n"
            f"So anh: {result['images']} | Bo cuc: {result['layout']} | "
            f"Loc: {result['orientation']} | "
            f"{result['columns']} cot x {result['rows']} hang"
        )
        messagebox.showinfo("Thanh cong", status)

    frm = ttk.Frame(root, padding=12)
    frm.pack(fill="both", expand=True)

    ttk.Label(frm, text="Folder chua anh:").grid(row=0, column=0, sticky="w")
    entry = ttk.Entry(frm, textvariable=folder_var, width=60)
    entry.grid(row=1, column=0, padx=(0, 8), sticky="we")
    ttk.Button(frm, text="Browse...", command=browse_folder).grid(row=1, column=1, sticky="e")

    ttk.Label(frm, text="Kieu bo cuc:").grid(row=2, column=0, pady=(12, 4), sticky="w")
    ttk.Combobox(
        frm,
        textvariable=layout_var,
        values=["square", "portrait", "landscape"],
        state="readonly",
        width=15,
    ).grid(row=3, column=0, sticky="w")

    ttk.Label(frm, text="Loc huong anh:").grid(row=4, column=0, pady=(10, 4), sticky="w")
    ttk.Combobox(
        frm,
        textvariable=orientation_var,
        values=["all", "vertical", "horizontal"],
        state="readonly",
        width=15,
    ).grid(row=5, column=0, sticky="w")

    ttk.Checkbutton(frm, text="Lay ca anh trong subfolder", variable=recursive_var).grid(
        row=6,
        column=0,
        pady=(10, 0),
        sticky="w",
    )

    ttk.Button(frm, text="Tao thumbnail.jpg", command=create_thumbnail).grid(
        row=7,
        column=0,
        columnspan=2,
        pady=(14, 0),
        sticky="we",
    )

    frm.columnconfigure(0, weight=1)
    entry.focus_set()
    root.mainloop()
    return 0


def main() -> int:
    args = parse_args()

    if args.gui or (args.input_dir is None and args.output is None):
        return run_gui()

    if args.input_dir is None or args.output is None:
        raise SystemExit("Please provide both input_dir and output, or use --gui.")

    result = merge_images(
        input_dir=args.input_dir,
        output=args.output,
        layout=args.layout,
        columns=args.columns,
        thumb_width=args.thumb_width,
        padding=args.padding,
        bg_color=args.bg_color,
        recursive=args.recursive,
        orientation_filter=args.orientation,
        only_vertical=args.only_vertical,
        only_horizontal=args.only_horizontal,
        quality=args.quality,
    )
    print(f"Done: {result['output']}")
    print(
        f"Images: {result['images']} | Layout: {result['layout']} | Orientation: {result['orientation']} | Columns x Rows: {result['columns']} x {result['rows']} | Size: {result['width']} x {result['height']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
