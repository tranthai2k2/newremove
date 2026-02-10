import os

# Đường dẫn thư mục chứa file cần xử lý và danh sách các tag không mong muốn
folder_to_process = r"D:\zhangyao\1-old\[PIXIV] Noi [810034] [AI Generated] [12]-1280x\83"






#------------------------------------------------------------------------------------------
unwanted_tags_folder = r"./wantremove"

# Tạo danh sách các tag không mong muốn từ các file .txt trong folder 'unwanted_tags_folder'
unwanted_tags = set()

for filename in os.listdir(unwanted_tags_folder):
    if filename.endswith('.txt'):
        file_path = os.path.join(unwanted_tags_folder, filename)
        with open(file_path, 'r', encoding='utf-8') as file:
            line = file.readline().strip()
            if line:
                if ',' in line:
                    split_tags = [t.strip() for t in line.split(',') if t.strip()]
                    unwanted_tags.update(split_tags)
                else:
                    unwanted_tags.add(line)

# Duyệt qua các file .txt trong thư mục cần xử lý
for filename in os.listdir(folder_to_process):
    if filename.endswith('.txt'):
        file_path = os.path.join(folder_to_process, filename)

        # Đọc nội dung file
        with open(file_path, 'r', encoding='utf-8') as file:
            line = file.readline().strip()
            if line:
                # Tách các tag trong file
                tags = [tag.strip() for tag in line.split(',') if tag.strip()]

                # Lọc bỏ các tag không mong muốn
                filtered_tags = [tag for tag in tags if tag not in unwanted_tags]

                # Ghi lại các tag đã lọc vào file mới
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(', '.join(filtered_tags))

        print(f"Đã xử lý file: {filename}")

print("Hoàn thành việc lọc các tag không mong muốn.")
