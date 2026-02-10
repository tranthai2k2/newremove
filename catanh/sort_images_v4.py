#!/usr/bin/env python3
"""
Sắp xếp Ảnh v4 - Full Features
✅ Drag & Drop Insert (kéo 5 lên 2 → 1,5,2,3,4)
✅ Xem thông tin ảnh chi tiết
✅ Thêm ảnh mới (trước/sau)
✅ TXT metadata tự động
Chạy: python sort_images_v4.py
"""

import os
import re
import sys
import json
import webbrowser
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import time
from base64 import b64encode
from datetime import datetime
import shutil
from PIL import Image

# ============================================================================
# HÀM SẮP XẾP (Backend)
# ============================================================================

def natural_sort_key(filename: str):
    """Sắp xếp thông minh - hiểu số"""
    parts = []
    for part in re.split(r'(\d+)', filename):
        if part.isdigit():
            parts.append(int(part))
        else:
            parts.append(part.lower())
    return tuple(parts)

def get_images_in_folder(folder_path: str, sort_method: str = 'natural'):
    """Lấy danh sách ảnh với metadata"""
    if not os.path.isdir(folder_path):
        return {'error': f'Folder không tồn tại: {folder_path}'}
    
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    images_data = []
    
    try:
        for filename in os.listdir(folder_path):
            filepath = os.path.join(folder_path, filename)
            
            if not os.path.isfile(filepath):
                continue
            if Path(filename).suffix.lower() not in image_extensions:
                continue
            
            stat = os.stat(filepath)
            size_mb = round(stat.st_size / (1024 * 1024), 2)
            
            images_data.append({
                'name': filename,
                'size_mb': size_mb,
                'size_bytes': stat.st_size,
                'path': filepath
            })
    except Exception as e:
        return {'error': str(e)}
    
    # Sắp xếp
    if sort_method == 'name':
        images_data.sort(key=lambda x: x['name'])
    elif sort_method == 'natural':
        images_data.sort(key=lambda x: natural_sort_key(x['name']))
    elif sort_method == 'time':
        images_data.sort(key=lambda x: os.path.getmtime(x['path']), reverse=True)
    elif sort_method == 'size':
        images_data.sort(key=lambda x: x['size_bytes'], reverse=True)
    
    # Loại bỏ 'path' khỏi response
    for img in images_data:
        del img['path']
    
    return {
        'success': True,
        'folder': folder_path,
        'total': len(images_data),
        'sort_method': sort_method,
        'images': images_data
    }

def get_image_info(folder_path: str, filename: str):
    """Lấy thông tin chi tiết ảnh"""
    try:
        filename = os.path.basename(filename)
        filepath = os.path.join(folder_path, filename)
        
        if not os.path.isfile(filepath):
            return {'error': 'File không tồn tại'}
        
        stat = os.stat(filepath)
        size_mb = round(stat.st_size / (1024 * 1024), 2)
        size_kb = round(stat.st_size / 1024, 2)
        
        # Lấy thời gian
        created_time = datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
        modified_time = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        
        # Lấy kích thước ảnh (pixels)
        try:
            img = Image.open(filepath)
            width, height = img.size
            pixels_info = f"{width}x{height} px"
        except:
            pixels_info = "N/A"
        
        return {
            'success': True,
            'filename': filename,
            'filepath': filepath,
            'size_mb': size_mb,
            'size_kb': size_kb,
            'size_bytes': stat.st_size,
            'created_time': created_time,
            'modified_time': modified_time,
            'pixels': pixels_info
        }
    except Exception as e:
        return {'error': str(e)}

def get_image_preview(folder_path: str, filename: str):
    """Lấy ảnh preview dưới dạng base64"""
    try:
        filename = os.path.basename(filename)
        filepath = os.path.join(folder_path, filename)
        
        if not os.path.isfile(filepath):
            return {'error': 'File không tồn tại'}
        
        with open(filepath, 'rb') as f:
            image_data = f.read()
        
        b64_data = b64encode(image_data).decode('utf-8')
        
        ext = Path(filename).suffix.lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp',
            '.webp': 'image/webp'
        }
        mime_type = mime_types.get(ext, 'image/jpeg')
        
        return {
            'success': True,
            'data': f'data:{mime_type};base64,{b64_data}',
            'filename': filename
        }
    except Exception as e:
        return {'error': str(e)}

def create_metadata_txt(filepath: str, index: int, total: int, original_name: str = ''):
    """Tạo file TXT metadata cho ảnh"""
    try:
        basename = os.path.splitext(filepath)[0]
        txt_path = basename + '.txt'
        
        stat = os.stat(filepath)
        size_mb = round(stat.st_size / (1024 * 1024), 2)
        size_kb = round(stat.st_size / 1024, 2)
        
        mod_time = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        filename = os.path.basename(filepath)
        
        content = f"""==============================================
THÔNG TIN ẢNH
==============================================

📌 VỊ TRÍ:        {index}/{total}
🖼️  TÊN FILE:      {filename}
💾 KÍCH THƯỚC:    {size_mb} MB ({size_kb} KB)
📅 NGÀY SỬA:      {mod_time}
📝 TÊN GỐC:       {original_name if original_name else 'N/A'}

==============================================
Tạo bởi: Image Sorter v4
Ngày tạo TXT: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
==============================================
"""
        
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True
    except Exception as e:
        print(f"Lỗi tạo TXT: {e}")
        return False

def add_image_file(folder_path: str, source_file: str, insert_after_index: int = -1):
    """Thêm ảnh từ file nguồn vào folder (trước/sau ảnh)"""
    try:
        if not os.path.isfile(source_file):
            return {'error': 'File nguồn không tồn tại'}
        
        if not os.path.isdir(folder_path):
            return {'error': 'Folder không tồn tại'}
        
        filename = os.path.basename(source_file)
        dest_file = os.path.join(folder_path, filename)
        
        if os.path.exists(dest_file):
            return {'error': f'File {filename} đã tồn tại trong folder'}
        
        shutil.copy2(source_file, dest_file)
        
        return {
            'success': True,
            'filename': filename,
            'message': f'✅ Đã thêm {filename}'
        }
    except Exception as e:
        return {'error': str(e)}

def apply_rename_files(folder_path: str, old_names: list, new_names: list):
    """Rename file + tạo TXT metadata"""
    if len(old_names) != len(new_names):
        return {'error': 'Số lượng file không khớp'}
    
    if not os.path.isdir(folder_path):
        return {'error': f'Folder không tồn tại: {folder_path}'}
    
    try:
        renamed_count = 0
        txt_created = 0
        failed = []
        
        # BƯỚC 1: Rename tất cả thành tên tạm
        temp_mapping = {}
        for i, old_name in enumerate(old_names):
            old_path = os.path.join(folder_path, old_name)
            temp_name = f"__TEMP_{i}__"
            temp_path = os.path.join(folder_path, temp_name)
            
            if os.path.exists(old_path):
                try:
                    os.rename(old_path, temp_path)
                    temp_mapping[temp_name] = (old_name, new_names[i])
                except Exception as e:
                    failed.append(f"{old_name}: {str(e)}")
        
        # BƯỚC 2: Rename từ tạm sang mới + tạo TXT
        for temp_name, (old_name, new_name) in temp_mapping.items():
            temp_path = os.path.join(folder_path, temp_name)
            new_path = os.path.join(folder_path, new_name)
            
            try:
                os.rename(temp_path, new_path)
                renamed_count += 1
                
                index = list(temp_mapping.keys()).index(temp_name) + 1
                total = len(new_names)
                if create_metadata_txt(new_path, index, total, old_name):
                    txt_created += 1
                    
            except Exception as e:
                failed.append(f"{old_name} → {new_name}: {str(e)}")
                try:
                    if os.path.exists(temp_path):
                        os.rename(temp_path, os.path.join(folder_path, old_name))
                except:
                    pass
        
        if failed:
            return {
                'success': False,
                'error': f'Lỗi rename {len(failed)} file',
                'details': failed,
                'renamed': renamed_count,
                'txt_created': txt_created
            }
        
        return {
            'success': True,
            'renamed': renamed_count,
            'txt_created': txt_created,
            'message': f'✅ Đã rename {renamed_count} file + tạo {txt_created} file TXT'
        }
    
    except Exception as e:
        return {'error': f'Lỗi hệ thống: {str(e)}'}

# ============================================================================
# HTTP SERVER
# ============================================================================

class ImageSorterHandler(SimpleHTTPRequestHandler):
    """HTTP Handler cho web UI"""
    
    def do_GET(self):
        """Xử lý GET request"""
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML_CONTENT.encode('utf-8'))
        else:
            super().do_GET()
    
    def do_POST(self):
        """Xử lý POST request (API)"""
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        
        try:
            data = json.loads(body.decode('utf-8'))
            
            if self.path == '/api/images':
                folder = data.get('folder', './test_images')
                sort_method = data.get('sort_method', 'natural')
                result = get_images_in_folder(folder, sort_method)
                
            elif self.path == '/api/preview':
                folder = data.get('folder', './test_images')
                filename = data.get('filename', '')
                result = get_image_preview(folder, filename)
            
            elif self.path == '/api/info':
                folder = data.get('folder', './test_images')
                filename = data.get('filename', '')
                result = get_image_info(folder, filename)
            
            elif self.path == '/api/apply-rename':
                folder = data.get('folder', './test_images')
                old_names = data.get('old_names', [])
                new_names = data.get('new_names', [])
                result = apply_rename_files(folder, old_names, new_names)
                
            elif self.path == '/api/export':
                folder = data.get('folder', './test_images')
                images = data.get('images', [])
                content = f"Danh sách ảnh từ: {folder}\n"
                content += f"Thời gian: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                content += f"Tổng số: {len(images)}\n"
                content += "="*60 + "\n\n"
                for i, img in enumerate(images, 1):
                    content += f"{i}. {img['name']}\n   Kích thước: {img['size_mb']} MB\n\n"
                result = {'success': True, 'content': content, 'count': len(images)}
                
            else:
                result = {'error': 'API không tồn tại'}
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
    
    def log_message(self, format, *args):
        """Giảm log spam"""
        pass

# ============================================================================
# HTML CONTENT
# ============================================================================

HTML_CONTENT = '''<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🖼️ Sắp xếp Ảnh v4 - Insert Mode</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        html, body {
            width: 100%;
            height: 100%;
            overflow-x: hidden;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 0;
            margin: 0;
        }
        .container {
            width: 100%;
            height: 100%;
            max-width: 100%;
            margin: 0 auto;
            background: white;
            border-radius: 0;
            box-shadow: none;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
            flex-shrink: 0;
        }
        .header h1 {
            font-size: clamp(1.5em, 4vw, 2.2em);
            margin-bottom: 8px;
        }
        .header p {
            font-size: clamp(0.85em, 2.5vw, 0.95em);
            opacity: 0.9;
        }
        .toolbar {
            padding: 12px 16px;
            background: #f8f9fa;
            border-bottom: 1px solid #e0e0e0;
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            align-items: center;
            flex-shrink: 0;
        }
        .toolbar input,
        .toolbar select {
            padding: 8px 12px;
            border: 2px solid #e0e0e0;
            border-radius: 6px;
            font-size: clamp(0.85em, 2vw, 0.95em);
        }
        .toolbar input {
            flex: 1;
            min-width: 150px;
        }
        .toolbar input:focus,
        .toolbar select:focus {
            outline: none;
            border-color: #667eea;
        }
        .btn {
            padding: 8px 16px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 6px;
            font-weight: 600;
            cursor: pointer;
            white-space: nowrap;
            transition: all 0.3s;
            font-size: clamp(0.8em, 1.8vw, 0.9em);
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 16px rgba(102, 126, 234, 0.3);
        }
        .btn.secondary {
            background: #6c757d;
        }
        .btn.secondary:hover {
            box-shadow: 0 8px 16px rgba(108, 117, 125, 0.3);
        }
        .btn.danger {
            background: #dc3545;
        }
        .btn.danger:hover {
            box-shadow: 0 8px 16px rgba(220, 53, 69, 0.3);
        }
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        .stats {
            padding: 12px 16px;
            background: white;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
            gap: 8px;
            flex-shrink: 0;
            border-bottom: 1px solid #e0e0e0;
        }
        .stat-box {
            background: #f8f9fa;
            padding: 10px 8px;
            border-radius: 6px;
            border-left: 3px solid #667eea;
            text-align: center;
        }
        .stat-box h3 {
            color: #666;
            font-size: clamp(0.7em, 1.2vw, 0.8em);
            margin-bottom: 4px;
            text-transform: uppercase;
            font-weight: 600;
        }
        .stat-box .value {
            font-size: clamp(1.2em, 2.5vw, 1.6em);
            font-weight: 700;
            color: #667eea;
            line-height: 1;
        }
        .error {
            background: #fee;
            color: #c33;
            padding: 10px 16px;
            border-bottom: 2px solid #c33;
            display: none;
            font-size: clamp(0.85em, 1.8vw, 0.95em);
            flex-shrink: 0;
        }
        .success {
            background: #efe;
            color: #3c3;
            padding: 10px 16px;
            border-bottom: 2px solid #3c3;
            display: none;
            font-size: clamp(0.85em, 1.8vw, 0.95em);
            flex-shrink: 0;
        }
        .content {
            padding: 16px;
            flex: 1;
            overflow-y: auto;
            overflow-x: hidden;
            min-height: 200px;
        }
        .gallery {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(clamp(130px, 18vw, 180px), 1fr));
            gap: clamp(10px, 1.5vw, 16px);
            margin-bottom: 16px;
        }
        .gallery-item {
            position: relative;
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            cursor: grab;
            transition: all 0.3s;
            border: 3px solid transparent;
            aspect-ratio: 1;
        }
        .gallery-item:hover {
            transform: translateY(-4px);
            box-shadow: 0 12px 24px rgba(0,0,0,0.15);
            border-color: #667eea;
        }
        .gallery-item.dragging {
            opacity: 0.6;
            cursor: grabbing;
            background: #f0f0ff;
        }
        .gallery-item.drag-over {
            border-color: #667eea;
            background: #f0f0ff;
            transform: scale(1.01);
        }
        .image-wrapper {
            width: 100%;
            height: 100%;
            overflow: hidden;
            background: #f0f0f0;
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
        }
        .image-wrapper img {
            width: 100%;
            height: 100%;
            object-fit: contain;
        }
        .image-number {
            position: absolute;
            top: 6px;
            right: 6px;
            background: rgba(102, 126, 234, 0.9);
            color: white;
            width: 28px;
            height: 28px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: clamp(0.75em, 1.2vw, 0.85em);
            transition: all 0.2s;
        }
        .gallery-item.drag-over .image-number {
            background: rgba(118, 75, 162, 0.95);
            transform: scale(1.1);
        }
        .image-menu {
            position: absolute;
            top: 6px;
            left: 6px;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 6px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            display: none;
            z-index: 100;
            max-width: 140px;
        }
        .gallery-item:hover .image-menu {
            display: block;
        }
        .menu-item {
            padding: 6px 10px;
            border: none;
            background: none;
            cursor: pointer;
            width: 100%;
            text-align: left;
            font-size: clamp(0.7em, 1vw, 0.8em);
            transition: all 0.2s;
            border-bottom: 1px solid #eee;
            white-space: nowrap;
        }
        .menu-item:last-child {
            border-bottom: none;
        }
        .menu-item:hover {
            background: #f0f0f0;
        }
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #999;
        }
        .empty-state p {
            font-size: clamp(0.95em, 2.5vw, 1.1em);
            margin-bottom: 20px;
        }
        .footer {
            background: #f8f9fa;
            padding: 10px 16px;
            text-align: center;
            color: #666;
            border-top: 1px solid #e0e0e0;
            flex-shrink: 0;
            font-size: clamp(0.8em, 1.5vw, 0.85em);
        }
        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 35px;
            height: 35px;
            animation: spin 1s linear infinite;
            margin: 40px auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.9);
        }
        .modal.show {
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .modal-content {
            background: white;
            padding: clamp(15px, 4vw, 25px);
            border-radius: 10px;
            max-width: 90%;
            max-height: 85vh;
            overflow: auto;
            position: relative;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        .modal-header {
            margin-bottom: 15px;
            padding-bottom: 12px;
            border-bottom: 2px solid #e0e0e0;
        }
        .modal-header h2 {
            color: #333;
            margin-bottom: 8px;
            font-size: clamp(1.1em, 3.5vw, 1.6em);
        }
        .modal-body {
            font-size: clamp(0.9em, 1.8vw, 1em);
            color: #666;
            margin-bottom: 20px;
            line-height: 1.6;
        }
        .modal-footer {
            display: flex;
            gap: 10px;
            justify-content: flex-end;
        }
        .modal-footer .btn {
            min-width: 100px;
        }

        .preview-modal {
            display: none;
            position: fixed;
            z-index: 999;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.9);
        }
        .preview-modal.show {
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .preview-content {
            background: white;
            padding: clamp(15px, 4vw, 25px);
            border-radius: 10px;
            max-width: 90%;
            max-height: 85vh;
            overflow: auto;
            position: relative;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        .modal-close {
            position: absolute;
            right: 12px;
            top: 12px;
            font-size: 26px;
            font-weight: bold;
            cursor: pointer;
            color: #999;
            background: none;
            border: none;
            padding: 0;
            width: 28px;
            height: 28px;
        }
        .modal-close:hover {
            color: #333;
        }
        .preview-header {
            margin-bottom: 15px;
            padding-bottom: 12px;
            border-bottom: 2px solid #e0e0e0;
        }
        .preview-header h2 {
            color: #333;
            word-break: break-all;
            margin-bottom: 8px;
            font-size: clamp(1.1em, 3.5vw, 1.6em);
        }
        .preview-info {
            font-size: clamp(0.8em, 1.5vw, 0.9em);
            color: #666;
            line-height: 1.8;
        }
        .preview-info p {
            margin: 6px 0;
        }
        .preview-image {
            text-align: center;
            margin: 15px 0;
        }
        .preview-image img {
            max-width: 100%;
            max-height: 55vh;
            border-radius: 6px;
            box-shadow: 0 8px 20px rgba(0,0,0,0.2);
        }

        .info-grid {
            display: grid;
            gap: 12px;
        }
        .info-row {
            display: grid;
            grid-template-columns: 120px 1fr;
            gap: 10px;
            padding: 8px;
            background: #f8f9fa;
            border-radius: 4px;
        }
        .info-label {
            font-weight: 600;
            color: #667eea;
        }
        .info-value {
            color: #333;
            word-break: break-all;
        }

        @media (max-width: 768px) {
            body {
                padding: 0;
            }
            .toolbar {
                flex-direction: column;
                gap: 6px;
            }
            .toolbar input,
            .toolbar select {
                width: 100%;
            }
            .gallery {
                grid-template-columns: repeat(auto-fill, minmax(clamp(110px, 22vw, 150px), 1fr));
            }
            .stats {
                grid-template-columns: repeat(3, 1fr);
            }
        }

        @media (max-width: 480px) {
            .gallery {
                grid-template-columns: repeat(auto-fill, minmax(clamp(95px, 25vw, 130px), 1fr));
                gap: clamp(8px, 1vw, 12px);
            }
            .header {
                padding: 15px;
            }
            .content {
                padding: 12px;
            }
            .toolbar, .stats, .footer {
                padding: 10px 12px;
            }
            .modal-footer {
                flex-direction: column;
            }
            .modal-footer .btn {
                width: 100%;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🖼️ Sắp xếp Ảnh v4</h1>
            <p>Kéo thả (Insert) | Info | Thêm | Apply (TXT)</p>
        </div>

        <div class="toolbar">
            <input id="folderPath" placeholder="Đường dẫn folder ảnh" value="./test_images">
            <select id="sortMethod">
                <option value="natural">📊 Thông minh</option>
                <option value="name">🔤 A-Z</option>
                <option value="time">📅 Thời gian</option>
                <option value="size">📦 Kích thước</option>
            </select>
            <button class="btn" onclick="loadImages()">🔍 Tải</button>
            <button class="btn secondary" onclick="resetOrder()" id="resetBtn" style="display:none;">🔄 Reset</button>
            <button class="btn secondary" onclick="exportList()" id="exportBtn" style="display:none;">📥 Export</button>
            <button class="btn danger" onclick="showApplyModal()" id="applyBtn" style="display:none;">⚡ Apply</button>
        </div>

        <div id="error" class="error"></div>
        <div id="success" class="success"></div>
        <div id="stats" class="stats"></div>

        <div class="content">
            <div id="result"></div>
        </div>

        <div class="footer">
            <p>✨ Insert Mode (kéo 5 lên 2 → 1,5,2,3,4) | Info | Thêm | Apply</p>
        </div>
    </div>

    <!-- Modal Apply -->
    <div id="applyModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2>⚠️ Xác nhận Apply</h2>
            </div>
            <div class="modal-body">
                <p><strong>Bạn sắp rename tất cả file ảnh!</strong></p>
                <p>Hệ thống sẽ:</p>
                <ul style="margin-left:20px; margin-top:8px;">
                    <li>✅ Đổi tên <span id="applyCount">0</span> file ảnh</li>
                    <li>✅ Tạo <span id="applyCount">0</span> file TXT metadata</li>
                </ul>
                <p style="margin-top:12px;">Folder: <code style="background:#f0f0f0; padding:8px; border-radius:4px; display:inline-block;">
                    <span id="applyFolder"></span>
                </code></p>
                <p style="color:#c33; margin-top:15px;">🔐 Backup trước!</p>
            </div>
            <div class="modal-footer">
                <button class="btn secondary" onclick="closeApplyModal()">❌ Hủy</button>
                <button class="btn danger" onclick="confirmApplyRename()">✅ Apply</button>
            </div>
        </div>
    </div>

    <!-- Modal Preview/Info -->
    <div id="previewModal" class="preview-modal">
        <div class="preview-content">
            <button class="modal-close" onclick="closePreview()">✕</button>
            <div class="preview-header">
                <h2 id="previewName"></h2>
            </div>
            <div class="preview-info" id="previewInfo"></div>
            <div class="preview-image" id="previewImageDiv"></div>
        </div>
    </div>

    <script>
        let currentFolder = '';
        let currentImages = [];
        let originalOrder = [];
        let imageCache = {};
        let draggedFromIndex = -1;

        async function loadImages() {
            const folder = document.getElementById('folderPath').value.trim();
            const method = document.getElementById('sortMethod').value;
            
            if (!folder) {
                showError('Vui lòng nhập đường dẫn folder');
                return;
            }
            
            currentFolder = folder;
            imageCache = {};
            const resultEl = document.getElementById('result');
            resultEl.innerHTML = '<div class="spinner"></div>';
            document.getElementById('error').style.display = 'none';
            document.getElementById('success').style.display = 'none';
            
            try {
                const response = await fetch('/api/images', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ folder: folder, sort_method: method })
                });
                const data = await response.json();
                
                if (data.error) {
                    showError(data.error);
                    resultEl.innerHTML = '';
                } else {
                    currentImages = data.images;
                    originalOrder = JSON.parse(JSON.stringify(data.images));
                    await displayGallery();
                    displayStats(data);
                    document.getElementById('exportBtn').style.display = 'inline-block';
                    document.getElementById('applyBtn').style.display = 'inline-block';
                    document.getElementById('resetBtn').style.display = 'inline-block';
                }
            } catch (e) {
                showError('Lỗi: ' + e);
                resultEl.innerHTML = '';
            }
        }

        async function displayGallery() {
            const resultEl = document.getElementById('result');
            
            if (currentImages.length === 0) {
                resultEl.innerHTML = '<div class="empty-state"><p>Không tìm thấy ảnh nào</p></div>';
                return;
            }
            
            let html = '<div class="gallery">';
            
            for (let i = 0; i < currentImages.length; i++) {
                const img = currentImages[i];
                const cachedImg = imageCache[img.name] || '';
                html += `
                    <div class="gallery-item" draggable="true" 
                         ondragstart="dragStart(event, ${i})" 
                         ondragover="dragOver(event)" 
                         ondrop="drop(event, ${i})"
                         ondragleave="dragLeave(event)">
                        <div class="image-wrapper">
                            <img src="${cachedImg}" alt="${img.name}">
                            <div class="image-number">${i + 1}</div>
                            <div class="image-menu">
                                <button class="menu-item" onclick="showInfo(${i})">ℹ️ Info</button>
                                <button class="menu-item" onclick="previewImage(${i})">👁️ Xem</button>
                                <button class="menu-item" onclick="copyName('${img.name}', this)">📋 Copy</button>
                            </div>
                        </div>
                    </div>
                `;
            }
            
            html += '</div>';
            resultEl.innerHTML = html;
            
            for (let i = 0; i < currentImages.length; i++) {
                if (!imageCache[currentImages[i].name]) {
                    loadImagePreview(i);
                }
            }
        }

        async function loadImagePreview(index) {
            const img = currentImages[index];
            try {
                const response = await fetch('/api/preview', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        folder: currentFolder, 
                        filename: img.name 
                    })
                });
                const data = await response.json();
                
                if (data.success) {
                    imageCache[img.name] = data.data;
                    const imgs = document.querySelectorAll('.gallery-item img');
                    if (imgs[index]) {
                        imgs[index].src = data.data;
                    }
                }
            } catch (e) {
                console.error('Lỗi load preview:', e);
            }
        }

        function dragStart(e, index) {
            draggedFromIndex = index;
            e.target.closest('.gallery-item').classList.add('dragging');
            e.dataTransfer.effectAllowed = 'move';
        }

        function dragOver(e) {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
            e.target.closest('.gallery-item')?.classList.add('drag-over');
        }

        function dragLeave(e) {
            e.target.closest('.gallery-item')?.classList.remove('drag-over');
        }

        function drop(e, toIndex) {
            e.preventDefault();
            const targetItem = e.target.closest('.gallery-item');
            const draggedItem = document.querySelector('.gallery-item.dragging');
            
            if (draggedItem && draggedFromIndex !== -1 && draggedFromIndex !== toIndex) {
                // Lấy phần tử bị kéo
                const moved = currentImages.splice(draggedFromIndex, 1)[0];
                
                // Tính lại index nếu kéo từ trên xuống
                let insertIndex = toIndex;
                if (draggedFromIndex < toIndex) {
                    insertIndex = toIndex - 1;
                }
                
                // Chèn vào vị trí mới
                currentImages.splice(insertIndex, 0, moved);
                
                displayGallery().then(() => {
                    showSuccess('Đã thay đổi vị trí!');
                });
            }
            
            draggedItem?.classList.remove('dragging');
            targetItem?.classList.remove('drag-over');
            draggedFromIndex = -1;
        }

        function displayStats(data) {
            const labels = {
                'natural': '📊 Thông minh',
                'name': '🔤 A-Z',
                'time': '📅 Thời gian',
                'size': '📦 Kích thước'
            };
            
            const totalSize = getTotalSize(data.images);
            
            document.getElementById('stats').innerHTML = `
                <div class="stat-box"><h3>Tổng</h3><div class="value">${data.total}</div></div>
                <div class="stat-box"><h3>Kiểu</h3><div class="value" style="font-size:clamp(0.9em, 1.3vw, 1em);">${labels[data.sort_method]}</div></div>
                <div class="stat-box"><h3>Dung lượng</h3><div class="value">${totalSize}</div></div>
            `;
        }

        async function showInfo(index) {
            const img = currentImages[index];
            
            try {
                const response = await fetch('/api/info', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        folder: currentFolder, 
                        filename: img.name 
                    })
                });
                const data = await response.json();
                
                if (data.success) {
                    let html = `
                        <div class="info-grid">
                            <div class="info-row">
                                <div class="info-label">📌 Vị trí:</div>
                                <div class="info-value">${index + 1}/${currentImages.length}</div>
                            </div>
                            <div class="info-row">
                                <div class="info-label">🖼️ Tên file:</div>
                                <div class="info-value">${data.filename}</div>
                            </div>
                            <div class="info-row">
                                <div class="info-label">📍 Đường dẫn:</div>
                                <div class="info-value">${data.filepath}</div>
                            </div>
                            <div class="info-row">
                                <div class="info-label">💾 Kích thước:</div>
                                <div class="info-value">${data.size_mb} MB (${data.size_kb} KB)</div>
                            </div>
                            <div class="info-row">
                                <div class="info-label">📐 Pixels:</div>
                                <div class="info-value">${data.pixels}</div>
                            </div>
                            <div class="info-row">
                                <div class="info-label">📅 Tạo:</div>
                                <div class="info-value">${data.created_time}</div>
                            </div>
                            <div class="info-row">
                                <div class="info-label">✏️ Sửa:</div>
                                <div class="info-value">${data.modified_time}</div>
                            </div>
                        </div>
                    `;
                    
                    document.getElementById('previewName').textContent = data.filename;
                    document.getElementById('previewInfo').innerHTML = html;
                    document.getElementById('previewImageDiv').innerHTML = '';
                    document.getElementById('previewModal').classList.add('show');
                } else {
                    showError('Lỗi: ' + data.error);
                }
            } catch (e) {
                showError('Lỗi info: ' + e);
            }
        }

        async function previewImage(index) {
            const img = currentImages[index];
            
            if (imageCache[img.name]) {
                showPreviewImage(img.name, index, imageCache[img.name]);
                return;
            }
            
            try {
                const response = await fetch('/api/preview', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        folder: currentFolder, 
                        filename: img.name 
                    })
                });
                const data = await response.json();
                
                if (data.success) {
                    imageCache[img.name] = data.data;
                    showPreviewImage(data.filename, index, data.data);
                } else {
                    showError('Không load được ảnh: ' + data.error);
                }
            } catch (e) {
                showError('Lỗi preview: ' + e);
            }
        }

        function showPreviewImage(filename, index, imageData) {
            const img = currentImages[index];
            document.getElementById('previewName').textContent = filename;
            document.getElementById('previewInfo').innerHTML = `
                <p>📦 Kích thước: <strong>${img.size_mb} MB</strong></p>
                <p>🔢 Vị trí: <strong>${index + 1}/${currentImages.length}</strong></p>
            `;
            document.getElementById('previewImageDiv').innerHTML = `<img src="${imageData}" alt="Preview">`;
            document.getElementById('previewModal').classList.add('show');
        }

        function closePreview() {
            document.getElementById('previewModal').classList.remove('show');
        }

        function getTotalSize(images) {
            const bytes = images.reduce((s, i) => s + i.size_bytes, 0);
            if (bytes > 1024*1024*1024) return (bytes/(1024*1024*1024)).toFixed(2) + ' GB';
            if (bytes > 1024*1024) return (bytes/(1024*1024)).toFixed(2) + ' MB';
            if (bytes > 1024) return (bytes/1024).toFixed(2) + ' KB';
            return bytes + ' B';
        }

        function copyName(text, btn) {
            navigator.clipboard.writeText(text).then(() => {
                const orig = btn.textContent;
                btn.textContent = '✅';
                setTimeout(() => {
                    btn.textContent = orig;
                }, 1500);
            });
        }

        async function resetOrder() {
            currentImages = JSON.parse(JSON.stringify(originalOrder));
            await displayGallery();
            showSuccess('Đã khôi phục thứ tự gốc!');
        }

        async function exportList() {
            if (currentImages.length === 0) {
                showError('Không có ảnh để export');
                return;
            }
            
            try {
                const response = await fetch('/api/export', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ folder: currentFolder, images: currentImages })
                });
                const data = await response.json();
                
                if (data.error) {
                    showError(data.error);
                } else {
                    const element = document.createElement("a");
                    element.setAttribute("href", "data:text/plain;charset=utf-8," + encodeURIComponent(data.content));
                    element.setAttribute("download", "danh_sach_anh.txt");
                    element.style.display = "none";
                    document.body.appendChild(element);
                    element.click();
                    document.body.removeChild(element);
                    showSuccess('✅ Export ' + data.count + ' ảnh');
                }
            } catch (e) {
                showError('Lỗi export: ' + e);
            }
        }

        function showApplyModal() {
            if (currentImages.length === 0) {
                showError('Không có ảnh để apply');
                return;
            }
            
            document.getElementById('applyCount').textContent = currentImages.length;
            document.getElementById('applyFolder').textContent = currentFolder;
            document.getElementById('applyModal').classList.add('show');
        }

        function closeApplyModal() {
            document.getElementById('applyModal').classList.remove('show');
        }

        async function confirmApplyRename() {
            const oldNames = originalOrder.map(img => img.name);
            const newNames = currentImages.map(img => img.name);
            
            document.getElementById('applyBtn').disabled = true;
            document.getElementById('applyBtn').textContent = '⏳ Đang xử lý...';
            
            try {
                const response = await fetch('/api/apply-rename', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        folder: currentFolder,
                        old_names: oldNames,
                        new_names: newNames
                    })
                });
                const data = await response.json();
                
                closeApplyModal();
                
                if (data.success) {
                    showSuccess(`✅ ${data.message}`);
                    originalOrder = JSON.parse(JSON.stringify(currentImages));
                } else {
                    showError(`❌ ${data.error}`);
                    if (data.details) {
                        console.error('Chi tiết lỗi:', data.details);
                    }
                }
            } catch (e) {
                showError('Lỗi apply: ' + e);
            } finally {
                document.getElementById('applyBtn').disabled = false;
                document.getElementById('applyBtn').textContent = '⚡ Apply';
            }
        }

        function showError(msg) {
            const el = document.getElementById('error');
            el.textContent = msg;
            el.style.display = 'block';
        }

        function showSuccess(msg) {
            const el = document.getElementById('success');
            el.textContent = msg;
            el.style.display = 'block';
            setTimeout(() => el.style.display = 'none', 3000);
        }

        document.getElementById('folderPath').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') loadImages();
        });

        document.getElementById('applyModal').addEventListener('click', (e) => {
            if (e.target === document.getElementById('applyModal')) {
                closeApplyModal();
            }
        });

        document.getElementById('previewModal').addEventListener('click', (e) => {
            if (e.target === document.getElementById('previewModal')) {
                closePreview();
            }
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                closePreview();
                closeApplyModal();
            }
        });

        window.addEventListener('load', () => loadImages());
    </script>
</body>
</html>'''

# ============================================================================
# MAIN
# ============================================================================

def start_server(port=5000):
    """Khởi động HTTP server"""
    server_address = ('127.0.0.1', port)
    httpd = HTTPServer(server_address, ImageSorterHandler)
    
    print("\n" + "="*60)
    print("🖼️  Sắp xếp Ảnh v4 - Insert Mode + Info + TXT")
    print("="*60)
    print(f"\n✓ Server: http://localhost:{port}")
    print(f"✓ Ctrl+C để dừng")
    print("\n📝 Cài đặt Pillow (nếu chưa có):")
    print("   pip install pillow")
    print("\n")
    
    try:
        time.sleep(1)
        webbrowser.open(f'http://localhost:{port}')
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n✓ Server đã dừng")
        httpd.shutdown()

if __name__ == '__main__':
    port = 5000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except:
            pass
    
    start_server(port)
