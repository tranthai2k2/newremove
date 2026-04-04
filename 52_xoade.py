#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import argparse
from pathlib import Path

# ==================== CẤU HÌNH MẶC ĐỊNH ====================

DEFAULT_FOLDER = Path(r"D:\zhangyao\pose-v-2\pose-noi\New folder (5)")

# ============================================================

parser = argparse.ArgumentParser(description="52 XoaDe - Tag Remover")
parser.add_argument(
    "--folder",
    type=Path,
    default=DEFAULT_FOLDER,
    help="Đường dẫn folder cần xử lý (mặc định: {})".format(DEFAULT_FOLDER),
)
args = parser.parse_args()

folder_to_process = args.folder

# ─────────────────────────────────────────────────────────────
unwanted_tags_folder = r"./wantremove"

# Tạo danh sách các tag không mong muốn từ các file .txt trong folder 'wantremove'
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

        with open(file_path, 'r', encoding='utf-8') as file:
            line = file.readline().strip()
            if line:
                tags = [tag.strip() for tag in line.split(',') if tag.strip()]
                filtered_tags = [tag for tag in tags if tag not in unwanted_tags]

                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(', '.join(filtered_tags))

        print(f"Đã xử lý file: {filename}")

print(f"✅ Hoàn thành việc lọc tag trong: {folder_to_process}")