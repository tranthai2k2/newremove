"""
Module quản lý tags với Tab Viewer và Tag Manager
"""
import os
from pathlib import Path

def load_text_files(folder_path):
    """
    Load tất cả file .txt từ thư mục out_tags

    Args:
        folder_path (str): Đường dẫn folder gốc

    Returns:
        dict: {filename: content} hoặc None nếu lỗi
    """
    out_tags_path = os.path.join(folder_path, "out_tags")

    if not os.path.exists(out_tags_path):
        return None

    txt_files = {}
    for f in sorted(os.listdir(out_tags_path)):
        if f.endswith('.txt'):
            file_path = os.path.join(out_tags_path, f)
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    txt_files[f] = file.read()
            except UnicodeDecodeError:
                try:
                    with open(file_path, 'r', encoding='windows-1252') as file:
                        txt_files[f] = file.read()
                except Exception as e:
                    txt_files[f] = f"⚠️ Lỗi đọc file: {str(e)}"
            except Exception as e:
                txt_files[f] = f"⚠️ Lỗi đọc file: {str(e)}"

    return txt_files if txt_files else None

def save_tags_to_file(output_file, tags_content, mode='append', log_callback=None):
    """
    Lưu tags vào file

    Args:
        output_file (str): Đường dẫn file output
        tags_content (str): Nội dung tags cần lưu
        mode (str): 'append' hoặc 'overwrite'
        log_callback (function): Hàm callback để ghi log

    Returns:
        bool: True nếu thành công, False nếu thất bại
    """
    def log(msg):
        if log_callback:
            log_callback(msg)
        else:
            print(msg, end='')

    if not tags_content.strip():
        log("❌ Không có nội dung tags để lưu\n")
        return False

    try:
        # Tạo thư mục nếu chưa tồn tại
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        if mode == 'overwrite':
            # Ghi đè hoàn toàn
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(tags_content.strip())
            log(f"✅ Đã GHI ĐÈ tags vào: {output_file}\n")
        else:
            # Append (mode mặc định)
            # Đọc nội dung hiện tại
            existing_content = ""
            if os.path.exists(output_file):
                with open(output_file, 'r', encoding='utf-8') as f:
                    existing_content = f.read()

            # Xóa các newline ở cuối (nếu có)
            existing_content = existing_content.rstrip('\n\r')

            # Ghi lại file với nội dung mới được append
            with open(output_file, 'w', encoding='utf-8') as f:
                if existing_content:
                    # Nếu có nội dung cũ, thêm ", " trước nội dung mới
                    f.write(existing_content + ", " + tags_content.strip())
                else:
                    # Nếu file trống, chỉ ghi nội dung mới
                    f.write(tags_content.strip())
            log(f"✅ Đã APPEND tags vào: {output_file}\n")

        log(f"📝 Nội dung: {tags_content.strip()}\n")
        return True

    except Exception as e:
        log(f"❌ Lỗi khi lưu tags: {str(e)}\n")
        return False

def get_file_preview(output_file, max_chars=500):
    """
    Đọc preview nội dung file

    Args:
        output_file (str): Đường dẫn file
        max_chars (int): Số ký tự tối đa hiển thị

    Returns:
        str: Nội dung preview
    """
    try:
        if os.path.exists(output_file):
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if len(content) > max_chars:
                    return "...\n" + content[-max_chars:]
                else:
                    return content
        else:
            return "(File chưa tồn tại)"
    except Exception as e:
        return f"Lỗi đọc file: {str(e)}"

def remove_tags_from_folder(folder_path, log_callback=None):
    """
    Xóa các tags không mong muốn từ tất cả file .txt trong folder
    Dựa trên logic từ 52_xoade.py

    Args:
        folder_path (str): Đường dẫn folder chứa file cần xử lý
        log_callback (function): Hàm callback để ghi log

    Returns:
        bool: True nếu thành công
    """
    def log(msg):
        if log_callback:
            log_callback(msg)
        else:
            print(msg, end='')

    if not os.path.exists(folder_path):
        log(f"❌ Folder không tồn tại: {folder_path}\n")
        return False

    # Đường dẫn tương đối tới wantremove
    unwanted_tags_folder = os.path.join(os.path.dirname(__file__), "..", "wantremove")

    if not os.path.exists(unwanted_tags_folder):
        log(f"❌ Không tìm thấy folder wantremove: {unwanted_tags_folder}\n")
        return False

    log(f"📁 Load tags từ: {unwanted_tags_folder}\n")

    # Tạo danh sách các tag không mong muốn
    unwanted_tags = set()
    for filename in os.listdir(unwanted_tags_folder):
        if filename.endswith('.txt'):
            file_path = os.path.join(unwanted_tags_folder, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    line = file.readline().strip()
                    if line:
                        if ',' in line:
                            split_tags = [t.strip() for t in line.split(',') if t.strip()]
                            unwanted_tags.update(split_tags)
                        else:
                            unwanted_tags.add(line)
            except Exception as e:
                log(f"⚠️ Lỗi đọc {filename}: {e}\n")

    if not unwanted_tags:
        log("⚠️ Không có tags nào để xóa\n")
        return False

    log(f"🗑️ Tìm thấy {len(unwanted_tags)} unwanted tags\n\n")

    # Duyệt qua các file .txt trong thư mục cần xử lý
    processed_count = 0
    for filename in os.listdir(folder_path):
        if filename.endswith('.txt'):
            file_path = os.path.join(folder_path, filename)
            try:
                # Đọc nội dung file
                with open(file_path, 'r', encoding='utf-8') as file:
                    line = file.readline().strip()

                if line:
                    # Tách các tag trong file
                    tags = [tag.strip() for tag in line.split(',') if tag.strip()]

                    # Lọc bỏ các tag không mong muốn
                    filtered_tags = [tag for tag in tags if tag not in unwanted_tags]

                    # Ghi lại các tag đã lọc vào file
                    with open(file_path, 'w', encoding='utf-8') as file:
                        file.write(', '.join(filtered_tags))

                    processed_count += 1
                    log(f"✓ {filename}\n")
            except Exception as e:
                log(f"❌ Lỗi xử lý {filename}: {e}\n")

    log(f"\n✅ Đã xử lý {processed_count} file!\n")
    return True

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 2:
        output_file = sys.argv[1]
        tags_content = sys.argv[2]
        mode = sys.argv[3] if len(sys.argv) > 3 else 'append'
        save_tags_to_file(output_file, tags_content, mode)
    else:
        print("Usage: python code3_tag_manager.py <output_file> <tags_content> [mode]")
