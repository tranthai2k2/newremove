from PIL import Image
from pathlib import Path
import os

# Thư mục chứa file WebP
FOLDER = r"D:\zhangyao\1-old\[PIXIV] Noi [810034] [AI Generated] [12]-1280x\7"

folder = Path(FOLDER)

# Tìm file WebP
webp_files = []
for ext in ['*.webp', '*.WEBP']:
    webp_files.extend(list(folder.rglob(ext)))

if not webp_files:
    print("Không có file WebP")
    exit()

for i, webp in enumerate(webp_files, 1):
    try:
        # Kiểm tra file tồn tại
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
        
        print(f"[{i}/{len(webp_files)}] ✅ {webp.name}")
        
    except FileNotFoundError:
        continue  # Skip nếu file không tồn tại
    except PermissionError:
        print(f"[{i}/{len(webp_files)}] ⚠️ {webp.name} - File đang được mở")
    except Exception as e:
        print(f"[{i}/{len(webp_files)}] ❌ {webp.name} - {e}")
