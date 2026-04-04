from PIL import Image
from pathlib import Path
try:
    import pillow_avif
except ImportError:
    pass  # Pillow 9.1+ has built-in AVIF support

ROOT_FOLDER = r"F:\chưa làm\tanhatthuoctinh_Attribute Collection"
root = Path(ROOT_FOLDER)

print(f"Thư mục: {root}")
print(f"Tồn tại: {root.exists()}\n")

# Bỏ qua: .jpg / .jpeg / .png (đã đúng lowercase)
# Rename:  .JPG / .Jpg / .JPEG / .Jpeg → .jpg (không re-encode)
# Convert: .PNG / .Png + .webp / .avif (mọi hoa thường) → .jpg
rename_exts  = {'.jpg', '.jpeg'}   # nếu suffix.lower() khớp nhưng không phải lowercase → rename
convert_exts = {'.png', '.webp', '.avif'}  # luôn re-encode

all_files = [
    f for f in root.rglob("*")
    if f.is_file()
    and f.suffix.lower() in rename_exts | convert_exts
    and f.suffix != f.suffix.lower()  # bỏ qua file đã là lowercase
]

if not all_files:
    print("Không tìm thấy file phù hợp.")
    # Debug: in thử toàn bộ file tìm thấy
    print("\n[DEBUG] Tất cả file trong thư mục:")
    for f in list(root.rglob("*.*"))[:30]:
        print(f"  {f.suffix!r:15} | {f.parent.name}/{f.name}")
    exit()

print(f"Tìm thấy {len(all_files)} file. Bắt đầu chuyển đổi...\n")

total_converted = 0
total_errors = 0

for i, file_path in enumerate(all_files, 1):
    try:
        if not file_path.exists():
            continue

        jpg_path = file_path.with_suffix('.jpg')

        if file_path.suffix.lower() in rename_exts:
            # .JPG / .JPEG → chỉ rename, không re-encode
            file_path.rename(jpg_path)
            print(f"[{i}/{len(all_files)}] 🔤 rename: {file_path.name} -> {jpg_path.name}")
        else:
            # .PNG / .webp / .avif → convert sang jpg
            with Image.open(file_path) as img:
                if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    img_rgba = img.convert("RGBA")
                    background.paste(img_rgba, mask=img_rgba.split()[3])
                    final_img = background
                else:
                    final_img = img.convert("RGB")
                final_img.save(jpg_path, 'JPEG', quality=95, optimize=True)
            file_path.unlink()
            print(f"[{i}/{len(all_files)}] ✅ {file_path.parent.name}/{file_path.name} -> {jpg_path.name}")
        total_converted += 1

    except Exception as e:
        print(f"[{i}/{len(all_files)}] ❌ {file_path.parent.name}/{file_path.name} - Lỗi: {e}")
        total_errors += 1

print(f"\n{'='*50}")
print(f"✅ Thành công: {total_converted} file")
print(f"❌ Lỗi:       {total_errors} file")
print("Hoàn tất!")