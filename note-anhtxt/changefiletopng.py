from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock
import os
import sys

from PIL import Image

try:
    import pillow_avif
except ImportError:
    pass

FOLDER = r"D:\zhangyao\1-old\all-prompt\prompt moriaa\[moriAAA] Shokugeki no Soma [AI Generated]-1280x\New folder"
folder = Path(FOLDER)

# .png (lowercase) = đích, bỏ qua
# .PNG / .Png ... = rename về .png (không re-encode)
# .webp/.avif/.jpg/.jpeg (mọi kiểu hoa thường) = convert sang .png
CONVERT_EXTS = {".webp", ".avif", ".jpg", ".jpeg"}
SUPPORTED_EXTS = CONVERT_EXTS | {".png"}
MAX_WORKERS = min(32, (os.cpu_count() or 4) * 2)
PNG_SAVE_OPTIONS = {"format": "PNG", "compress_level": 1}

print_lock = Lock()


def collect_files(root: Path) -> list[Path]:
    return [
        file_path
        for file_path in root.rglob("*")
        if file_path.is_file()
        and file_path.suffix != ".png"
        and file_path.suffix.lower() in SUPPORTED_EXTS
    ]


def process_file(index: int, total: int, file_path: Path) -> tuple[bool, str]:
    try:
        if not file_path.exists():
            return False, f"[{index}/{total}] ⏭️ bỏ qua: {file_path.name} (không còn tồn tại)"

        png_path = file_path.with_suffix(".png")

        if file_path.suffix.lower() == ".png":
            if png_path.exists() and png_path != file_path:
                return False, f"[{index}/{total}] ❌ {file_path.parent.name}/{file_path.name} - Đích đã tồn tại"

            file_path.rename(png_path)
            return True, f"[{index}/{total}] 🔤 rename: {file_path.name} -> {png_path.name}"

        with Image.open(file_path) as img:
            final_img = img if img.mode == "RGBA" else img.convert("RGBA")
            final_img.save(png_path, **PNG_SAVE_OPTIONS)

            if final_img is not img:
                final_img.close()

        file_path.unlink()
        return True, f"[{index}/{total}] ✅ {file_path.parent.name}/{file_path.name} -> {png_path.name}"
    except Exception as exc:
        return False, f"[{index}/{total}] ❌ {file_path.parent.name}/{file_path.name} - Lỗi: {exc}"


def main() -> int:
    all_files = collect_files(folder)

    if not all_files:
        print("Không tìm thấy file phù hợp.")
        return 0

    print(f"Tìm thấy {len(all_files)} file. Bắt đầu chuyển đổi với {MAX_WORKERS} luồng...\n")

    total_converted = 0
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
                total_converted += 1
            else:
                total_errors += 1

    print(f"\n{'=' * 50}")
    print(f"✅ Thành công: {total_converted} file")
    print(f"❌ Lỗi:       {total_errors} file")
    print("Hoàn tất!")
    return 0 if total_errors == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
