import os
from PIL import Image

# Thư mục chứa ảnh
input_folder = r"D:\prompt_album\Love by Mistake\Sylvie_Jaine"

# Lặp qua tất cả file trong thư mục
for filename in os.listdir(input_folder):
    if filename.lower().endswith(".webp"):
        webp_path = os.path.join(input_folder, filename)
        
        # Đổi phần mở rộng thành .jpg
        jpg_filename = os.path.splitext(filename)[0] + ".jpg"
        jpg_path = os.path.join(input_folder, jpg_filename)
        
        # Mở ảnh và lưu lại dưới dạng JPG
        with Image.open(webp_path) as img:
            img = img.convert("RGB")  # JPG không hỗ trợ alpha
            img.save(jpg_path, "JPEG", quality=95)

        # Xóa file gốc .webp
        os.remove(webp_path)

        print(f"Đã chuyển và xóa: {filename} -> {jpg_filename}")
