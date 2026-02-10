"""
Module chuyển đổi WebP sang JPG
"""
from PIL import Image
from pathlib import Path
import os

def convert_webp_to_jpg(folder_path, log_callback=None):
    """
    Chuyển đổi tất cả file WebP trong folder sang JPG

    Args:
        folder_path (str): Đường dẫn folder chứa file WebP
        log_callback (function): Hàm callback để ghi log
    """
    def log(msg):
        if log_callback:
            log_callback(msg)
        else:
            print(msg, end='')

    folder = Path(folder_path)

    if not folder.exists():
        log(f"❌ Folder không tồn tại: {folder_path}\n")
        return

    # Tìm file WebP
    webp_files = []
    for ext in ['*.webp', '*.WEBP']:
        webp_files.extend(list(folder.rglob(ext)))

    if not webp_files:
        log("❌ Không có file WebP trong folder này\n")
        return

    log(f"📁 Tìm thấy {len(webp_files)} file WebP\n")

    for i, webp in enumerate(webp_files, 1):
        try:
            if not webp.exists():
                continue

            # Convert
            img = Image.open(webp)
            if img.mode != 'RGB':
                rgb = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                if 'A' in img.mode:
                    rgb.paste(img, mask=img.split()[-1])
                else:
                    rgb.paste(img)
                img = rgb

            jpg = webp.with_suffix('.jpg')
            img.save(jpg, 'JPEG', quality=95, optimize=True)
            img.close()

            # Xóa WebP
            os.remove(str(webp))
            log(f"[{i}/{len(webp_files)}] ✅ {webp.name}\n")

        except FileNotFoundError:
            continue
        except PermissionError:
            log(f"[{i}/{len(webp_files)}] ⚠️ {webp.name} - File đang được mở\n")
        except Exception as e:
            log(f"[{i}/{len(webp_files)}] ❌ {webp.name} - {e}\n")

    log("\n✅ Hoàn thành chuyển đổi WebP to JPG!\n")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        convert_webp_to_jpg(sys.argv[1])
    else:
        print("Usage: python code1_convert_webp.py <folder_path>")
