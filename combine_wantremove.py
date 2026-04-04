#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nạp tất cả tag từ thư mục wantremove vào 1 file alltag-enchange.txt trong wantkeep.
- Đọc tất cả .txt trong wantremove
- Tách tag theo dấu phẩy hoặc xuống dòng
- Loại bỏ trùng, sắp xếp
- Lưu vào wantkeep/alltag-enchange.txt
"""

from pathlib import Path

WANTREMOVE = Path(r".\wantremove")
WANTKEEP = Path(r".\wantkeep")
OUTPUT_FILE = WANTKEEP / "alltag-enchange.txt"

def main():
    WANTKEEP.mkdir(exist_ok=True)

    all_tags = set()
    txt_files = list(WANTREMOVE.glob("*.txt"))

    if not txt_files:
        print(f"Không tìm thấy file .txt nào trong {WANTREMOVE}")
        return

    for txt_file in sorted(txt_files):
        content = txt_file.read_text(encoding="utf-8", errors="ignore")
        for line in content.splitlines():
            for tag in line.split(","):
                tag = tag.strip()
                if tag:
                    all_tags.add(tag)

    sorted_tags = sorted(all_tags, key=lambda t: t.lower())

    OUTPUT_FILE.write_text(", ".join(sorted_tags), encoding="utf-8")

    print(f"Đã nạp {len(txt_files)} file từ {WANTREMOVE}")
    print(f"Tổng số tag unique: {len(sorted_tags)}")
    print(f"Đã lưu vào: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
