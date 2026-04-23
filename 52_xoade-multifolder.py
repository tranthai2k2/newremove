#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
52_xoade-multifolder.py
Chạy 52_xoade.py cho từng subfolder trong một folder cha
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime

# ==================== CẤU HÌNH - SỬA Ở ĐÂY ====================

XOADE_PATH = Path(r"D:\no\52_xoade.py")

PARENT_FOLDER = Path(r"D:\zhangyao\pose-v-2\POSE-MORIAAA")

# ================================================================


def run_xoade_for_folder(folder: Path) -> bool:
    print(f"\n{'─'*60}")
    print(f"📁 Processing: {folder}")
    print(f"{'─'*60}")

    cmd = [sys.executable, str(XOADE_PATH), "--folder", str(folder)]

    try:
        result = subprocess.run(cmd, text=True)
        if result.returncode == 0:
            print(f"✅ DONE: {folder.name}")
            return True
        else:
            print(f"❌ FAILED: {folder.name} (exit code {result.returncode})")
            return False
    except Exception as e:
        print(f"❌ ERROR: {folder.name} → {e}")
        return False


def main():
    print("=" * 60)
    print(" 52_XOADE MULTI-FOLDER RUNNER")
    print("=" * 60)
    print(f" Script       : {XOADE_PATH}")
    print(f" Parent Folder: {PARENT_FOLDER}")
    print(f" Start        : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    if not XOADE_PATH.exists():
        print(f"\n❌ Không tìm thấy script: {XOADE_PATH}")
        sys.exit(1)

    if not PARENT_FOLDER.exists():
        print(f"\n❌ Folder không tồn tại: {PARENT_FOLDER}")
        sys.exit(1)

    subfolders = sorted([f for f in PARENT_FOLDER.iterdir() if f.is_dir()])

    if not subfolders:
        print(f"\n⚠️  Không có subfolder nào trong: {PARENT_FOLDER}")
        sys.exit(0)

    print(f"\n📋 Tìm thấy {len(subfolders)} subfolder(s):")
    for i, sf in enumerate(subfolders, 1):
        print(f"   {i:2}. {sf.name}")

    print(f"\n▶️  Bắt đầu xử lý...")

    success, failed, failed_list = 0, 0, []

    for i, folder in enumerate(subfolders, 1):
        print(f"\n[{i}/{len(subfolders)}]", end="")
        if run_xoade_for_folder(folder):
            success += 1
        else:
            failed += 1
            failed_list.append(folder.name)

    print(f"\n{'='*60}")
    print(f" KẾT QUẢ BATCH")
    print(f"{'='*60}")
    print(f" Tổng  : {len(subfolders)} folder(s)")
    print(f" ✅ OK : {success}")
    print(f" ❌ Lỗi: {failed}")
    if failed_list:
        print(f"\n Folder bị lỗi:")
        for name in failed_list:
            print(f"   • {name}")
    print(f"\n End: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()