from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
from pathlib import Path
from threading import Lock
import os
import re
import sys
import uuid

from PIL import Image

try:
    import pillow_avif  # noqa: F401
except ImportError:
    pass

DEFAULT_FOLDER = r"D:\dataset\manhua\voluyen\làm ngay\Hua Qing Si-skin2"
RENDER_SUFFIX = "_rendered"

CONVERT_EXTS = {".webp", ".avif", ".jpg", ".jpeg"}
SUPPORTED_EXTS = CONVERT_EXTS | {".png"}
MAX_WORKERS = min(32, (os.cpu_count() or 4) * 2)
PNG_SAVE_OPTIONS = {"format": "PNG", "compress_level": 1}
MIN_NUMERIC_PAD_WIDTH = 3
LARGE_FOLDER_PAD_THRESHOLD = 1000
LARGE_FOLDER_PAD_WIDTH = 4

print_lock = Lock()
RENDER_PATTERN = re.compile(re.escape(RENDER_SUFFIX), re.IGNORECASE)
NUMERIC_STEM_PATTERN = re.compile(r"^[+-]?\d+$")


def resolve_folder() -> Path:
    if len(sys.argv) > 1:
        return Path(sys.argv[1])
    return Path(DEFAULT_FOLDER)


def remove_rendered_from_stem(stem: str) -> str:
    cleaned = RENDER_PATTERN.sub("", stem)
    return cleaned if cleaned else stem


def cleanup_rendered_names(root: Path) -> tuple[int, int]:
    renamed = 0
    errors = 0
    all_files = [file_path for file_path in root.rglob("*") if file_path.is_file()]

    for file_path in all_files:
        if not file_path.exists():
            continue

        if RENDER_SUFFIX not in file_path.stem.lower():
            continue

        new_stem = remove_rendered_from_stem(file_path.stem)
        new_path = file_path.with_name(f"{new_stem}{file_path.suffix}")

        if new_path == file_path:
            continue

        if new_path.exists():
            print(f"RENAME ERROR: target exists -> {new_path.name}")
            errors += 1
            continue

        try:
            file_path.rename(new_path)
            renamed += 1
            print(f"RENAME CLEAN: {file_path.name} -> {new_path.name}")
        except Exception as exc:
            print(f"RENAME ERROR: {file_path.name} - {exc}")
            errors += 1

    return renamed, errors


def build_output_path(file_path: Path) -> Path:
    stem = remove_rendered_from_stem(file_path.stem)
    return file_path.with_name(f"{stem}.png")


def should_process(file_path: Path) -> bool:
    if not file_path.is_file():
        return False

    ext_lower = file_path.suffix.lower()
    if ext_lower not in SUPPORTED_EXTS:
        return False

    # Skip files that already match final output naming convention.
    if ext_lower == ".png" and file_path.stem.lower().endswith(RENDER_SUFFIX):
        return False

    return True


def collect_files(root: Path) -> list[Path]:
    return [file_path for file_path in root.rglob("*") if should_process(file_path)]


def normalize_numeric_png_order(root: Path) -> tuple[int, int]:
    """
    Rename numeric PNG filenames with zero-padding so lexicographic readers
    still consume them in numeric order: 00, 01, 02 ... 10, 11.
    """
    renamed = 0
    errors = 0
    by_parent: dict[Path, list[Path]] = defaultdict(list)

    for file_path in root.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() == ".png":
            by_parent[file_path.parent].append(file_path)

    for parent, files in by_parent.items():
        numeric_files = [p for p in files if NUMERIC_STEM_PATTERN.fullmatch(p.stem)]
        if len(numeric_files) < 2:
            continue

        current_max_digits = max(len(p.stem.lstrip("+-")) for p in numeric_files)
        pad_width = max(current_max_digits, MIN_NUMERIC_PAD_WIDTH)

        # Use 4 digits for large folders to keep ordering stable in tools
        # that sort purely by filename string.
        if len(numeric_files) >= LARGE_FOLDER_PAD_THRESHOLD:
            pad_width = max(pad_width, LARGE_FOLDER_PAD_WIDTH)

        planned: list[tuple[Path, Path]] = []
        seen_destinations: set[Path] = set()
        source_paths = set(numeric_files)
        has_conflict = False

        for src in numeric_files:
            sign = src.stem[0] if src.stem and src.stem[0] in "+-" else ""
            digits = src.stem[1:] if sign else src.stem
            target_stem = f"{sign}{digits.zfill(pad_width)}"
            dst = src.with_name(f"{target_stem}{src.suffix}")

            if src == dst:
                continue

            if dst in seen_destinations:
                print(f"ORDER ERROR: duplicate target name -> {dst.name}")
                errors += 1
                has_conflict = True
                break

            if dst.exists() and dst not in source_paths:
                print(f"ORDER ERROR: target exists -> {dst.name}")
                errors += 1
                has_conflict = True
                break

            planned.append((src, dst))
            seen_destinations.add(dst)

        if has_conflict or not planned:
            continue

        temp_moves: list[tuple[Path, Path]] = []
        move_failed = False

        for src, dst in planned:
            tmp = src.with_name(f".__order_tmp__{uuid.uuid4().hex}{src.suffix}")
            try:
                src.rename(tmp)
                temp_moves.append((tmp, dst))
            except Exception as exc:
                print(f"ORDER ERROR: {src.name} - {exc}")
                errors += 1
                move_failed = True
                break

        if move_failed:
            for tmp, dst in temp_moves:
                original = next((s for s, d in planned if d == dst), None)
                if original and tmp.exists():
                    try:
                        tmp.rename(original)
                    except Exception as rollback_exc:
                        print(f"ORDER ROLLBACK ERROR: {tmp.name} - {rollback_exc}")
                        errors += 1
            continue

        for tmp, dst in temp_moves:
            try:
                tmp.rename(dst)
                renamed += 1
                print(f"ORDER FIX: {tmp.name} -> {dst.name}")
            except Exception as exc:
                print(f"ORDER ERROR: {dst.name} - {exc}")
                errors += 1

    return renamed, errors


def process_file(index: int, total: int, file_path: Path) -> tuple[bool, str]:
    try:
        if not file_path.exists():
            return False, f"[{index}/{total}] SKIP: {file_path.name} (missing)"

        png_path = build_output_path(file_path)
        same_target = str(file_path).lower() == str(png_path).lower()

        if png_path.exists() and not same_target:
            return False, f"[{index}/{total}] ERROR: target exists -> {png_path.name}"

        if file_path.suffix.lower() == ".png":
            file_path.rename(png_path)
            return True, f"[{index}/{total}] RENAME: {file_path.name} -> {png_path.name}"

        with Image.open(file_path) as img:
            final_img = img if img.mode == "RGBA" else img.convert("RGBA")
            final_img.save(png_path, **PNG_SAVE_OPTIONS)
            if final_img is not img:
                final_img.close()

        file_path.unlink()
        return True, f"[{index}/{total}] OK: {file_path.name} -> {png_path.name}"
    except Exception as exc:
        return False, f"[{index}/{total}] ERROR: {file_path.name} - {exc}"


def main() -> int:
    folder = resolve_folder()

    if not folder.exists():
        print(f"Folder not found: {folder}")
        print("Usage: python changefiletopng_v2.py <folder_path>")
        return 1

    renamed, rename_errors = cleanup_rendered_names(folder)
    if renamed or rename_errors:
        print(f"\nCleanup names: renamed={renamed}, errors={rename_errors}\n")

    all_files = collect_files(folder)

    if not all_files:
        print("No matching files found.")
        return 0

    print(f"Found {len(all_files)} files. Converting with {MAX_WORKERS} workers...\n")

    total_success = 0
    total_errors = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(process_file, index, len(all_files), file_path): file_path
            for index, file_path in enumerate(all_files, 1)
        }

        for future in as_completed(futures):
            success, message = future.result()
            with print_lock:
                print(message)

            if success:
                total_success += 1
            else:
                total_errors += 1

    order_renamed, order_errors = normalize_numeric_png_order(folder)
    if order_renamed or order_errors:
        print(f"\nOrder normalize: renamed={order_renamed}, errors={order_errors}")
    total_errors += order_errors

    print("\n" + "=" * 50)
    print(f"Success: {total_success}")
    print(f"Errors:  {total_errors}")
    print("Done.")
    return 0 if total_errors == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
