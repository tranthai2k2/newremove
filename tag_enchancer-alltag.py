import os
import shutil
from pathlib import Path

def main():
    # Đường dẫn thư mục chính
    root_path = r"F:\prompt\[PIXIV] Noi [810034] [AI Generated] [25]-1280x"
    
    # Kiểm tra đường dẫn tồn tại
    if not os.path.exists(root_path):
        print(f"❌ Không tìm thấy thư mục: {root_path}")
        return
    
    print(f"📁 Output trực tiếp vào root: {root_path}")
    
    # Duyệt qua tất cả các subfolder
    subfolders = [f for f in os.listdir(root_path) 
                  if os.path.isdir(os.path.join(root_path, f))]
    
    print(f"\n🔍 Tìm kiếm trong {len(subfolders)} folder con...\n")
    
    copied_count = 0
    
    for subfolder in subfolders:
        subfolder_path = os.path.join(root_path, subfolder)
        
        # Kiểm tra xem subfolder có chứa folder out_tags không
        out_tags_path = os.path.join(subfolder_path, "out_tags")
        
        if not os.path.exists(out_tags_path) or not os.path.isdir(out_tags_path):
            print(f"⏭️  {subfolder}: Không có folder out_tags")
            continue
        
        # Kiểm tra file addfaceless.txt bên trong out_tags
        addfaceless_file = os.path.join(out_tags_path, "addfaceless.txt")
        
        if not os.path.exists(addfaceless_file):
            print(f"⚠️  {subfolder}: Có out_tags nhưng không có file addfaceless.txt")
            continue
        
        # Nếu tìm thấy file, sao chép và đổi tên
        try:
            # Sao chép file với tên mới: {tên_folder}_addfaceless.txt
            dest_file = os.path.join(root_path, f"{subfolder}_addfaceless.txt")
            shutil.copy2(addfaceless_file, dest_file)
            print(f"✅ Sao chép: {subfolder}_addfaceless.txt")
            copied_count += 1
        except Exception as e:
            print(f"❌ Lỗi khi sao chép {subfolder}_addfaceless.txt: {e}")
    
    print(f"\n{'='*60}")
    print(f"✨ Hoàn thành! Sao chép {copied_count} file")
    print(f"📁 Tất cả file đã được lưu trực tiếp trong root")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
    input("\nNhấn Enter để thoát...")
