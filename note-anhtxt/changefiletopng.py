from PIL import Image
from pathlib import Path
try:
    import pillow_avif
except ImportError:
    pass

FOLDER = r"F:\chưa làm\tanhatthuoctinh_Attribute Collection - Copy"
folder = Path(FOLDER)

# .png (lowercase) = đích, bỏ qua
# .PNG / .Png ... = rename về .png (không re-encode)
# .webp/.avif/.jpg/.jpeg (mọi hoa thường) = convert sang .png
convert_exts = {'.webp', '.avif', '.jpg', '.jpeg'}

all_files = [
    f for f in folder.rglob("*")
    if f.is_file() and f.suffix != '.png' and f.suffix.lower() in convert_exts | {'.png'}
]

if not all_files:
    print("Không tìm thấy file phù hợp.")
    exit()

print(f"Tìm thấy {len(all_files)} file. Bắt đầu chuyển đổi...\n")

total_converted = 0
total_errors = 0

for i, file_path in enumerate(all_files, 1):
    try:
        if not file_path.exists():
            continue

        png_path = file_path.with_suffix('.png')

        if file_path.suffix.lower() == '.png':
            # Chỉ rename .PNG → .png, không re-encode
            file_path.rename(png_path)
            print(f"[{i}/{len(all_files)}] 🔤 rename: {file_path.name} -> {png_path.name}")
        else:
            with Image.open(file_path) as img:
                final_img = img.convert("RGBA") if img.mode != "RGBA" else img
                final_img.save(png_path, 'PNG', optimize=True)
            file_path.unlink()
            print(f"[{i}/{len(all_files)}] ✅ {file_path.parent.name}/{file_path.name} -> {png_path.name}")
        total_converted += 1

    except Exception as e:
        print(f"[{i}/{len(all_files)}] ❌ {file_path.parent.name}/{file_path.name} - Lỗi: {e}")
        total_errors += 1

print(f"\n{'='*50}")
print(f"✅ Thành công: {total_converted} file")
print(f"❌ Lỗi:       {total_errors} file")
print("Hoàn tất!")
