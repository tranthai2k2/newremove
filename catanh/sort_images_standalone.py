#!/usr/bin/env python3
"""
Sắp xếp Ảnh - Standalone (Không cần Flask)
Chạy trực tiếp: python sort_images_standalone.py
Hoặc: py sort_images_standalone.py
"""

import os
import re
import sys
import webbrowser
from pathlib import Path
from typing import List, Tuple
from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import urllib.parse
from threading import Thread
import time

# ============================================================================
# HÀM SẮP XẾP (Backend)
# ============================================================================

def natural_sort_key(filename: str) -> Tuple:
    """Sắp xếp thông minh - hiểu số"""
    parts = []
    for part in re.split(r'(\d+)', filename):
        if part.isdigit():
            parts.append(int(part))
        else:
            parts.append(part.lower())
    return tuple(parts)

def get_images_in_folder(folder_path: str, sort_method: str = 'natural') -> dict:
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
    
    return {
        'success': True,
        'folder': folder_path,
        'total': len(images_data),
        'sort_method': sort_method,
        'images': images_data
    }

# ============================================================================
# HTTP SERVER - Tạo Web UI đơn giản
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
        if self.path == '/api/images':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            
            try:
                data = json.loads(body.decode('utf-8'))
                folder = data.get('folder', './test_images')
                sort_method = data.get('sort_method', 'natural')
                
                result = get_images_in_folder(folder, sort_method)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Giảm log spam"""
        pass

# ============================================================================
# HTML CONTENT (Giao diện)
# ============================================================================

HTML_CONTENT = '''<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🖼️ Sắp xếp Ảnh</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 20px;
            text-align: center;
        }
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }
        .content {
            padding: 40px;
        }
        .input-group {
            display: flex;
            gap: 15px;
            margin-bottom: 30px;
            flex-wrap: wrap;
        }
        .input-group input,
        .input-group select {
            padding: 12px 15px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 1em;
        }
        .input-group input {
            flex: 1;
            min-width: 250px;
        }
        .input-group input:focus,
        .input-group select:focus {
            outline: none;
            border-color: #667eea;
        }
        .btn {
            padding: 12px 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            white-space: nowrap;
            transition: all 0.3s;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
        }
        .btn-secondary {
            background: #6c757d;
        }
        .btn-secondary:hover {
            box-shadow: 0 10px 20px rgba(108, 117, 125, 0.4);
        }
        .btn-success {
            background: #28a745;
        }
        .btn-success:hover {
            box-shadow: 0 10px 20px rgba(40, 167, 69, 0.4);
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-box {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        .stat-box h3 {
            color: #666;
            font-size: 0.9em;
            margin-bottom: 10px;
            text-transform: uppercase;
        }
        .stat-box .value {
            font-size: 2em;
            font-weight: 700;
            color: #667eea;
        }
        .error {
            background: #fee;
            color: #c33;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            border-left: 4px solid #c33;
            display: none;
        }
        .sort-info {
            background: #e3f2fd;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            border-left: 4px solid #2196f3;
            color: #1565c0;
            display: none;
        }
        .action-buttons {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        thead {
            background: #f8f9fa;
            border-bottom: 2px solid #e0e0e0;
        }
        th {
            padding: 15px;
            text-align: left;
            font-weight: 600;
            color: #333;
        }
        td {
            padding: 12px 15px;
            border-bottom: 1px solid #e0e0e0;
        }
        tbody tr {
            cursor: grab;
            transition: background 0.2s;
        }
        tbody tr.dragging {
            opacity: 0.5;
            background: #e3f2fd;
        }
        tbody tr:hover {
            background: #f8f9fa;
        }
        tbody tr.drag-over {
            border-top: 3px solid #667eea;
        }
        .filename-cell {
            word-break: break-all;
        }
        .preview-link {
            color: #667eea;
            text-decoration: underline;
            cursor: pointer;
            margin-right: 8px;
        }
        .preview-link:hover {
            color: #764ba2;
        }
        .copy-btn {
            background: #f0f0f0;
            border: 1px solid #ddd;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.85em;
            transition: all 0.2s;
        }
        .copy-btn:hover {
            background: #e0e0e0;
        }
        .copy-btn.copied {
            background: #4caf50;
            color: white;
        }
        /* Modal Preview */
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.8);
            animation: fadeIn 0.3s;
        }
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        .modal-content {
            position: relative;
            background: white;
            margin: auto;
            padding: 0;
            max-width: 90%;
            max-height: 90%;
            top: 50%;
            transform: translateY(-50%);
            border-radius: 8px;
            overflow: auto;
            animation: slideIn 0.3s;
        }
        @keyframes slideIn {
            from { transform: translateY(-100px); opacity: 0; }
            to { transform: translateY(-50%); opacity: 1; }
        }
        .modal-header {
            padding: 20px;
            background: #f8f9fa;
            border-bottom: 1px solid #e0e0e0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .modal-body {
            padding: 20px;
            text-align: center;
        }
        .modal-body img {
            max-width: 100%;
            max-height: 70vh;
            border-radius: 8px;
        }
        .modal-info {
            margin-top: 20px;
            text-align: left;
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            font-size: 0.95em;
        }
        .modal-info p {
            margin: 8px 0;
            color: #666;
        }
        .close-btn {
            font-size: 28px;
            font-weight: bold;
            color: #666;
            cursor: pointer;
            background: none;
            border: none;
            padding: 0;
        }
        .close-btn:hover {
            color: #000;
        }
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #999;
        }
        .footer {
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
            border-top: 1px solid #e0e0e0;
        }
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        @media (max-width: 768px) {
            .input-group { flex-direction: column; }
            .input-group input,
            .input-group select { width: 100%; }
            .action-buttons { flex-direction: column; }
            .btn { width: 100%; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🖼️ Sắp xếp Ảnh</h1>
            <p>Sắp xếp hàng trăm ảnh mà không load vào RAM</p>
        </div>
        <div class="content">
            <div class="input-group">
                <input id="folderPath" placeholder="Nhập đường dẫn folder ảnh" value="./test_images">
                <select id="sortMethod">
                    <option value="natural">📊 Sắp xếp Thông minh (Số)</option>
                    <option value="name">🔤 Sắp xếp A-Z</option>
                    <option value="time">📅 Theo Thời gian</option>
                    <option value="size">📦 Theo Kích thước</option>
                </select>
                <button class="btn" onclick="loadImages()">🔍 Tải</button>
            </div>
            <div id="error" class="error"></div>
            <div id="sortInfo" class="sort-info"></div>
            <div id="stats" class="stats"></div>
            <div id="actionButtons" class="action-buttons" style="display:none;"></div>
            <div id="result"></div>
        </div>
        <div class="footer">
            <p>✨ Preview ảnh | Kéo thả sắp xếp | Export danh sách | Memory: O(n)</p>
        </div>
    </div>

    <!-- Modal Preview -->
    <div id="imageModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2 id="modalTitle">Preview Ảnh</h2>
                <button class="close-btn" onclick="closePreview()">&times;</button>
            </div>
            <div class="modal-body">
                <img id="modalImage" src="" alt="Preview">
                <div class="modal-info">
                    <p><strong>Tên file:</strong> <span id="modalFileName"></span></p>
                    <p><strong>Kích thước:</strong> <span id="modalFileSize"></span></p>
                    <p><strong>Vị trí:</strong> <span id="modalFileIndex"></span></p>
                </div>
            </div>
        </div>
    </div>

    <script>
        let currentImages = [];
        let currentFolder = '';

        function loadImages() {
            const folder = document.getElementById('folderPath').value.trim();
            const method = document.getElementById('sortMethod').value;
            
            if (!folder) {
                showError('Vui lòng nhập đường dẫn folder');
                return;
            }
            
            currentFolder = folder;
            const resultEl = document.getElementById('result');
            resultEl.innerHTML = '<div class="spinner"></div><p style="text-align: center;">Đang tải...</p>';
            document.getElementById('error').style.display = 'none';
            
            fetch('/api/images', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ folder: folder, sort_method: method })
            })
            .then(r => r.json())
            .then(data => {
                if (data.error) {
                    showError(data.error);
                    resultEl.innerHTML = '';
                } else {
                    currentImages = JSON.parse(JSON.stringify(data.images));
                    displayResults(data);
                }
            })
            .catch(e => {
                showError('Lỗi: ' + e);
                resultEl.innerHTML = '';
            });
        }
        
        function showError(msg) {
            const el = document.getElementById('error');
            el.textContent = '❌ ' + msg;
            el.style.display = 'block';
        }
        
        function displayResults(data) {
            const labels = {
                'natural': '📊 Sắp xếp Thông minh (Số)',
                'name': '🔤 Sắp xếp A-Z',
                'time': '📅 Theo Thời gian',
                'size': '📦 Theo Kích thước'
            };
            
            document.getElementById('stats').innerHTML = `
                <div class="stat-box"><h3>Tổng ảnh</h3><div class="value">${data.total}</div></div>
                <div class="stat-box"><h3>Phương pháp</h3><div class="value" style="font-size:1.2em;">${labels[data.sort_method]}</div></div>
                <div class="stat-box"><h3>Dung lượng</h3><div class="value">${getTotalSize(data.images)}</div></div>
            `;
            
            document.getElementById('sortInfo').innerHTML = `✓ Đã sắp xếp ${data.total} ảnh từ: <strong>${data.folder}</strong>`;
            document.getElementById('sortInfo').style.display = 'block';
            
            // Nút hành động
            document.getElementById('actionButtons').innerHTML = `
                <button class="btn btn-success" onclick="exportList()">📥 Export Danh sách</button>
                <button class="btn btn-secondary" onclick="resetOrder()">🔄 Khôi phục Gốc</button>
            `;
            document.getElementById('actionButtons').style.display = 'flex';
            
            if (data.total === 0) {
                document.getElementById('result').innerHTML = '<div class="empty-state"><p>Không tìm thấy ảnh nào</p></div>';
                return;
            }
            
            let html = '<table id="imageTable"><thead><tr><th style="width:50px;">#</th><th>Tên file</th><th style="text-align:right;width:120px;">Kích thước</th></tr></thead><tbody>';
            currentImages.forEach((img, i) => {
                const size = img.size_mb > 0 ? img.size_mb.toFixed(2) + ' MB' : img.size_bytes + ' B';
                html += `<tr draggable="true" data-index="${i}">
                    <td>${i+1}</td>
                    <td class="filename-cell">
                        <span class="preview-link" onclick="previewImage(${i})">📸</span>
                        <span>${img.name}</span>
                        <button class="copy-btn" onclick="copy('${img.name}', this)">📋</button>
                    </td>
                    <td style="text-align:right;">${size}</td>
                </tr>`;
            });
            html += '</tbody></table>';
            document.getElementById('result').innerHTML = html;
            
            attachDragListeners();
        }
        
        function attachDragListeners() {
            const rows = document.querySelectorAll('#imageTable tbody tr');
            rows.forEach(row => {
                row.addEventListener('dragstart', handleDragStart);
                row.addEventListener('dragend', handleDragEnd);
                row.addEventListener('dragover', handleDragOver);
                row.addEventListener('drop', handleDrop);
                row.addEventListener('dragenter', handleDragEnter);
                row.addEventListener('dragleave', handleDragLeave);
            });
        }
        
        let draggedIndex = null;
        
        function handleDragStart(e) {
            draggedIndex = parseInt(e.target.closest('tr').dataset.index);
            e.target.closest('tr').classList.add('dragging');
            e.dataTransfer.effectAllowed = 'move';
        }
        
        function handleDragEnd(e) {
            document.querySelectorAll('#imageTable tbody tr').forEach(r => {
                r.classList.remove('dragging', 'drag-over');
            });
        }
        
        function handleDragOver(e) {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
        }
        
        function handleDragEnter(e) {
            if (e.target.closest('tr') !== e.target.closest('tr').closest('tr')) return;
            e.target.closest('tr')?.classList.add('drag-over');
        }
        
        function handleDragLeave(e) {
            e.target.closest('tr')?.classList.remove('drag-over');
        }
        
        function handleDrop(e) {
            e.preventDefault();
            const targetIndex = parseInt(e.target.closest('tr').dataset.index);
            
            if (draggedIndex !== targetIndex) {
                const draggedItem = currentImages[draggedIndex];
                currentImages.splice(draggedIndex, 1);
                currentImages.splice(targetIndex, 0, draggedItem);
                
                refreshTableNumbers();
            }
        }
        
        function refreshTableNumbers() {
            const rows = document.querySelectorAll('#imageTable tbody tr');
            rows.forEach((row, i) => {
                row.dataset.index = i;
                row.cells[0].textContent = i + 1;
            });
        }
        
        function previewImage(index) {
            const img = currentImages[index];
            const filePath = currentFolder + '/' + img.name;
            
            document.getElementById('modalTitle').textContent = '📸 ' + img.name;
            document.getElementById('modalImage').src = filePath;
            document.getElementById('modalFileName').textContent = img.name;
            document.getElementById('modalFileSize').textContent = img.size_mb > 0 ? img.size_mb.toFixed(2) + ' MB' : img.size_bytes + ' B';
            document.getElementById('modalFileIndex').textContent = (index + 1) + ' / ' + currentImages.length;
            document.getElementById('imageModal').style.display = 'block';
        }
        
        function closePreview() {
            document.getElementById('imageModal').style.display = 'none';
        }
        
        function exportList() {
            let content = 'Danh sách ảnh đã sắp xếp\\n';
            content += '='.repeat(50) + '\\n\\n';
            currentImages.forEach((img, i) => {
                const size = img.size_mb > 0 ? img.size_mb.toFixed(2) + ' MB' : img.size_bytes + ' B';
                content += (i+1) + '. ' + img.name + ' (' + size + ')\\n';
            });
            
            const blob = new Blob([content], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'danh-sach-anh.txt';
            a.click();
            URL.revokeObjectURL(url);
        }
        
        function resetOrder() {
            if (confirm('Khôi phục lại thứ tự sắp xếp ban đầu?')) {
                loadImages();
            }
        }
        
        function getTotalSize(images) {
            const bytes = images.reduce((s, i) => s + i.size_bytes, 0);
            if (bytes > 1024*1024*1024) return (bytes/(1024*1024*1024)).toFixed(2) + ' GB';
            if (bytes > 1024*1024) return (bytes/(1024*1024)).toFixed(2) + ' MB';
            if (bytes > 1024) return (bytes/1024).toFixed(2) + ' KB';
            return bytes + ' B';
        }
        
        function copy(text, btn) {
            navigator.clipboard.writeText(text).then(() => {
                const orig = btn.textContent;
                btn.textContent = '✅';
                btn.classList.add('copied');
                setTimeout(() => {
                    btn.textContent = orig;
                    btn.classList.remove('copied');
                }, 1500);
            });
        }
        
        document.getElementById('folderPath').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') loadImages();
        });
        
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') closePreview();
        });
        
        window.addEventListener('load', () => loadImages());
    </script>
</body>
</html>'''

# ============================================================================
# MAIN - Khởi động server
# ============================================================================

def start_server(port=5000):
    """Khởi động HTTP server"""
    server_address = ('127.0.0.1', port)
    httpd = HTTPServer(server_address, ImageSorterHandler)
    
    print("\n" + "="*60)
    print("🖼️  Sắp xếp Ảnh Web UI (Standalone - Không cần Flask)")
    print("="*60)
    print(f"\n✓ Server đang chạy tại: http://localhost:{port}")
    print(f"✓ Nhấn Ctrl+C để dừng")
    print("\n")
    
    try:
        # Mở trình duyệt tự động
        time.sleep(1)
        webbrowser.open(f'http://localhost:{port}')
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n✓ Server đã dừng")
        httpd.shutdown()

if __name__ == '__main__':
    port = 5000
    
    # Kiểm tra port argument
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except:
            pass
    
    start_server(port)
