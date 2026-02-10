import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './FolderManager.css';

function FolderManager({ onFoldersChanged }) {
  const [folders, setFolders] = useState([]);
  const [newFolderPath, setNewFolderPath] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    loadFolders();
  }, []);

  const loadFolders = async () => {
    try {
      const res = await axios.get('http://localhost:5000/api/folders');
      setFolders(res.data.folders);
    } catch (error) {
      console.error('Error loading folders:', error);
    }
  };

  const handleAddFolder = async () => {
    if (!newFolderPath.trim()) {
      setMessage('⚠️ Vui lòng nhập đường dẫn folder');
      return;
    }

    setLoading(true);
    setMessage('');

    try {
      await axios.post('http://localhost:5000/api/folders/add', {
        folderPath: newFolderPath
      });
      
      setMessage('✅ Đã thêm folder');
      setNewFolderPath('');
      loadFolders();
      onFoldersChanged();
    } catch (error) {
      setMessage(`❌ ${error.response?.data?.error || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleScanFolder = async (folderId) => {
    setLoading(true);
    setMessage('🔍 Đang scan...');

    try {
      const res = await axios.post(`http://localhost:5000/api/folders/${folderId}/scan`);
      setMessage(`✅ ${res.data.message}`);
      loadFolders();
      onFoldersChanged();
    } catch (error) {
      setMessage(`❌ ${error.response?.data?.error || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleScanAll = async () => {
    setLoading(true);
    setMessage('🔍 Đang scan tất cả folders...');

    try {
      const res = await axios.post('http://localhost:5000/api/folders/scan-all');
      setMessage(`✅ ${res.data.message}`);
      loadFolders();
      onFoldersChanged();
    } catch (error) {
      setMessage(`❌ ${error.response?.data?.error || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteFolder = async (folderId) => {
    if (!window.confirm('Xóa folder này khỏi database?')) return;

    try {
      await axios.delete(`http://localhost:5000/api/folders/${folderId}`);
      setMessage('✅ Đã xóa folder');
      loadFolders();
      onFoldersChanged();
    } catch (error) {
      setMessage(`❌ ${error.response?.data?.error || error.message}`);
    }
  };

  return (
    <div className="folder-manager">
      {/* Add folder form */}
      <div className="add-folder-section">
        <input
          type="text"
          value={newFolderPath}
          onChange={(e) => setNewFolderPath(e.target.value)}
          placeholder="Nhập đường dẫn folder (vd: D:\images\anime)"
          className="folder-input"
          disabled={loading}
        />
        <button 
          onClick={handleAddFolder} 
          className="btn-add"
          disabled={loading}
        >
          ➕ Thêm Folder
        </button>
      </div>

      {message && (
        <div className={`message ${message.includes('✅') ? 'success' : message.includes('❌') ? 'error' : 'info'}`}>
          {message}
        </div>
      )}

      {/* Folders list */}
      <div className="folders-section">
        <div className="folders-header">
          <h3>📂 Folders đã lưu ({folders.length})</h3>
          {folders.length > 0 && (
            <button 
              onClick={handleScanAll}
              className="btn-scan-all"
              disabled={loading}
            >
              🔄 Scan Tất Cả
            </button>
          )}
        </div>

        {folders.length === 0 ? (
          <div className="empty-folders">
            <p>Chưa có folder nào. Thêm folder để bắt đầu!</p>
          </div>
        ) : (
          <div className="folders-list">
            {folders.map((folder) => (
              <div 
                key={folder.id} 
                className={`folder-item ${!folder.exists ? 'missing' : ''}`}
              >
                <div className="folder-icon">
                  {folder.exists ? '📁' : '⚠️'}
                </div>
                
                <div className="folder-details">
                  <div className="folder-name">{folder.name}</div>
                  <div className="folder-path">{folder.path}</div>
                  <div className="folder-meta">
                    <span className="folder-count">
                      {folder.image_count || 0} ảnh
                    </span>
                    {folder.last_scan && (
                      <span className="folder-scan-time">
                        Scan: {new Date(folder.last_scan).toLocaleString('vi-VN')}
                      </span>
                    )}
                  </div>
                  {!folder.exists && (
                    <div className="folder-warning">
                      ⚠️ Folder không tồn tại trên disk
                    </div>
                  )}
                </div>

                <div className="folder-actions">
                  <button
                    onClick={() => handleScanFolder(folder.id)}
                    className="btn-action btn-scan"
                    disabled={loading || !folder.exists}
                    title="Scan folder này"
                  >
                    🔄
                  </button>
                  <button
                    onClick={() => handleDeleteFolder(folder.id)}
                    className="btn-action btn-delete"
                    disabled={loading}
                    title="Xóa khỏi database"
                  >
                    🗑️
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="folder-hint">
        <p>💡 <strong>Lưu ý:</strong></p>
        <ul>
          <li>Folders sẽ được lưu vào database, không cần nhập lại</li>
          <li>Click 🔄 để scan lại folder khi có ảnh mới</li>
          <li>Click 🗑️ để xóa folder khỏi database (không xóa files trên disk)</li>
          <li>Hỗ trợ scan cả folder con bên trong</li>
        </ul>
      </div>
    </div>
  );
}

export default FolderManager;
