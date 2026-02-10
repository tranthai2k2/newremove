import React, { useState } from 'react';
import axios from 'axios';
import './FolderSelector.css';

function FolderSelector({ onFolderLoaded }) {
  const [folderPath, setFolderPath] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const handleScanFolder = async () => {
    if (!folderPath.trim()) {
      setMessage('⚠️ Vui lòng nhập đường dẫn folder');
      return;
    }

    setLoading(true);
    setMessage('🔍 Đang scan folder...');

    try {
      const res = await axios.post('http://localhost:5000/api/scan-folder', {
        folderPath: folderPath
      });

      setMessage(`✅ ${res.data.message}`);
      onFolderLoaded(res.data.count);
    } catch (error) {
      setMessage(`❌ Lỗi: ${error.response?.data?.error || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="folder-selector">
      <div className="folder-input-group">
        <input
          type="text"
          value={folderPath}
          onChange={(e) => setFolderPath(e.target.value)}
          placeholder="Nhập đường dẫn folder (vd: D:\images\anime)"
          className="folder-input"
          disabled={loading}
        />
        <button 
          onClick={handleScanFolder} 
          className="btn-scan"
          disabled={loading}
        >
          {loading ? '⏳ Scanning...' : '📂 Scan Folder'}
        </button>
      </div>

      {message && (
        <div className={`scan-message ${message.includes('✅') ? 'success' : message.includes('❌') ? 'error' : 'info'}`}>
          {message}
        </div>
      )}

      <div className="folder-hint">
        <p>💡 <strong>Hướng dẫn:</strong></p>
        <ul>
          <li>Nhập đường dẫn folder chứa ảnh (jpg, png, webp...)</li>
          <li>Mỗi ảnh cần có file .txt cùng tên chứa tags</li>
          <li>Hỗ trợ scan cả folder con bên trong</li>
        </ul>
      </div>
    </div>
  );
}

export default FolderSelector;
