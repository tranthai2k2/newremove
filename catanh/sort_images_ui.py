#!/usr/bin/env python3
"""
Web UI để sắp xếp ảnh - Flask + HTML/CSS/JS
Chạy: python sort_images_ui.py
Truy cập: http://localhost:5000
"""

from flask import Flask, render_template_string, request, jsonify
import os
import re
from pathlib import Path
from typing import List, Tuple
import json

app = Flask(__name__)

# ============================================================================
# BACKEND - Hàm sắp xếp (giống như trước)
# ============================================================================

def natural_sort_key(filename: str) -> Tuple:
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
                'path': filepath,
                'size_mb': size_mb,
                'size_bytes': stat.st_size,
                'mtime': stat.st_mtime
            })
    except Exception as e:
        return {'error': str(e)}
    
    # Sắp xếp theo phương pháp
    if sort_method == 'name':
        images_data.sort(key=lambda x: x['name'])
    elif sort_method == 'natural':
        images_data.sort(key=lambda x: natural_sort_key(x['name']))
    elif sort_method == 'time':
        images_data.sort(key=lambda x: x['mtime'], reverse=True)
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
# HTML TEMPLATE - Giao diện web
# ============================================================================

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sắp xếp Ảnh - No Memory Load</title>
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

        .input-group input {
            flex: 1;
            min-width: 250px;
            padding: 12px 15px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 1em;
            transition: border-color 0.3s;
        }

        .input-group input:focus {
            outline: none;
            border-color: #667eea;
        }

        .input-group select {
            padding: 12px 15px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 1em;
            background: white;
            cursor: pointer;
            transition: border-color 0.3s;
        }

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
            font-size: 1em;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
            white-space: nowrap;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
        }

        .btn:active {
            transform: translateY(0);
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
        }

        .loading {
            text-align: center;
            padding: 40px;
            color: #667eea;
        }

        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 15px;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .images-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            overflow-x: auto;
            display: block;
        }

        table {
            width: 100%;
            border-collapse: collapse;
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
            font-size: 0.95em;
        }

        td {
            padding: 12px 15px;
            border-bottom: 1px solid #e0e0e0;
        }

        tbody tr:hover {
            background: #f8f9fa;
        }

        .index-col {
            color: #999;
            font-weight: 600;
            width: 50px;
        }

        .name-col {
            color: #333;
            word-break: break-all;
        }

        .size-col {
            color: #666;
            text-align: right;
            width: 120px;
        }

        .copy-btn {
            background: #f0f0f0;
            border: 1px solid #ddd;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.85em;
            transition: background 0.2s;
        }

        .copy-btn:hover {
            background: #e0e0e0;
        }

        .copy-btn.copied {
            background: #4caf50;
            color: white;
            border-color: #4caf50;
        }

        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #999;
        }

        .empty-state svg {
            width: 80px;
            height: 80px;
            margin-bottom: 20px;
            opacity: 0.3;
        }

        .footer {
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
            font-size: 0.9em;
            border-top: 1px solid #e0e0e0;
        }

        .sort-info {
            background: #e3f2fd;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            border-left: 4px solid #2196f3;
            color: #1565c0;
        }

        @media (max-width: 768px) {
            .header h1 {
                font-size: 1.8em;
            }

            .content {
                padding: 20px;
            }

            .input-group {
                flex-direction: column;
            }

            .input-group input,
            .input-group select {
                width: 100%;
            }

            table {
                font-size: 0.9em;
            }

            th, td {
                padding: 10px;
            }
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
                <input 
                    type="text" 
                    id="folderPath" 
                    placeholder="Nhập đường dẫn folder ảnh (vd: ./my_photos)"
                    value="./test_images"
                >
                <select id="sortMethod">
                    <option value="natural">📊 Sắp xếp Thông minh (Số)</option>
                    <option value="name">🔤 Sắp xếp A-Z</option>
                    <option value="time">📅 Theo Thời gian</option>
                    <option value="size">📦 Theo Kích thước</option>
                </select>
                <button class="btn" onclick="loadImages()">🔍 Tải</button>
            </div>

            <div id="error" class="error" style="display: none;"></div>
            <div id="sortInfo" class="sort-info" style="display: none;"></div>
            <div id="stats" class="stats"></div>
            <div id="loading" class="loading" style="display: none;">
                <div class="spinner"></div>
                <p>Đang tải danh sách ảnh...</p>
            </div>
            <div id="result"></div>
        </div>

        <div class="footer">
            <p>✨ Không load ảnh vào bộ nhớ | Hỗ trợ 100+ ảnh | Memory: O(n)</p>
        </div>
    </div>

    <script>
        function showError(msg) {
            const errorEl = document.getElementById('error');
            errorEl.textContent = '❌ ' + msg;
            errorEl.style.display = 'block';
            document.getElementById('stats').innerHTML = '';
            document.getElementById('result').innerHTML = '';
        }

        function showLoading() {
            document.getElementById('loading').style.display = 'block';
            document.getElementById('error').style.display = 'none';
            document.getElementById('result').innerHTML = '';
        }

        function hideLoading() {
            document.getElementById('loading').style.display = 'none';
        }

        function loadImages() {
            const folderPath = document.getElementById('folderPath').value.trim();
            const sortMethod = document.getElementById('sortMethod').value;

            if (!folderPath) {
                showError('Vui lòng nhập đường dẫn folder');
                return;
            }

            showLoading();

            fetch('/api/images', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    folder: folderPath,
                    sort_method: sortMethod
                })
            })
            .then(response => response.json())
            .then(data => {
                hideLoading();
                if (data.error) {
                    showError(data.error);
                } else {
                    displayResults(data);
                }
            })
            .catch(error => {
                hideLoading();
                showError('Lỗi kết nối: ' + error);
            });
        }

        function displayResults(data) {
            const statsEl = document.getElementById('stats');
            const resultEl = document.getElementById('result');
            const sortInfoEl = document.getElementById('sortInfo');
            document.getElementById('error').style.display = 'none';

            // Hiển thị stats
            const sortLabels = {
                'natural': '📊 Sắp xếp Thông minh (Số)',
                'name': '🔤 Sắp xếp A-Z',
                'time': '📅 Theo Thời gian',
                'size': '📦 Theo Kích thước'
            };

            statsEl.innerHTML = `
                <div class="stat-box">
                    <h3>Tổng ảnh</h3>
                    <div class="value">${data.total}</div>
                </div>
                <div class="stat-box">
                    <h3>Phương pháp</h3>
                    <div class="value" style="font-size: 1.2em;">${sortLabels[data.sort_method] || data.sort_method}</div>
                </div>
                <div class="stat-box">
                    <h3>Tổng dung lượng</h3>
                    <div class="value">${getTotalSize(data.images)}</div>
                </div>
            `;

            // Hiển thị sort info
            sortInfoEl.innerHTML = `✓ Đã sắp xếp ${data.total} ảnh từ folder: <strong>${data.folder}</strong>`;
            sortInfoEl.style.display = 'block';

            // Hiển thị bảng ảnh
            if (data.total === 0) {
                resultEl.innerHTML = `
                    <div class="empty-state">
                        <p>Không tìm thấy ảnh nào trong folder</p>
                    </div>
                `;
                return;
            }

            let html = `
                <div class="images-table">
                    <table>
                        <thead>
                            <tr>
                                <th class="index-col">#</th>
                                <th>Tên file</th>
                                <th class="size-col">Kích thước</th>
                            </tr>
                        </thead>
                        <tbody>
            `;

            data.images.forEach((img, index) => {
                const size = img.size_mb > 0 ? img.size_mb.toFixed(2) + ' MB' : 
                            (img.size_bytes > 0 ? img.size_bytes + ' B' : '0 B');
                html += `
                    <tr>
                        <td class="index-col">${index + 1}</td>
                        <td class="name-col">
                            <span>${escapeHtml(img.name)}</span>
                            <button class="copy-btn" onclick="copyToClipboard('${escapeHtml(img.name)}', this)">📋</button>
                        </td>
                        <td class="size-col">${size}</td>
                    </tr>
                `;
            });

            html += `
                        </tbody>
                    </table>
                </div>
            `;

            resultEl.innerHTML = html;
        }

        function getTotalSize(images) {
            const totalBytes = images.reduce((sum, img) => sum + img.size_bytes, 0);
            if (totalBytes > 1024 * 1024 * 1024) {
                return (totalBytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB';
            } else if (totalBytes > 1024 * 1024) {
                return (totalBytes / (1024 * 1024)).toFixed(2) + ' MB';
            } else if (totalBytes > 1024) {
                return (totalBytes / 1024).toFixed(2) + ' KB';
            }
            return totalBytes + ' B';
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        function copyToClipboard(text, button) {
            navigator.clipboard.writeText(text).then(() => {
                const originalText = button.textContent;
                button.textContent = '✅';
                button.classList.add('copied');
                setTimeout(() => {
                    button.textContent = originalText;
                    button.classList.remove('copied');
                }, 2000);
            });
        }

        // Enter key để load
        document.getElementById('folderPath').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                loadImages();
            }
        });

        // Tự động tải khi trang load
        window.addEventListener('load', () => {
            loadImages();
        });
    </script>
</body>
</html>
'''

# ============================================================================
# ROUTES
# ============================================================================

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/images', methods=['POST'])
def api_images():
    """API endpoint để lấy danh sách ảnh"""
    data = request.get_json()
    folder = data.get('folder', './test_images')
    sort_method = data.get('sort_method', 'natural')
    
    result = get_images_in_folder(folder, sort_method)
    return jsonify(result)

# ============================================================================
# RUN
# ============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("🖼️  Sắp xếp Ảnh Web UI")
    print("=" * 60)
    print("\n✓ Khởi động server...")
    print("✓ Truy cập: http://localhost:5000")
    print("✓ Nhấn Ctrl+C để dừng\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
