import os
import gc
import time
import json
from PIL import Image
from pathlib import Path
from multiprocessing import freeze_support
from datetime import datetime

FOLDER_PATH = r"D:\prompt_album\ImageAssistant_Batch_Image_Downloader\philiascans.org\The_Evil_Alchemist_Can_t_Handle_His_Own_Experiment_-_Philia_Scans"

SUPPORTED_EXT = (".jpg", ".jpeg", ".png")
CHECK_INTERVAL = 5
LOG_FILE = "metadata_cleaned.json"

def load_cleaned_log():
    """Load danh sách file đã xóa"""
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return set(data.get('cleaned_files', []))
        except:
            return set()
    return set()

def save_cleaned_log(cleaned_files):
    """Lưu danh sách file đã xóa"""
    data = {
        'last_updated': datetime.now().isoformat(),
        'total_cleaned': len(cleaned_files),
        'cleaned_files': sorted(list(cleaned_files))
    }
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def clean_single_image(file_path):
    """Xóa metadata từ 1 ảnh - cực tiết kiệm RAM"""
    try:
        # Mở ảnh
        with Image.open(file_path) as img:
            # Lưu trực tiếp không metadata
            if img.format == 'JPEG':
                img.save(file_path, 'JPEG', quality=90, optimize=True)
            elif img.format == 'PNG':
                img.save(file_path, 'PNG', optimize=True)
            else:
                img.save(file_path)
        return True
    except:
        return False

def clean_all_images(cleaned_files):
    """Xóa metadata từ file CHƯA xóa - tuần tự (tiết kiệm RAM)"""
    path = Path(FOLDER_PATH)
    
    # Generator thay vì list (tiết kiệm RAM!)
    def image_generator():
        seen = set()
        for ext in SUPPORTED_EXT:
            for file in path.rglob(f"*{ext}"):
                file_str = str(file)
                if file_str not in seen:
                    seen.add(file_str)
                    yield file_str
            for file in path.rglob(f"*{ext.upper()}"):
                file_str = str(file)
                if file_str not in seen:
                    seen.add(file_str)
                    yield file_str
    
    processed = 0
    total = 0
    
    # Xử lý file một cái một cái
    for file_path in image_generator():
        # BỎ QUA file đã xóa
        if file_path in cleaned_files:
            continue
        
        total += 1
        
        success = clean_single_image(file_path)
        if success:
            processed += 1
            cleaned_files.add(file_path)
            
            # Save log mỗi 10 file
            if processed % 10 == 0:
                save_cleaned_log(cleaned_files)
        
        # Progress
        print(f"\r✔ [{processed}/{total}]", end="", flush=True)
        
        # Giải phóng memory mỗi 20 file
        if total % 20 == 0:
            gc.collect()
    
    print()
    gc.collect()
    save_cleaned_log(cleaned_files)
    
    return processed, total

def count_images():
    """Đếm ảnh mà không lưu vào RAM"""
    path = Path(FOLDER_PATH)
    count = 0
    
    for ext in SUPPORTED_EXT:
        count += sum(1 for _ in path.rglob(f"*{ext}"))
        count += sum(1 for _ in path.rglob(f"*{ext.upper()}"))
    
    return count

def get_folder_timestamp():
    """Lấy timestamp thay đổi gần nhất"""
    path = Path(FOLDER_PATH)
    max_time = 0
    
    for ext in SUPPORTED_EXT:
        try:
            max_time = max(max_time, max(
                (f.stat().st_mtime for f in path.rglob(f"*{ext}")),
                default=0
            ))
            max_time = max(max_time, max(
                (f.stat().st_mtime for f in path.rglob(f"*{ext.upper()}")),
                default=0
            ))
        except:
            pass
    
    return max_time

def main():
    print("╔" + "═" * 70 + "╗")
    print("║  🚀 ULTRA LIGHT METADATA CLEANER                            ║")
    print("║     (Minimal RAM - Remember & Skip Cleaned Files)            ║")
    print("╚" + "═" * 70 + "╝\n")
    
    print(f"📁 Folder: {FOLDER_PATH}")
    print(f"⏱️  Check every {CHECK_INTERVAL} seconds")
    print(f"📝 Log file: {LOG_FILE}")
    print("Press Ctrl+C to stop\n")
    
    # Load log
    print("Loading memory log...")
    cleaned_files = load_cleaned_log()
    print(f"✅ Found {len(cleaned_files)} files in history\n")
    
    # Initial scan
    print("Scanning initial files...")
    initial_count = count_images()
    last_timestamp = get_folder_timestamp()
    print(f"✅ Found {initial_count} images")
    print(f"🔄 Files not yet cleaned: {initial_count - len(cleaned_files)}\n")
    
    # Clean unclean files on startup
    unclean_count = initial_count - len(cleaned_files)
    if unclean_count > 0:
        print(f"Cleaning {unclean_count} unprocessed files...\n")
        processed, _ = clean_all_images(cleaned_files)
        print(f"✅ Cleaned {processed} files\n")
    
    print("=" * 70)
    print("Waiting for changes...\n")
    
    check_count = 0
    total_cleaned = 0
    
    try:
        while True:
            check_count += 1
            now = datetime.now().strftime("%H:%M:%S")
            
            # Check if folder changed
            current_timestamp = get_folder_timestamp()
            current_count = count_images()
            
            # File thay đổi hoặc có file mới?
            if current_timestamp > last_timestamp or current_count > initial_count:
                new_files_count = current_count - len(cleaned_files)
                
                if new_files_count > 0:
                    print(f"\n[{now}] 🆕 Change detected! ({new_files_count} new files)")
                    print(f"     Cleaning unprocessed images...\n")
                    
                    # Clean only UNCLEAN files
                    processed, total = clean_all_images(cleaned_files)
                    
                    print(f"\n[{now}] ✅ Done: {processed}/{total} cleaned\n")
                    
                    total_cleaned += processed
                else:
                    print(f"[{now}] ✅ All files already cleaned!\n")
                
                initial_count = current_count
                last_timestamp = current_timestamp
                
                print("=" * 70)
                print("Waiting for changes...\n")
            else:
                print(f"[{now}] ⏳ Checking ({current_count} files, {len(cleaned_files)} cleaned)...", end="\r")
            
            time.sleep(CHECK_INTERVAL)
    
    except KeyboardInterrupt:
        print(f"\n\n{'═' * 70}")
        print(f"✋ Stopped!")
        print(f"Total checks: {check_count}")
        print(f"Total cleaned this session: {total_cleaned}")
        print(f"Total files in history: {len(cleaned_files)}")
        print(f"Total files in folder: {current_count}")
        print(f"{'═' * 70}")
        print(f"\n📝 Log saved to: {LOG_FILE}")

if __name__ == "__main__":
    freeze_support()
    main()