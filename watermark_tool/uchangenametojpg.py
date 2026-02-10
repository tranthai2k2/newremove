import os
import unicodedata
from PIL import Image

# --- Hàm bỏ dấu tiếng Việt và định dạng tên ---
def normalize_name(name, use_underscore=True):
    nfkd_form = unicodedata.normalize('NFKD', name)
    no_accent = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    no_accent = no_accent.lower()
    if use_underscore:
        return no_accent.replace(" ", "_")
    else:
        return no_accent.replace(" ", "")

# --- Thư mục gốc ---
folder = r"D:\zhangyao\1-old\[PIXIV] Noi [810034] [AI Generated] [13]-1280x\New folder"

# Lấy tên folder cuối
base_name = os.path.basename(folder)
# Chọn định dạng tên: True = dùng dấu "_" , False = liền chữ
new_base = normalize_name(base_name, use_underscore=True)

# Tạo thư mục dataset
dataset_folder = os.path.join(folder, "dataset")
os.makedirs(dataset_folder, exist_ok=True)

# Duyệt file
count = 1
for file in os.listdir(folder):
    file_path = os.path.join(folder, file)

    if os.path.isfile(file_path):
        try:
            # Mở và convert sang JPG
            img = Image.open(file_path).convert("RGB")
            new_name = f"{new_base}_{count}.jpg"
            new_path = os.path.join(dataset_folder, new_name)
            img.save(new_path, "JPEG")
            print(f"Đã chuyển: {file} -> {new_name}")
            count += 1
        except Exception as e:
            print(f"Bỏ qua {file}: {e}")
